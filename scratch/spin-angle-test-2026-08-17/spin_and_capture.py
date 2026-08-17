#!/usr/bin/env python3
"""Spin 90 deg in place, capture a photo at each stop, to verify the 90 deg turn.

Sequence:
  right: photo(view_right_0) -> spin 90 -> photo(view_right_1) -> ... x4
         (view_right_4 should face the same way as view_right_0)
  left:  same, back to the starting heading.

Photos are taken with ``rpicam-still`` between moves so the operator can
compare the scene across stops (the calibration target in front of the car).

⚠️ Motor-moving. An operator must stand beside the car able to cut main power
instantly. Lift the wheels or secure the chassis before running.

Run on the Pi from the repo root:

    echo yes | uv run python /tmp/spin_and_capture.py
"""

from __future__ import annotations

import subprocess
import sys
import time

from carbot import Car, NeZhaError
from carbot.config import SAFE_TEST_SPEED
from carbot.motion import MotionModel

OUT_DIR = "/tmp/spin_capture"
SPIN_90_S = MotionModel().seconds_for_angle(90)  # ~1.68 s at speed 200
PAUSE_S = 1.5  # let the car settle before capturing


def capture(name: str) -> None:
    out = f"{OUT_DIR}/{name}.jpg"
    print(f"  capturing {out} ...", flush=True)
    subprocess.run(
        ["rpicam-still", "-n", "-o", out],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


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
        return 1

    subprocess.run(["mkdir", "-p", OUT_DIR], check=True)

    with car:
        for side, method_name in (("right", "spin_right"), ("left", "spin_left")):
            move = getattr(car, method_name)
            print(f"\n=== spin {side} 90 deg x4 (photos before/after each stop) ===")
            capture(f"view_{side}_0")
            for i in range(1, 5):
                print(f"  spin {side} 90 deg ({i}/4) ...", flush=True)
                move(SAFE_TEST_SPEED)
                time.sleep(SPIN_90_S)
                car.stop()
                time.sleep(PAUSE_S)
                capture(f"view_{side}_{i}")

    print(f"\nDone. Photos in {OUT_DIR}/ on the Pi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
