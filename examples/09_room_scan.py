#!/usr/bin/env python3
"""Room spin-scan: log HC-SR04 distance vs. time while the car spins in place.

This is M1 of the room-mapping prototype — capture the polar distance profile
of the space around the car. Run with the car LIFTED (or on the floor with an
operator beside it, able to cut power):

    PYTHONPATH=src python3 examples/09_room_scan.py --scan 20 --interval 0.15

Output: /tmp/room_scan.csv with columns elapsed_s, distance_cm, spin360_s.

The scan is one frame of the incremental mapping loop in
``src/carbot/mapping.py`` (ICP + occupancy grid). Spin rate is verified at
~8.2 s per full turn at speed 150 on this build — pass ``--spin-360`` if you
change the speed or drive.

Wiring: HC-SR04 VCC=Pin 2, GND=Pin 9, TRIG=Pin 11 (GPIO 17), ECHO=Pin 13
(GPIO 27) via a 2.2k/1k divider. See docs/hardware/hc-sr04-ultrasonic-sensor.md.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time

from RPi import GPIO

TRIG_PIN = 17  # GPIO 17 (Pin 11)
ECHO_PIN = 27  # GPIO 27 (Pin 13)
SPEED_OF_SOUND = 34300.0  # cm/s


def measure_once(timeout_s: float = 0.5) -> float | None:
    """One TRIG/ECHO cycle; distance in cm or None on timeout."""
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Spin-scan the room with the HC-SR04")
    parser.add_argument("--scan", type=float, default=20.0, help="scan duration in seconds")
    parser.add_argument("--interval", type=float, default=0.15, help="seconds between readings")
    parser.add_argument("--spin-360", type=float, default=8.0,
                        help="estimated seconds per full spin (verified ~8.2 at speed 150)")
    parser.add_argument("--speed", type=int, default=150, help="spin speed 0-255")
    parser.add_argument("--out", default="/tmp/room_scan.csv", help="output CSV path")
    args = parser.parse_args()

    from carbot import Car, NeZhaError

    try:
        car = Car()
    except NeZhaError as exc:
        print(f"Connection failed: {exc}")
        print("Run `examples/01_i2c_probe.py` first to debug the link.")
        return 1

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(ECHO_PIN, GPIO.IN)

    rows: list[tuple[float, float]] = []
    print(f"Scanning {args.scan:.0f}s at {args.interval}s interval, spin speed {args.speed}...")
    car.spin_right(args.speed)
    t_start = time.time()
    try:
        while time.time() - t_start < args.scan:
            d = measure_once()
            elapsed = time.time() - t_start
            if d is not None:
                rows.append((elapsed, d))
                print(f"  t={elapsed:5.1f}s  d={d:6.1f} cm")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        car.stop()
        car.close()
        GPIO.cleanup()

    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["elapsed_s", "distance_cm", "spin360_s"])
        for elapsed, d in rows:
            w.writerow([f"{elapsed:.2f}", f"{d:.1f}", args.spin_360])
    print(f"Saved {len(rows)} readings -> {args.out}")
    if rows:
        dists = [d for _, d in rows]
        print(f"min {min(dists):.1f} cm, max {max(dists):.1f} cm, "
              f"avg {sum(dists) / len(dists):.1f} cm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
