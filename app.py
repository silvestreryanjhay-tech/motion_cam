"""
Motion Monitor - Raspberry Pi app for the Embedded Systems activity

IV. Challenge Activity : motion -> picture -> email notification (smtplib + Gmail)
Additional Task        : website control + graph + buzzer + camera captures
Both run from the same app. A step tracker on the website shows each stage happening.

Run:   python3 app.py        then open  http://localhost:5000
"""
import io
import os
import smtplib
import threading
import time
from collections import deque
from datetime import datetime
from email.message import EmailMessage

import requests
from flask import Flask, Response, jsonify, request, send_from_directory
from gpiozero import Buzzer, MotionSensor
from picamera2 import Picamera2

import config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTURE_DIR = os.path.join(BASE_DIR, "captures")
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(CAPTURE_DIR, exist_ok=True)

APP_PASSWORD = config.GMAIL_APP_PASSWORD.replace(" ", "")
EMAIL_READY = (
    config.GMAIL_SENDER != "your_email@gmail.com"
    and APP_PASSWORD not in ("", "xxxxxxxxxxxxxxxx")
)

# ---- Hardware ---------------------------------------------------------
pir = MotionSensor(config.PIR_PIN)
buzzer = Buzzer(config.BUZZER_PIN)
cam = Picamera2()
cam.configure(cam.create_preview_configuration(main={"size": config.CAMERA_SIZE}))
cam.start()
time.sleep(2)  # let the camera exposure settle

# ---- Shared state -----------------------------------------------------
started = time.time()
cam_lock = threading.Lock()
state = {"armed": True, "buzzer": True, "email": EMAIL_READY, "motion": False, "total": 0}
history = deque(maxlen=180)   # (time, 0 or 1), one sample per second
events = deque(maxlen=30)     # newest first
counter = {"n": 0}


def beep(seconds):
    buzzer.on()
    time.sleep(seconds)
    buzzer.off()


def take_picture(tag):
    name = "motion_" + datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(tag) + ".jpg"
    path = os.path.join(CAPTURE_DIR, name)
    with cam_lock:
        cam.capture_file(path)
    return name, path


def send_email(subject, body, path=None):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.GMAIL_SENDER
    msg["To"] = config.EMAIL_RECEIVER
    msg.set_content(body)
    if path:
        with open(path, "rb") as f:
            msg.add_attachment(
                f.read(), maintype="image", subtype="jpeg", filename=os.path.basename(path)
            )
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
        server.login(config.GMAIL_SENDER, APP_PASSWORD)
        server.send_message(msg)


def save_to_database(filename, email_status):
    headers = {
        "apikey": config.SUPABASE_KEY,
        "Authorization": "Bearer " + config.SUPABASE_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    try:
        r = requests.post(
            config.SUPABASE_URL + "/rest/v1/events",
            headers=headers,
            json={"image_file": filename, "email_status": email_status},
            timeout=10,
        )
        print("Supabase:", r.status_code, r.text[:120])
        return r.status_code in (200, 201, 204)
    except Exception as e:
        print("Supabase failed:", e)
        return False


def run_flow(source):
    """The full activity flow: motion -> buzzer + picture -> email -> database."""
    counter["n"] += 1
    now = datetime.now()
    ev = {
        "id": counter["n"],
        "ts": time.time(),
        "time": now.strftime("%H:%M:%S"),
        "date": now.strftime("%b %d"),
        "source": source,
        "file": None,
        "steps": {
            "motion": "ok",
            "buzzer": "waiting",
            "picture": "waiting",
            "email": "waiting",
            "database": "waiting",
        },
    }
    events.appendleft(ev)
    state["total"] += 1
    steps = ev["steps"]

    # Additional Task: buzzer sounds while the camera works
    if state["buzzer"]:
        steps["buzzer"] = "running"

        def do_buzz():
            try:
                beep(config.BUZZ_SECONDS)
                steps["buzzer"] = "ok"
            except Exception as e:
                print("Buzzer error:", e)
                steps["buzzer"] = "failed"

        threading.Thread(target=do_buzz, daemon=True).start()
    else:
        steps["buzzer"] = "skipped"

    # Camera picture
    path = None
    steps["picture"] = "running"
    try:
        ev["file"], path = take_picture(ev["id"])
        steps["picture"] = "ok"
    except Exception as e:
        print("Camera error:", e)
        steps["picture"] = "failed"

    # Challenge Activity: email notification with the picture
    email_status = "skipped"
    if state["email"] and EMAIL_READY and path:
        steps["email"] = "running"
        try:
            send_email(
                "Motion detected!",
                "Motion was detected at " + now.strftime("%Y-%m-%d %H:%M:%S"),
                path,
            )
            steps["email"] = "ok"
            email_status = "sent"
        except Exception as e:
            print("Email failed:", e)
            steps["email"] = "failed"
            email_status = "failed"
    else:
        steps["email"] = "skipped"

    # Database log
    steps["database"] = "running"
    ok = save_to_database(ev["file"] or "none", email_status)
    steps["database"] = "ok" if ok else "failed"


def monitor():
    """Reads the PIR, records readings for the graph, and starts the flow on motion."""
    last = False
    last_trigger = 0.0
    last_sample = 0.0
    pulse = False
    while True:
        now = time.time()
        m = bool(pir.motion_detected)
        pulse = pulse or m
        state["motion"] = m
        if now - last_sample >= 1:
            history.append((now, 1 if pulse else 0))
            pulse = False
            last_sample = now
        ready = now - started >= config.WARMUP_SECONDS
        if (
            m
            and not last
            and ready
            and state["armed"]
            and now - last_trigger >= config.COOLDOWN_SECONDS
        ):
            last_trigger = now
            threading.Thread(target=run_flow, args=("sensor",), daemon=True).start()
        last = m
        time.sleep(0.1)


# ---- Web server -------------------------------------------------------
app = Flask(__name__, static_folder=None)


@app.route("/")
def home():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/api/status")
def api_status():
    now = time.time()
    return jsonify(
        {
            "now": now,
            "warmup": max(0, int(config.WARMUP_SECONDS - (now - started))),
            "armed": state["armed"],
            "buzzer": state["buzzer"],
            "email": state["email"],
            "email_ready": EMAIL_READY,
            "receiver": config.EMAIL_RECEIVER if EMAIL_READY else "",
            "motion": state["motion"],
            "total": state["total"],
            "history": [[t, v] for t, v in history if now - t <= 60],
            "events": [dict(e, steps=dict(e["steps"])) for e in list(events)[:15]],
        }
    )


@app.route("/api/set", methods=["POST"])
def api_set():
    data = request.get_json(force=True, silent=True) or {}
    for key in ("armed", "buzzer", "email"):
        if key in data:
            if key == "email" and not EMAIL_READY:
                continue
            state[key] = bool(data[key])
    return jsonify({"ok": True})


@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    threading.Thread(target=run_flow, args=("simulated",), daemon=True).start()
    return jsonify({"ok": True})


@app.route("/api/capture", methods=["POST"])
def api_capture():
    counter["n"] += 1
    try:
        name, _ = take_picture("manual" + str(counter["n"]))
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})
    now = datetime.now()
    events.appendleft(
        {
            "id": counter["n"],
            "ts": time.time(),
            "time": now.strftime("%H:%M:%S"),
            "date": now.strftime("%b %d"),
            "source": "manual",
            "file": name,
            "steps": {
                "motion": "skipped",
                "buzzer": "skipped",
                "picture": "ok",
                "email": "skipped",
                "database": "skipped",
            },
        }
    )
    return jsonify({"ok": True})


@app.route("/api/test_buzzer", methods=["POST"])
def api_test_buzzer():
    threading.Thread(target=beep, args=(0.5,), daemon=True).start()
    return jsonify({"ok": True})


@app.route("/api/test_email", methods=["POST"])
def api_test_email():
    if not EMAIL_READY:
        return jsonify({"ok": False, "message": "Add your Gmail and App Password in config.py first."})
    try:
        send_email("Test email from Motion Monitor", "If you can read this, email alerts work.")
        return jsonify({"ok": True, "message": "Test email sent. Check your inbox."})
    except Exception as e:
        return jsonify({"ok": False, "message": "Failed: " + str(e)})


@app.route("/captures/<path:filename>")
def get_capture(filename):
    return send_from_directory(CAPTURE_DIR, filename)


def stream():
    while True:
        buf = io.BytesIO()
        with cam_lock:
            cam.capture_file(buf, format="jpeg")
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.getvalue() + b"\r\n"
        time.sleep(0.1)


@app.route("/video")
def video():
    return Response(stream(), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    threading.Thread(target=monitor, daemon=True).start()
    print("Motion Monitor running.")
    print("Open http://localhost:5000  (other devices: http://<pi-ip>:5000, find it with: hostname -I)")
    print("PIR warm-up:", config.WARMUP_SECONDS, "seconds. Email alerts:", "ON" if EMAIL_READY else "OFF (set up config.py)")
    try:
        app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
    finally:
        buzzer.off()
        cam.stop()
