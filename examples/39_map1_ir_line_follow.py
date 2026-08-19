#!/usr/bin/env python3
"""Map1 test: drive the circular track using only IR sensor (no camera).

Pure 4-channel IR sensor line following, plus a scripted junction turn.

**Motor-moving. Operator must stand beside the car able to cut main power instantly.**

Wiring and physical layout — see `carbot.ir_geometry`, and the mapping table in
docs/hardware/ir-tracing-sensor.md. Do NOT assume Out1..Out4 is left-to-right:

  position       P1      P2      P3      P4
  channel      Out2    Out1    Out3    Out4
  BCM GPIO       25      24      22      23     (measured 2026-08-19)
  offset      -3.2cm  -0.4cm  +0.4cm  +3.2cm

Readings are logged in **physical P1..P4 order**, not channel order, so the bit
string reads left-to-right as the bar is laid out.

Steering (see `carbot.ir_geometry.STATE_TABLE`, total over all 16 readings):
  - `0110` centred → straight. `0010`/`0100` → slight correction; these are the
    only warning before the blind band, and the window is just 0.8cm wide
  - `0000` is NOT automatically "line lost". The outer gap is 2.8cm and the line
    2.0cm, so there is a 0.8cm band where the car is on the line and sees
    nothing. The previous reading decides: after `0010`/`0100` it is the blind
    band and steering continues; after `0001`/`1000` the line really has left
    the bar and the search starts
  - A sustained junction reading only means "a junction is under the bar". Which
    junction it is, and whether to turn or cross, comes from the route sequence
    in `carbot.ir_route`, gated by distance since the previous one. The readings
    themselves cannot tell the roundabout exit from the T junction — both are a
    right branch — and the 2026-08-19 run showed `1111` appears at the T and on
    the roundabout too, not only at the entry
  - Non-contiguous readings (`0101`, `1001`, `1010`, `1011`, `1101`) cannot come
    from a single 2cm line, so they never steer — the previous command is held
    and the frame is counted as noise

Usage (wheels lifted, operator ready):
    PYTHONPATH=src python3 examples/39_map1_ir_line_follow.py --duration 120

Usage (simulation, no motor):
    PYTHONPATH=src python3 examples/39_map1_ir_line_follow.py --dry-run --duration 30
"""

from __future__ import annotations

import argparse
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description="Map1 IR sensor line tracking (no camera)")
    parser.add_argument("--dry-run", action="store_true", help="detection only, no motor")
    parser.add_argument(
        "--hz",
        type=float,
        default=100.0,
        help="control loop rate (default 100). Free-running produced 6.2M frames and a "
        "608MB log in 148s; at 10cm/s, 100Hz still samples the 0.8cm blind band 8 times",
    )
    parser.add_argument(
        "--log-every",
        action="store_true",
        help="log every cycle instead of only on state change (very verbose)",
    )
    parser.add_argument(
        "--heartbeat-s",
        type=float,
        default=2.0,
        help="print the current state at least this often even when unchanged",
    )
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
        "--start-on-loop",
        action="store_true",
        help="car starts on the east-west line facing east, not in the start box, so the "
        "one-time stem T junction is dropped and the first junction is the roundabout entry",
    )
    parser.add_argument(
        "--laps",
        type=int,
        default=0,
        help="stop at the T junction closing lap N (0 = lap forever). The stop is an entry "
        "in the route sequence, so it only fires after every junction before it was reached",
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

    from carbot.ir_route import TASK1_LOOP_ONLY, TASK1_ROUTE, task1_route_for_laps

    if args.laps > 0:
        route = task1_route_for_laps(args.laps, start_on_loop=args.start_on_loop)
    else:
        route = TASK1_LOOP_ONLY if args.start_on_loop else TASK1_ROUTE

    nav_policy = IRNavPolicy(
        route=route,
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
    drive_error: NeZhaError | None = None

    period = 1.0 / args.hz if args.hz > 0 else 0.0
    last_logged: tuple | None = None
    last_log_time = 0.0
    logged_lines = 0

    try:
        while True:
            now = time.monotonic()
            if period:
                sleep_for = period - (now - last)
                if sleep_for > 0:
                    time.sleep(sleep_for)
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

            # Drive. A bus error here must end the run through the normal path — letting it
            # escape skips the stop and leaves the wheels turning.
            if car:
                try:
                    car.drive(command.left, command.right)
                except NeZhaError as exc:
                    drive_error = exc
                    break

            # Log — bits are physical P1..P4, left to right along the bar.
            # Only on change by default: a car tracking a straight line holds
            # one reading for thousands of cycles and printing each of them
            # buries the transitions that actually matter.
            key = (reading.physical, command.state, command.left, command.right)
            stale = (now - last_log_time) >= args.heartbeat_s
            if args.log_every or key != last_logged or stale:
                ch_str = "".join(str(c) for c in reading.physical)
                status = "OK" if reading.visible else "LOST"
                where = f"{nav.junctions.pending.name[:14]:14s}"
                print(
                    f"[{elapsed:6.1f}s] #{frame_index:6d} "
                    f"{status:5s} P{ch_str} {reading.state.kind.value:9s} {where} -> "
                    f"{command.state.value:14s} L{command.left:4d} R{command.right:4d} "
                    f"| {command.reason}"
                )
                last_logged = key
                last_log_time = now
                logged_lines += 1

            if command.state is IRNavState.STOPPED:
                print(f"\nRoute complete: {command.reason}")
                break

            if args.duration and elapsed >= args.duration:
                print(f"\nDuration limit reached ({args.duration}s)")
                break

    except KeyboardInterrupt:
        print("\nStopped by operator")
    finally:
        if car:
            if not car.stop(best_effort=True):
                print("\n*** WHEELS MAY STILL BE TURNING — CUT POWER NOW ***")
            car.close()
        GPIO.cleanup()
        elapsed = time.monotonic() - start
        print()
        print("=" * 70)
        rate = frame_index / elapsed if elapsed else 0.0
        print(f"Test summary: {elapsed:.1f}s, {frame_index} cycles ({rate:.0f} Hz)")
        print(f"  Log lines written: {logged_lines}")
        print(f"  Line visible: {line_found_count} cycles")
        print(f"  Line lost: {line_lost_count} cycles")
        print(f"  Line-recovery searches: {search_entries}")
        print(f"  Junctions taken: {nav.junctions_seen}  (last: {nav.last_junction or 'none'})")
        print(f"  Junctions rejected by the distance gate: {nav.junctions_rejected}")
        print(f"  Next junction expected: {nav.junctions.pending.name}")
        if car:
            print(f"  I2C writes retried: {car.board.write_retries}")
        if drive_error:
            print(f"  Run ended early on a bus error: {drive_error}")
        noise_pct = 100 * nav.noise_frames / frame_index if frame_index else 0.0
        print(f"  Noise/hold frames: {nav.noise_frames} ({noise_pct:.1f}%)")
        if noise_pct > 5.0:
            print("    ^ over 5%: raise the sensor bar toward 2cm, or re-tune the pots.")
            print("      Non-contiguous readings cannot come from the line itself.")
        print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
