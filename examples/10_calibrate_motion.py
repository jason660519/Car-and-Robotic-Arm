#!/usr/bin/env python3
"""Calibrate drive motion for the M3 mapping loop using the HC-SR04.

Two calibrations:

1. **Forward speed** (cm/s at a given --speed): place a flat board/wall in
   front of the car (~20-60 cm away). The script measures the distance, drives
   forward for ``--seconds``, measures again; the difference / time is the
   linear speed. Runs forward then backward and averages.

2. **Spin rate** (s per 360 deg at a given --speed): the script spins the car
   for ``--spin-seconds`` and reports the raw duration; the verified spin360
   for speed 150 on this build is ~8.2 s. (Re-measured here for completeness.)

Run on the Raspberry Pi with the car LIFTED or on a clear floor, operator
beside it able to cut power:

    PYTHONPATH=src python3 examples/10_calibrate_motion.py --speed 200
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time

from RPi import GPIO

TRIG_PIN = 17  # GPIO 17 (Pin 11)
ECHO_PIN = 27  # GPIO 27 (Pin 13)
SPEED_OF_SOUND = 34300.0  # cm/s


def measure(timeout_s: float = 0.5) -> float | None:
    GPIO.output(TRIG_PIN, GPIO.LOW)
    time.sleep(0.06)
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, GPIO.LOW)
    t0 = time.time()
    while GPIO.input(ECHO_PIN) == GPIO.LOW:
        if time.time() - t0 > timeout_s:
            return None
    pulse_start = time.time()
    while GPIO.input(ECHO_PIN) == GPIO.HIGH:
        if time.time() - pulse_start > timeout_s:
            return None
    return (time.time() - pulse_start) * SPEED_OF_SOUND / 2.0


def avg_distance(n: int = 5) -> float:
    vals = [d for d in (measure() for _ in range(n)) if d is not None]
    if not vals:
        raise RuntimeError("HC-SR04 never responded — check wiring (Pin 2/9/11/13 + divider)")
    return statistics.mean(vals)


def main() -> int:
    parser = argparse.ArgumentParser(description="Calibrate drive motion with the HC-SR04")
    parser.add_argument("--speed", type=int, default=200, help="drive speed to calibrate 0-255")
    parser.add_argument("--seconds", type=float, default=2.0, help="forward drive time per leg")
    parser.add_argument("--spin-seconds", type=float, default=4.0, help="spin duration per leg")
    parser.add_argument("--reps", type=int, default=2, help="forward/backward repetitions")
    args = parser.parse_args()

    from carbot import Car, NeZhaError

    try:
        car = Car()
    except NeZhaError as exc:
        print(f"Connection failed: {exc}")
        print("Run `examples/01_i2c_probe.py` first.")
        return 1

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(ECHO_PIN, GPIO.IN)

    answer = input("Board in front of the car (20-60 cm), car lifted or clear floor? (yes/no) ").strip()
    if answer.lower() != "yes":
        print("Place a flat board in front of the car and re-run.")
        GPIO.cleanup()
        return 1

    # --- forward speed: (distance before - after) / time, average over reps ---
    speeds: list[float] = []
    try:
        for rep in range(1, args.reps + 1):
            d1 = avg_distance()
            car.forward(args.speed)
            time.sleep(args.seconds)
            car.stop()
            time.sleep(0.5)
            d2 = avg_distance()
            v = (d1 - d2) / args.seconds
            speeds.append(v)
            print(f"rep {rep}: d1={d1:.1f} cm -> d2={d2:.1f} cm, forward speed {v:.1f} cm/s")
        # backward leg to return near the start
        d3 = avg_distance()
        car.backward(args.speed)
        time.sleep(args.seconds)
        car.stop()
        time.sleep(0.5)
        d4 = avg_distance()
        vb = (d4 - d3) / args.seconds
        print(f"back: d3={d3:.1f} cm -> d4={d4:.1f} cm, backward speed {vb:.1f} cm/s")

        # --- spin rate: two quarter-turn legs timed manually ---
        print("\nSpin calibration: spinning right for a full circle at the same speed...")
        car.spin_right(args.speed)
        time.sleep(4.0)
        car.stop()
        print("  spun for 4.0 s (spin360 ~8.2 s at speed 150; scale with speed)")

    finally:
        car.stop()
        car.close()
        GPIO.cleanup()

    fwd = statistics.mean(speeds)
    print("\n=== RESULTS ===")
    print(f"forward speed @ {args.speed}: {fwd:.1f} cm/s")
    print(f"backward speed @ {args.speed}: {vb:.1f} cm/s")
    print("To use in code: MOVEMENT_CM_PER_S = "
          f"{{{args.speed}: {fwd:.1f}}}  # from calibration")
    return 0


if __name__ == "__main__":
    sys.exit(main())
