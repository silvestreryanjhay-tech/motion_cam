"""All settings for the Motion Monitor app. Edit this file only."""

# ---- Hardware pins (GPIO / BCM numbers, not physical pin numbers) ----
PIR_PIN = 17        # PIR OUT -> physical Pin 11
BUZZER_PIN = 27     # GPIO27 (physical Pin 13) -> 1k resistor -> transistor base

# ---- Behaviour ----
WARMUP_SECONDS = 30      # PIR needs time to settle after power-up
COOLDOWN_SECONDS = 10    # minimum time between two detections
BUZZ_SECONDS = 3         # how long the buzzer sounds
CAMERA_SIZE = (1024, 768)

# ---- Gmail (Challenge Activity: email notification) ----
# Use a Google App Password (16 characters), NOT your normal password.
GMAIL_SENDER = "2023-204057@rtu.edu.ph"
GMAIL_APP_PASSWORD = "xxxxxxxxxxxxxxxx"
EMAIL_RECEIVER = "2023-204057@rtu.edu.ph"

# ---- Supabase (database) ----
SUPABASE_URL = "https://lzkzmdsgnnyxnsfoxcee.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx6a3ptZHNnbm55eG5zZm94Y2VlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1MDYwOTEsImV4cCI6MjEwNDA4MjA5MX0.pXGk24qRS9KK2NHuBXa6NPA0hVaYsTkxkoYLU2kQV_s"
