#!/usr/bin/env python3
"""M3 autonomous exploration loop: spin-scan -> ICP -> grid -> move -> repeat.

This is the incremental-mapping loop validated by the M1/M2 prototype:

1. Spin one full turn and record a polar scan (HC-SR04).
2. Register the scan against the accumulated map with *no-move* ICP — the
   verified regime: for steps <15 cm the ICP converges to ~0.06 cm error even
   with an identity initial guess, so odometry only needs to be roughly right.
3. Fuse the scan into the 10 cm :class:`OccupancyGrid`.
4. Detect door/wall gaps and decide the next move (drive toward the largest
   unexplored gap, else rotate a bit), then take a small step.
5. Stop when the step budget runs out or Ctrl-C.

Run on the Raspberry Pi with the operator beside the car:

    PYTHONPATH=src python3 examples/11_explore_mapping.py --steps 20

Known limits (documented in docs/progress/2026-08-14-...): no wheel encoders,
so odometry is open-loop; incremental ICP drift accumulates, and pure
multi-angle ICP remains multi-modal for non-adjacent scans of rectangular
rooms. This loop intentionally stays in the local-convergence regime.
"""

from __future__ import annotations

import argparse
import math
import statistics
import sys
import time

import numpy as np
from RPi import GPIO

from carbot.mapping import OccupancyGrid, detect_gaps, icp, polar_to_points

TRIG_PIN = 17  # GPIO 17 (Pin 11)
ECHO_PIN = 27  # GPIO 27 (Pin 13)
SPEED_OF_SOUND = 34300.0  # cm/s
SPIN_360_S = 8.2  # verified on this build at speed 150
MAX_RANGE = 400.0

STEP_S = 2.5  # seconds of forward per step (~15-25 cm at the measured ~5-10 cm/s)
DRIVE_SPEED = 200
FWD_CM_PER_S = 8.0  # rough calibration from examples/10_calibrate_motion.py (5-10 cm/s)


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


def spin_scan(car, spin_s: float = SPIN_360_S, interval: float = 0.15) -> list[tuple[float, float]]:
    """Spin one full turn, logging (angle, distance) rows."""
    rows: list[tuple[float, float]] = []
    car.spin_right(DRIVE_SPEED)
    t0 = time.time()
    try:
        while time.time() - t0 < spin_s:
            d = measure()
            if d is not None:
                elapsed = time.time() - t0
                angle = (elapsed % SPIN_360_S) / SPIN_360_S * 2 * math.pi
                rows.append((angle, min(d, MAX_RANGE)))
            time.sleep(interval)
    finally:
        car.stop()
    return rows


def gap_anchor_heading(scan_gaps, ref_gaps):
    """Estimate the sensor heading from gap angles vs world-frame reference gaps.

    A door/gap is a fixed world feature; the difference between its angle in
    the sensor frame and its reference (world) angle is the sensor heading.
    Returns degrees (0-360) or None when there are no gaps to vote with.
    """
    if not scan_gaps or not ref_gaps:
        return None
    votes = []
    for sg in scan_gaps:
        best = min(((rg - sg["center_deg"]) % 360.0 for rg in ref_gaps), default=None)
        if best is not None:
            votes.append(best)
    return (statistics.mean(votes) % 360.0) if votes else None


def main() -> int:
    parser = argparse.ArgumentParser(description="M3 autonomous room-mapping loop")
    parser.add_argument("--steps", type=int, default=20, help="max exploration steps")
    parser.add_argument("--spin360", type=float, default=SPIN_360_S, help="seconds per full spin")
    parser.add_argument("--step-s", type=float, default=STEP_S, help="forward seconds per step")
    args = parser.parse_args()

    from carbot import Car, NeZhaError

    try:
        car = Car()
    except NeZhaError as exc:
        print(f"Connection failed: {exc}")
        return 1

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(ECHO_PIN, GPIO.IN)

    grid = OccupancyGrid(cell_cm=10.0, side_cm=1000.0)
    map_pts: np.ndarray | None = None
    ref_gaps: list[float] | None = None
    prev_pos: np.ndarray | None = None
    print("M3 exploration loop — spin scan, ICP (gap-anchored), grid update, small step")
    print("=" * 60)

    try:
        for step in range(1, args.steps + 1):
            rows = spin_scan(car, args.spin360)
            scan = polar_to_points(np.asarray(rows, dtype=np.float64))
            if len(scan) < 10:
                print(f"[{step}] scan too sparse ({len(scan)} pts) — stopping")
                break

            gaps = detect_gaps(np.asarray(rows, dtype=np.float64))
            if ref_gaps is None and gaps:
                ref_gaps = [g["center_deg"] for g in gaps]
                print(f"[{step}] reference gaps (world): "
                      f"{[round(g) for g in ref_gaps]}")

            if map_pts is None:
                r, t = np.eye(2), np.zeros(2)
                inl = len(scan)
                map_pts = scan.copy()
            else:
                # initial guess from open-loop odometry: the car drove forward
                # along its heading (scan angle 0 -> +y in sensor frame) since
                # the previous frame; ICP refines it.
                odom_cm = FWD_CM_PER_S * args.step_s
                r, t = icp(scan, map_pts, trans0=np.array([0.0, odom_cm]))
                # gap anchor: correct heading drift using fixed world gaps
                heading_icp = math.degrees(math.atan2(r[1, 0], r[0, 0])) % 360.0
                heading_gap = gap_anchor_heading(gaps, ref_gaps)
                if heading_gap is not None:
                    delta = (heading_gap - heading_icp + 180.0) % 360.0 - 180.0
                    if abs(delta) > 15.0:
                        print(f"    heading drift: ICP {heading_icp:.0f} vs gap anchor "
                              f"{heading_gap:.0f} (delta {delta:.0f}) — correcting")
                        r = np.array([[math.cos(math.radians(heading_gap)),
                                       -math.sin(math.radians(heading_gap))],
                                      [math.sin(math.radians(heading_gap)),
                                       math.cos(math.radians(heading_gap))]])
                aligned = scan @ r.T + t
                d = np.sqrt(((aligned[:, None, :] - map_pts[None, :, :]) ** 2).sum(-1).min(1))
                inl = int((d < 25.0).sum())
                map_pts = np.vstack([map_pts, aligned])

            grid.update(r, t, scan)

            # crash detection: position jump vs odometry expectation, low inliers
            crash = False
            if prev_pos is not None:
                jump = float(np.linalg.norm(t - prev_pos))
                expect = FWD_CM_PER_S * args.step_s
                if jump > max(30.0, 3 * expect):
                    print(f"    CRASH DETECTED: pos jumped {jump:.0f} cm "
                          f"(expected ~{expect:.0f}) — stopping")
                    crash = True
            if inl / max(len(scan), 1) < 0.55:
                print(f"    LOW INLIERS ({inl}/{len(scan)}) — stopping before wrong lock-in")
                crash = True
            prev_pos = t.copy()

            print(f"[{step}] ICP inliers {inl}/{len(scan)}, pos ({t[0]:5.0f}, {t[1]:5.0f}) cm, "
                  f"gaps: {[(round(g['center_deg']), round(g['dist_cm'])) for g in gaps]}")

            if crash or step >= args.steps:
                break

            car.forward(DRIVE_SPEED)
            time.sleep(args.step_s)
            car.stop()
            time.sleep(0.3)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        car.stop()
        car.close()
        GPIO.cleanup()

    print("-" * 60)
    print(f"Done. Occupied bounding box: {grid.occupied_bounds_cm()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
