"""
Test the online parts. Run from the project folder:

  python3 tools/cloud_test.py supabase   -> inserts a test row and reads the latest rows
  python3 tools/cloud_test.py email      -> sends a test email with your Gmail App Password
"""
import os
import smtplib
import sys
from email.message import EmailMessage

import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import config

what = sys.argv[1] if len(sys.argv) > 1 else ""

if what == "supabase":
    headers = {
        "apikey": config.SUPABASE_KEY,
        "Authorization": "Bearer " + config.SUPABASE_KEY,
        "Content-Type": "application/json",
    }
    r = requests.post(
        config.SUPABASE_URL + "/rest/v1/events",
        headers=dict(headers, Prefer="return=minimal"),
        json={"image_file": "test.jpg", "email_status": "test"},
        timeout=10,
    )
    print("Insert:", r.status_code, r.text)
    r = requests.get(
        config.SUPABASE_URL + "/rest/v1/events?select=*&order=id.desc&limit=5",
        headers=headers,
        timeout=10,
    )
    print("Read:", r.status_code)
    if r.ok:
        for row in r.json():
            print(row)
    print("201 on insert = working. 401/403 = run supabase_setup.sql. 404 = table name is not 'events'.")

elif what == "email":
    msg = EmailMessage()
    msg["Subject"] = "Test email from Motion Monitor"
    msg["From"] = config.GMAIL_SENDER
    msg["To"] = config.EMAIL_RECEIVER
    msg.set_content("If you can read this, email alerts work.")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as s:
            s.login(config.GMAIL_SENDER, config.GMAIL_APP_PASSWORD.replace(" ", ""))
            s.send_message(msg)
        print("Email sent. Check the inbox of", config.EMAIL_RECEIVER)
    except Exception as e:
        print("Email failed:", e)
        print("Check the App Password. School accounts may block App Passwords; use a personal Gmail.")

else:
    print(__doc__)
