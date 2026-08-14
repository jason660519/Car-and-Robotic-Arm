#!/usr/bin/env python3
"""Autonomous patrol + capture for Structure-from-Motion.

The car drives **itself** slowly around the room, avoids obstacles with the
HC-SR04, and captures a still at every stop. No operator pushing — but an
operator must stand beside the car able to cut main power instantly, because
this script moves motors.

Run on the Pi with the operator beside the car, path clear and the battery
charged:

    PYTHONPATH=src python3 examples/17_patrol_capture.py --frames 40

Loop per frame:

1. Sample the sonar several times and keep the **nearest** reading.
2. If the reading is ``None`` (HC-SR04 near-range blind zone, <~20 cm, or a
   fault) **or** closer than --obstacle-cm, treat it as an obstacle: spin away
   (alternating left/right) and capture a still of this position, then retry.
   A missing reading is treated as unsafe, never as "clear".
3. Otherwise drive forward a short --step-s, stop, and capture a still.

The car has no encoders, so position is open-loop; SfM does not need odometry,
only overlapping viewpoints.

Output: one frame-NNN.jpg per capture under --out-dir (default /tmp/room-sfm).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from RPi import GPIO

from carbot.sonar import Sonar

TRIG_PIN = 17  # GPIO 17 (Pin 11)
ECHO_PIN = 27  # GPIO 27 (Pin 13)


def read_distance(sonar: Sonar, trials: int = 3) -> float | None:
    """Nearest of ``trials`` readings, or None when none return a value.

    A None result means "cannot confirm clear" (blind zone or fault); callers
    must treat it as an obstacle, never as free space.
    """
    vals = [d for d in (sonar.measure() for _ in range(trials)) if d is not None]
    return min(vals) if vals else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Autonomous patrol + capture for SfM")
    parser.add_argument("--frames", type=int, default=40, help="number of stills to capture")
    parser.add_argument("--step-s", type=float, default=0.8, help="seconds of forward per step")
    parser.add_argument("--speed", type=int, default=150, help="drive speed 0-255 (low)")
    parser.add_argument("--obstacle-cm", type=float, default=45.0,
                        help="turn away when the sonar reads closer than this")
    parser.add_argument("--turn-s", type=float, default=2.0, help="seconds to spin when avoiding")
    parser.add_argument("--size", default="2028x1520", help="capture size WxH")
    parser.add_argument("--out-dir", type=Path, default=Path("/tmp/room-sfm"))
    args = parser.parse_args()

    width, height = (int(v) for v in args.size.split("x"))

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(ECHO_PIN, GPIO.IN)
    sonar = Sonar(TRIG_PIN, ECHO_PIN, GPIO)

    answer = input(
        "Operator beside the car, path clear, power ready to cut? (yes/no) "
    ).strip()
    if answer.lower() != "yes":
        print("Re-run when an operator is ready beside the car.")
        GPIO.cleanup()
        return 1

    from carbot import Car, NeZhaError

    try:
        car = Car()
    except NeZhaError as exc:
        print(f"Connection failed: {exc}")
        print("Run `examples/01_i2c_probe.py` first to debug the link.")
        GPIO.cleanup()
        return 1

    try:
        from picamera2 import Picamera2
    except ImportError as exc:
        print(f"Picamera2 required: {exc}")
        car.close()
        GPIO.cleanup()
        return 1

    camera = Picamera2()
    try:
        config = camera.create_still_configuration(main={"size": (width, height)})
        camera.configure(config)
        camera.start()
        time.sleep(1.5)
    except Exception:
        camera.close()
        car.close()
        GPIO.cleanup()
        raise

    args.out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Patrolling: {args.frames} frames, step {args.step_s}s at speed {args.speed}, "
          f"obstacle/unreadable turns below {args.obstacle_cm:.0f} cm. Ctrl-C to stop.")
    turn_left = False
    n = 0
    try:
        while n < args.frames:
            d = read_distance(sonar)
            if d is None or d < args.obstacle_cm:
                # Near-range blind zone (None) or a real obstacle: turn away.
                why = f"{d:.0f} cm" if d is not None else "no reading (blind zone)"
                print(f"[{n + 1}] obstacle: {why} -> turn "
                      f"{'left' if turn_left else 'right'}")
                if turn_left:
                    car.spin_left(args.speed)
                else:
                    car.spin_right(args.speed)
                time.sleep(args.turn_s)
                car.stop()
                turn_left = not turn_left
                time.sleep(0.4)
                # capture this position too, then re-check before moving
                path = args.out_dir / f"frame-{n:03d}.jpg"
                camera.capture_file(str(path))
                print(f"[{n + 1}] {path.name}")
                n += 1
                continue

            # Clear: advance one short step, stop, then shoot.
            car.forward(args.speed)
            time.sleep(args.step_s)
            car.stop()
            time.sleep(0.4)  # settle so the still is sharp

            path = args.out_dir / f"frame-{n:03d}.jpg"
            camera.capture_file(str(path))
            print(f"[{n + 1}] {path.name}")
            n += 1
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        car.stop()
        camera.stop()
        camera.close()
        car.close()
        GPIO.cleanup()

    print(f"Captured {n} frames -> {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
