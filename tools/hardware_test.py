"""
Quick hardware tests. Stop the main app first (only one program can use the pins/camera).

  python3 tools/hardware_test.py pir      -> prints "no motion" / "MOTION DETECTED"
  python3 tools/hardware_test.py buzzer   -> beeps 3 times
  python3 tools/hardware_test.py camera   -> saves test.jpg
"""
import os
import sys
from time import sleep

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import config

what = sys.argv[1] if len(sys.argv) > 1 else ""

if what == "pir":
    from gpiozero import DigitalInputDevice

    pir = DigitalInputDevice(config.PIR_PIN, pull_up=False)
    print("Reading GPIO%d. Wave your hand sideways across the PIR. Ctrl+C to stop." % config.PIR_PIN)
    while True:
        print("MOTION DETECTED" if pir.value else "no motion")
        sleep(0.3)

elif what == "buzzer":
    from gpiozero import Buzzer

    b = Buzzer(config.BUZZER_PIN)
    for _ in range(3):
        b.on()
        sleep(0.5)
        b.off()
        sleep(0.5)
    print("Done. Did you hear 3 beeps?")

elif what == "camera":
    from picamera2 import Picamera2

    cam = Picamera2()
    cam.start()
    sleep(2)
    cam.capture_file("test.jpg")
    cam.stop()
    print("Saved test.jpg. Open it to check the picture.")

else:
    print(__doc__)
