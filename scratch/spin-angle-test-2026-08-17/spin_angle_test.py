#!/usr/bin/env python3
"""Open-loop spin-angle test: right 90/180/270/360, left 90/180/270/360.

Uses the calibrated spin rate in ``carbot.motion.MotionModel`` (53.5 deg/s at
speed 200, measured 2026-08-16) to compute each spin duration. The car has no
encoders, so this is open-loop — the operator must eyeball each angle and
report any large deviation afterwards.

⚠️ Motor-moving. An operator must stand beside the car able to cut main power
instantly. Lift the wheels or secure the chassis before running.

Run on the Pi from the repo root:

    echo yes | uv run python scratch/spin-angle-test-2026-08-17/spin_angle_test.py
"""

from __future__ import annotations

import sys
import time

from carbot import Car, NeZhaError
from carbot.config import SAFE_TEST_SPEED
from carbot.motion import MotionModel

PAUSE_S = 2.0  # pause between moves so the operator can check the heading

ANGLES = (90, 180, 270, 360)

MOVES: list[tuple[str, str]] = []
for direction, method in (("right", "spin_right"), ("left", "spin_left")):
    for angle in ANGLES:
        MOVES.append((method, f"spin {direction} {angle} deg"))


def main() -> int:
    if (
        input("Operator beside the car, wheels lifted/secured? (yes/no) ").strip().lower()
        != "yes"
    ):
        print("Lift/secure the car and have an operator ready before running this test.")
        return 1

    try:
        car = Car()
    except NeZhaError as exc:
        print(f"Connection failed: {exc}")
        print("Run `examples/01_i2c_probe.py` first to debug the link.")
        return 1

    model = MotionModel()  # speed 200, spin_degps 53.5

    with car:
        for method_name, label in MOVES:
            move = getattr(car, method_name)
            angle = label.rsplit(" ", 2)[1]
            seconds = model.seconds_for_angle(float(angle))
            print(f"  {label}  ->  {seconds:.2f} s at speed {SAFE_TEST_SPEED}", flush=True)
            move(SAFE_TEST_SPEED)
            time.sleep(seconds)
            car.stop()
            time.sleep(PAUSE_S)

    print("\nDone. Report any angle that visibly overshot or undershot.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
