# Motion Monitor (Raspberry Pi)

One app that covers both activities:

- **IV. Challenge Activity**: motion -> picture -> email notification (smtplib + Gmail)
- **Additional Task**: website control and monitoring, sensor graph, camera captures, and a buzzer

The website has a tab for each activity and a step tracker that lights up
(waiting -> working -> done) as each stage happens.

## 1. Wiring (Raspberry Pi powered OFF)

| Part | Connects to |
|---|---|
| PIR VCC | Pin 2 (5V) |
| PIR OUT | Pin 11 (GPIO17) |
| PIR GND | Pin 6 (GND) |
| Pin 13 (GPIO27) | 1 kOhm resistor, then transistor base |
| Transistor emitter | Pin 9 (GND) |
| Transistor collector | Buzzer (-) |
| Buzzer (+) | Pin 4 (5V) |
| Camera | CAMERA port (ribbon cable) |

## 2. Install (once)

    sudo apt install python3-flask python3-requests python3-picamera2 python3-gpiozero

## 3. Configure

- Open `config.py`. Supabase is already filled in.
- For email: set `GMAIL_SENDER`, `GMAIL_APP_PASSWORD` (Google App Password, 16 characters) and `EMAIL_RECEIVER`.
- In Supabase, open SQL Editor and run `supabase_setup.sql` once (creates the `events` table).

## 4. Test the parts first

    python3 tools/hardware_test.py pir
    python3 tools/hardware_test.py buzzer
    python3 tools/hardware_test.py camera
    python3 tools/cloud_test.py supabase
    python3 tools/cloud_test.py email

## 5. Run the app

    python3 app.py        (or ./run.sh)

Open http://localhost:5000 in the Pi browser, or http://PI-IP:5000 from another device
on the same network (find the IP with `hostname -I`).

## 6. Demo

1. Wait for the badge to say **Watching** (about 30 seconds of PIR warm-up).
2. Wave your hand sideways across the PIR. If the sensor is not working yet, press **Simulate motion**; it runs the same flow.
3. Challenge Activity tab: watch Motion -> Picture -> Email -> Saved to Supabase turn green, and check your inbox.
4. Additional Task tab: see the live camera, the buzzer step, the graph, and the new capture.
5. Check Supabase: Table Editor -> events shows a new row.

## Troubleshooting

- **Camera busy / error**: stop any other script using the camera or PIR (Thonny Stop button).
- **PIR never triggers**: run the PIR test; check VCC on Pin 2, GND on Pin 6, OUT on Pin 11, jumper on H.
- **Buzzer silent or always on**: check the transistor pin order and the buzzer polarity.
- **Email failed**: wrong App Password, or the school account blocks App Passwords. Use a personal Gmail.
- **Supabase 401/403**: run `supabase_setup.sql`. **404**: the table must be named `events`.
- **Blurry pictures**: the OV5647 camera is fixed focus; keep subjects about 1 to 2 meters away, with good light.

## Security

Never share your App Password. Do not post `config.py` online with your real Gmail details in it.
