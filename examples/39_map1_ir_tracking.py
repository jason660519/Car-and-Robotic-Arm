#!/usr/bin/env python3
"""Map1 test: drive the circular track using only IR sensor (no camera).

Pure 4-channel IR sensor line following, plus a scripted junction turn.

**Motor-moving. Operator must stand beside the car able to cut main power instantly.**

Wiring (verified 2026-08-17) and physical bar order (verified 2026-08-18 —
see `carbot.ir_line_nav` module docstring, do not assume Out1..Out4 is
left-to-right):
  Out1 (GPIO 24), Out2 (GPIO 25), Out3 (GPIO 22), Out4 (GPIO 23)
  physical left-to-right: Out4, Out3, Out1, Out2

Steering logic (see `carbot.ir_line_nav.IRLineNav`):
  - Normal line width lights the middle two physical channels → proportional
    follow steering (partial left/right imbalance)
  - All 4 channels black, sustained → a junction crossbar, not the line
    itself; the car executes a *scripted* turn (direction from policy, not
    detected — see IRNavPolicy docstring for why) then resumes follow once
    the line is reacquired or the nominal turn time elapses
  - No channels see black → line lost; automatic recovery (the sensor bar
    has a ~2.4cm dead zone between its two pairs while the route line is
    only ~2cm wide, so after a turn the car can face the gap and read
    nothing): sweep `--search-sweep-deg` left, sweep back through centre to
    the same angle right, then creep forward step by step until the line is
    seen again (or `--search-give-up-s` elapses)

Usage (wheels lifted, operator ready):
    PYTHONPATH=src python3 examples/39_map1_ir_tracking.py --duration 120

Usage (simulation, no motor):
    PYTHONPATH=src python3 examples/39_map1_ir_tracking.py --dry-run --duration 30
"""

from __future__ import annotations

import argparse
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Map1 IR sensor line tracking (no camera)"
    )
    parser.add_argument("--dry-run", action="store_true", help="detection only, no motor")
    parser.add_argument("--duration", type=float, default=120.0, help="run duration (seconds)")
    parser.add_argument(
        "--speed", type=int, default=150, help="base drive speed 0-1000 (default 150)"
    )
    parser.add_argument(
        "--turn-gain",
        type=float,
        default=2.0,
        help="steering sensitivity (default 2.0, higher = sharper turns)",
    )
    parser.add_argument(
        "--invert",
        default="0,1,2,3",
        help="IR channels to invert; default 0,1,2,3 (all) — verified 2026-08-18 "
        "after potentiometer retuning; re-check with examples/36 if pots are touched again",
    )
    parser.add_argument(
        "--junction-min-s",
        type=float,
        default=0.15,
        help="all 4 channels must read black this long before it counts as a junction",
    )
    parser.add_argument(
        "--turn-deg",
        type=float,
        default=90.0,
        help="nominal turn angle at the junction (default 90, a T-junction)",
    )
    parser.add_argument(
        "--turn-direction",
        choices=("right", "left"),
        default="right",
        help="scripted turn direction at the junction (Task-1 first T-junction: right)",
    )
    parser.add_argument(
        "--creep-before-turn-cm",
        type=float,
        default=9.5,
        help="straight creep distance after junction confirmed, before pivoting, "
        "so the axle (not just the forward-mounted sensor ~9.5cm ahead of it) "
        "centres on the junction",
    )
    parser.add_argument(
        "--forward-speed-cm-per-s",
        type=float,
        default=10.0,
        help="on-paper forward speed at --speed, used to convert "
        "--creep-before-turn-cm into a drive duration (9.5cm at 10cm/s = 0.95s)",
    )
    parser.add_argument(
        "--search-sweep-deg",
        type=float,
        default=10.0,
        help="probe angle each side of the lost heading during line-recovery search "
        "(the route line is ~2cm wide but the sensor pairs have a ~2.4cm dead zone)",
    )
    parser.add_argument(
        "--search-creep-step-s",
        type=float,
        default=0.3,
        help="forward creep duration per step during line-recovery search",
    )
    parser.add_argument(
        "--search-creep-speed-ratio",
        type=float,
        default=0.5,
        help="creep speed as a fraction of --speed during line-recovery search",
    )
    parser.add_argument(
        "--search-creep-steps",
        type=int,
        default=4,
        help="creep steps before the sweep+creep search cycle repeats",
    )
    parser.add_argument(
        "--search-give-up-s",
        type=float,
        default=30.0,
        help="stop the car after this many seconds of searching (0 = never)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Map1 IR Sensor Line Tracking")
    print("=" * 70)
    print(f"Speed: {args.speed} | Turn gain: {args.turn_gain} | Duration: {args.duration}s")
    print()

    if not args.dry_run:
        answer = input("Operator beside car, track clear, power ready to cut? (yes/no) ").strip()
        if answer.lower() != "yes":
            print("Re-run when ready.")
            return 1

    from RPi import GPIO

    from carbot.ir_line_nav import IRLineNav, IRNavPolicy, IRNavState, detect_ir_line
    from carbot.ir_tracing import IRTracingSensor

    # Setup IR sensor
    GPIO.setmode(GPIO.BCM)
    pins = (24, 25, 22, 23)
    for pin in pins:
        GPIO.setup(pin, GPIO.IN)

    invert_set = set()
    if args.invert.strip():
        invert_set = {int(x) for x in args.invert.split(",") if x.strip()}

    sensor = IRTracingSensor(pins, GPIO, invert=invert_set)

    nav_policy = IRNavPolicy(
        speed=args.speed,
        turn_gain=args.turn_gain,
        junction_min_s=args.junction_min_s,
        turn_direction=1 if args.turn_direction == "right" else -1,
        turn_deg=args.turn_deg,
        creep_before_turn_cm=args.creep_before_turn_cm,
        forward_speed_cm_per_s=args.forward_speed_cm_per_s,
        search_sweep_deg=args.search_sweep_deg,
        search_creep_step_s=args.search_creep_step_s,
        search_creep_speed_ratio=args.search_creep_speed_ratio,
        search_creep_steps_per_cycle=args.search_creep_steps,
        search_give_up_s=args.search_give_up_s,
    )
    nav = IRLineNav(nav_policy)

    from carbot import Car, NeZhaError

    car = None
    if not args.dry_run:
        try:
            car = Car()
        except NeZhaError as exc:
            print(f"Connection failed: {exc}")
            GPIO.cleanup()
            return 1

    start = time.monotonic()
    last = start
    frame_index = 0
    line_lost_count = 0
    line_found_count = 0
    search_entries = 0
    last_state = None

    try:
        while True:
            now = time.monotonic()
            dt = now - last
            last = now
            frame_index += 1
            elapsed = now - start

            # Read IR sensor
            reading = detect_ir_line(sensor, speed=args.speed)
            command = nav.step(reading, dt)

            # Track statistics
            if command.state is IRNavState.SEARCH and last_state is not IRNavState.SEARCH:
                search_entries += 1
            last_state = command.state
            if reading.visible:
                line_found_count += 1
                line_lost_count = 0
            else:
                line_lost_count += 1

            # Drive
            if car:
                car.drive(command.left, command.right)

            # Log
            ch_str = "".join(str(c) for c in reading.channels)
            status = "OK" if reading.visible else "LOST"
            print(
                f"[{elapsed:6.1f}s] #{frame_index:4d} "
                f"{status:5s} {ch_str} err={reading.error_fraction:+.2f} -> "
                f"{command.state.value:14s} L{command.left:4d} R{command.right:4d} | {command.reason}"
            )

            if args.duration and elapsed >= args.duration:
                print(f"\nDuration limit reached ({args.duration}s)")
                break

    except KeyboardInterrupt:
        print("\nStopped by operator")
    finally:
        if car:
            car.stop()
            car.close()
        GPIO.cleanup()
        elapsed = time.monotonic() - start
        print()
        print("=" * 70)
        print(f"Test summary: {elapsed:.1f}s, {frame_index} cycles")
        print(f"  Line visible: {line_found_count} cycles")
        print(f"  Line lost: {line_lost_count} cycles")
        print(f"  Line-recovery searches: {search_entries}")
        print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
