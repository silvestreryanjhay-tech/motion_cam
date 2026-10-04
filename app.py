import os

import requests
from flask import Flask, jsonify, send_from_directory

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

app = Flask(__name__, static_folder=None)


@app.route("/")
def home():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/api/events")
def events():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({"error": "SUPABASE_URL and SUPABASE_KEY are not set on the server."}), 500
    try:
        r = requests.get(
            SUPABASE_URL + "/rest/v1/events?select=*&order=id.desc&limit=500",
            headers={"apikey": SUPABASE_KEY, "Authorization": "Bearer " + SUPABASE_KEY},
            timeout=10,
        )
        if not r.ok:
            return jsonify({"error": "Supabase returned " + str(r.status_code), "detail": r.text[:200]}), 502
        return jsonify({"events": r.json()})
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))