#!/usr/bin/env python3
"""Autonomous patrol that avoids what the sonar cannot see, capturing for SfM.

A single forward HC-SR04 sees neither thin chair legs nor an overhead tabletop,
so `examples/17` drove under a chair and stuck on its underside. This patrol
fuses the IMX500's on-sensor object detection with the sonar through
:func:`carbot.vision_avoid.fuse`, and it captures 2028x1520 stills for COLMAP
from the **same camera configuration** — mode 'single', measured in
`docs/progress/2026-08-14-camera-modes-exposure-and-preflight-fix.md`, needs no
mode switching at all.

Per station: read the sonar and the latest detections, fuse them, then either
back up and turn away, or advance one short step. Then capture a **burst** of
overlapping frames — several shots about 20 deg apart — and rotate back to the
original heading before moving on.

The burst exists because single frames did not reconstruct. Ten individually good
frames from one run (all sharp, all well exposed) formed four disconnected
islands when matched pairwise: 600-1500 matches within an island and 10-40
between them, and COLMAP registered only 3 of 10, reporting "no good initial
image pair found". The frames that did connect were the ones taken while the car
drove straight. Random 36-144 deg turns between shots destroy the overlap that
Structure-from-Motion is built on; a ~20 deg step keeps roughly 70% of the 66 deg
field of view in common. Rotating back afterwards keeps the trajectory straight,
which is what linked frames across stations in the first place.

Each shot is also gated on being worth keeping. That gate exists because the
first supervised run kept frames shot 30 cm
from a whiteboard: sharp, correctly exposed, and 70% blank panel. Nothing was
blurred; the frames were simply useless to COLMAP. A capture is now rejected
when the sonar says the camera has no room in front (``--min-standoff-cm``) or
when :mod:`carbot.frame_quality` finds too few textured tiles. Rejected poses
cost a step, not a frame, so the saved set stays contiguous and every file in it
is worth matching. ``--max-steps`` bounds the run when a room rejects most poses.

The avoidance threshold is deliberately *not* raised to the standoff distance: a
45 cm turn threshold is what made an earlier patrol spin in place.

**Motor-moving.** An operator must stand beside the car able to cut main power
instantly. Run `examples/14_preflight_check.py` first.

    # stationary logic check — reads sensors, never drives
    PYTHONPATH=src python3 examples/22_fused_patrol_capture.py --dry-run --frames 10

    # supervised run
    PYTHONPATH=src python3 examples/22_fused_patrol_capture.py --frames 10
    PYTHONPATH=src python3 examples/22_fused_patrol_capture.py --frames 150

Exposure defaults to `auto`. The stationary sweep in `examples/21` preferred spot
metering, but a patrol turns to face every direction, and spot metering blew out
43% of one frame when the car pointed at a window — the sweep never tested that
because the camera never moved. `spot` and `long-shutter-spot` remain available
for comparison. The 97 ms shutter blur risk that sweep left open is *resolved*:
at 38 ms with a 1.0 s settle, captures came back sharp while moving.
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

from carbot.frame_quality import assess_file
from carbot.sonar import Sonar
from carbot.vision_avoid import ObstaclePolicy, detections_from_metadata, fuse

TRIG_PIN = 17  # GPIO 17 (Pin 11)
ECHO_PIN = 27  # GPIO 27 (Pin 13)
# Measured at speed 200 by examples/23_spin_rate_check.py: 53.5 deg/s with a
# startup dead time of 0.005 s, i.e. none worth compensating. The older 43.9
# deg/s came from speed 150 and made every commanded turn ~22% too large.
VERIFIED_SPIN_DEG_PER_S = 53.5
VERIFIED_AT_SPEED = 200
DEFAULT_MODEL = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"
STILL_SIZE = (2028, 1520)
LONG_FRAME_DURATION_US = 100_000

# Exposure presets, measured in examples/21. 'long-shutter-spot' won on
# repeatable keypoints at the lowest gain, but only with the camera stationary.
EXPOSURE_PRESETS = ("auto", "spot", "long-shutter-spot")


def _exposure_controls(preset: str) -> dict[str, object]:
    from libcamera import controls as libcamera_controls

    if preset == "auto":
        return {}
    spot = {"AeMeteringMode": libcamera_controls.AeMeteringModeEnum.Spot}
    if preset == "spot":
        return spot
    return {
        **spot,
        "FrameDurationLimits": (LONG_FRAME_DURATION_US, LONG_FRAME_DURATION_US),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Vision + sonar fused patrol with SfM capture")
    parser.add_argument("--frames", type=int, default=150, help="number of stills to capture")
    parser.add_argument("--dry-run", action="store_true",
                        help="read sensors and fuse, but never drive the motors")
    parser.add_argument("--step-s", type=float, default=1.0, help="seconds of forward per step")
    parser.add_argument("--speed", type=int, default=200, help="drive speed 0-1000")
    parser.add_argument("--backup-s", type=float, default=0.6,
                        help="seconds to reverse before turning (frees the car from a corner)")
    parser.add_argument("--obstacle-cm", type=float, default=30.0,
                        help="sonar distance below which the car turns away")
    parser.add_argument("--turn-min-deg", type=float, default=30.0)
    parser.add_argument("--turn-max-deg", type=float, default=150.0)
    parser.add_argument("--spin-deg-per-s", type=float, default=VERIFIED_SPIN_DEG_PER_S,
                        help=f"spin rate (deg/s); measured {VERIFIED_SPIN_DEG_PER_S} at speed "
                             f"{VERIFIED_AT_SPEED}, re-measure with examples/23 for other speeds")
    parser.add_argument("--burst-frames", type=int, default=5,
                        help="overlapping frames to capture per station (1 = no burst)")
    parser.add_argument("--burst-step-deg", type=float, default=20.0,
                        help="rotation between burst frames; ~20 deg keeps ~70%% overlap")
    parser.add_argument("--settle-s", type=float, default=1.0,
                        help="seconds to let the chassis stop rocking before a capture")
    parser.add_argument("--threshold", type=float, default=0.30,
                        help="detection confidence threshold")
    parser.add_argument("--exposure", choices=EXPOSURE_PRESETS, default="auto",
                        help="auto-exposure preset (see examples/21)")
    parser.add_argument("--min-standoff-cm", type=float, default=50.0,
                        help="do not photograph when the nearest surface is closer than this")
    parser.add_argument("--min-textured-tiles", type=int, default=6,
                        help="reject a capture with fewer textured tiles (of 12)")
    parser.add_argument("--max-steps", type=int, default=0,
                        help="stop after this many steps even if --frames is unmet "
                             "(default: 4x --frames)")
    parser.add_argument("--keep-rejected", action="store_true",
                        help="save rejected captures under <out-dir>/rejected for calibration")
    parser.add_argument("--frame-report", action="store_true",
                        help="print the SfM quality of every accepted capture")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out-dir", type=Path, default=Path("/tmp/room-sfm"))
    args = parser.parse_args()

    if args.turn_min_deg > args.turn_max_deg:
        print("--turn-min-deg must not exceed --turn-max-deg", file=sys.stderr)
        return 1

    policy = ObstaclePolicy(
        confidence_threshold=args.threshold, sonar_stop_cm=args.obstacle_cm
    )

    from RPi import GPIO

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(ECHO_PIN, GPIO.IN)
    sonar = Sonar(TRIG_PIN, ECHO_PIN, GPIO)

    if not args.dry_run:
        answer = input(
            "Operator beside the car, path clear, power ready to cut? (yes/no) "
        ).strip()
        if answer.lower() != "yes":
            print("Re-run when an operator is ready beside the car.")
            GPIO.cleanup()
            return 1

    car = None
    if not args.dry_run:
        from carbot import Car, NeZhaError

        try:
            car = Car()
        except NeZhaError as exc:
            print(f"Connection failed: {exc}")
            print("Run `examples/01_i2c_probe.py` first to debug the link.")
            GPIO.cleanup()
            return 1

    from picamera2 import Picamera2
    from picamera2.devices import IMX500
    from picamera2.devices.imx500 import NetworkIntrinsics

    imx500 = IMX500(args.model)
    intrinsics = imx500.network_intrinsics
    if not intrinsics:
        intrinsics = NetworkIntrinsics()
        intrinsics.task = "object detection"
    if intrinsics.task != "object detection":
        print(f"Model is not an object-detection network (task={intrinsics.task})", file=sys.stderr)
        if car:
            car.close()
        GPIO.cleanup()
        return 1
    intrinsics.update_with_defaults()
    imx500.show_network_fw_progress_bar()

    camera = Picamera2(imx500.camera_num)
    try:
        # Mode 'single': inference and the 2028x1520 still come from one
        # configuration, so there is nothing to switch between captures.
        camera.configure(camera.create_preview_configuration(
            main={"size": STILL_SIZE},
            controls={"FrameRate": intrinsics.inference_rate},
            buffer_count=4,
        ))
        camera.start()
        controls = _exposure_controls(args.exposure)
        if controls:
            camera.set_controls(controls)
        time.sleep(max(args.settle_s, 1.0))
        frame_width, frame_height = camera.camera_configuration()["main"]["size"]
    except Exception:
        camera.close()
        if car:
            car.close()
        GPIO.cleanup()
        raise

    args.out_dir.mkdir(parents=True, exist_ok=True)
    mode = "DRY RUN (no motors)" if args.dry_run else f"driving at speed {args.speed}"
    print(f"Fused patrol: {args.frames} frames, {mode}, exposure={args.exposure}")
    print(f"stop below {args.obstacle_cm:.0f} cm or on a central-low detection "
          f">={args.threshold:.2f}; turn {args.turn_min_deg:.0f}-{args.turn_max_deg:.0f} deg "
          f"after backing up {args.backup_s:.1f}s. Ctrl-C to stop.")
    print("=" * 72)

    max_steps = args.max_steps if args.max_steps > 0 else args.frames * 4
    rejected_dir = args.out_dir / "rejected"
    if args.keep_rejected:
        rejected_dir.mkdir(parents=True, exist_ok=True)
    pending = args.out_dir / "pending.jpg"

    blocked_count = 0
    rejected_count = 0
    empty_bursts = 0
    reject_reasons: dict[str, int] = {}
    n = 0
    step = 0
    try:
        while n < args.frames and step < max_steps:
            step += 1
            kept_this_burst = 0
            distance = sonar.measure_nearest()
            metadata = camera.capture_metadata()
            detections = detections_from_metadata(
                metadata, imx500, intrinsics, camera, policy
            )
            verdict = fuse(distance, detections, (frame_width, frame_height), policy)

            if verdict.blocked:
                blocked_count += 1
                angle = random.uniform(args.turn_min_deg, args.turn_max_deg)
                direction = "left" if random.random() < 0.5 else "right"
                print(f"[{step}] BLOCKED {verdict.reason} -> back up, {direction} {angle:.0f} deg")
                if car:
                    # Back up first: a chassis wedged in a corner physically
                    # cannot spin in place.
                    car.backward(args.speed)
                    time.sleep(args.backup_s)
                    car.stop()
                    time.sleep(0.3)
                    if direction == "left":
                        car.spin_left(args.speed)
                    else:
                        car.spin_right(args.speed)
                    time.sleep(angle / args.spin_deg_per_s)
                    car.stop()
            else:
                print(f"[{step}] clear   {verdict.reason} -> forward {args.step_s:.1f}s")
                if car:
                    car.forward(args.speed)
                    time.sleep(args.step_s)
                    car.stop()

            time.sleep(args.settle_s)  # let the chassis stop rocking

            # A burst of overlapping frames, not one frame per station. Single
            # frames taken 36-144 deg apart shared almost nothing: a pairwise
            # match of one run's ten frames formed four disconnected islands and
            # COLMAP registered only the largest, reporting "no good initial
            # image pair found". Rotating ~20 deg between shots keeps ~70% of the
            # 66 deg field of view in common, so a burst is internally connected.
            for shot in range(max(1, args.burst_frames)):
                if n >= args.frames:
                    break
                if shot > 0 and car:
                    car.spin_right(args.speed)
                    time.sleep(args.burst_step_deg / args.spin_deg_per_s)
                    car.stop()
                    time.sleep(args.settle_s)

                # Re-checked every shot: rotating changes what the camera and
                # the sonar are pointed at, so the gate verdict changes too.
                reason = _standoff_reason(sonar, args.min_standoff_cm)
                quality = None
                if reason is None:
                    camera.capture_file(str(pending))
                    quality, reason = _quality_reason(pending, args.min_textured_tiles)
                elif args.keep_rejected:
                    # Shoot anyway, purely to record what the standoff gate
                    # skipped. Without this the flag saves nothing when standoff
                    # is doing all the rejecting, which is exactly when the
                    # threshold needs calibrating.
                    camera.capture_file(str(pending))

                if reason is None:
                    path = args.out_dir / f"frame-{n:03d}.jpg"
                    pending.replace(path)
                    n += 1
                    kept_this_burst += 1
                    label = f"      {path.name} [{shot + 1}/{args.burst_frames}]"
                    if args.frame_report and quality:
                        print(f"{label}: {quality.summary()}")
                    else:
                        print(f"{label} kept ({n}/{args.frames})")
                else:
                    rejected_count += 1
                    key = reason.split(":")[0]
                    reject_reasons[key] = reject_reasons.get(key, 0) + 1
                    print(f"      no capture [{shot + 1}/{args.burst_frames}]: {reason}")
                    if args.keep_rejected and pending.exists():
                        pending.replace(rejected_dir / f"step-{step:03d}-{shot}.jpg")

            if kept_this_burst == 0:
                empty_bursts += 1
                print("      burst kept nothing — this station is unusable")

            # Undo the burst rotation so the next forward move continues along
            # the previous heading. A straight run is what produced the only
            # frames that ever registered, so the sweep must not let the burst
            # quietly re-aim the car by its full span.
            span = args.burst_step_deg * (max(1, args.burst_frames) - 1)
            if car and span > 0:
                car.spin_left(args.speed)
                time.sleep(span / args.spin_deg_per_s)
                car.stop()
                time.sleep(args.settle_s)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        if car:
            car.stop()
        camera.stop()
        camera.close()
        if car:
            car.close()
        GPIO.cleanup()
        pending.unlink(missing_ok=True)

    print("-" * 72)
    print(f"Kept {n} frames -> {args.out_dir} in {step} stations "
          f"({blocked_count} blocked, {step - blocked_count} forward, "
          f"{rejected_count} captures rejected, {empty_bursts} empty bursts)")
    for key, count in sorted(reject_reasons.items(), key=lambda kv: -kv[1]):
        print(f"  rejected {count}x: {key}")
    if n < args.frames:
        print(f"Stopped at the {max_steps}-step cap with {n}/{args.frames} frames — the room "
              f"is rejecting most poses. Check the reject reasons before raising --max-steps.")
    if args.dry_run:
        print("Dry run: no motor commands were sent.")
    return 0


def _standoff_reason(sonar: Sonar, minimum_cm: float) -> str | None:
    """Reject a pose whose camera is pressed up against a nearby surface.

    A frame shot 30 cm from a whiteboard is 70% blank panel: sharp, correctly
    exposed, and useless to COLMAP. Two such frames were what made the first
    supervised run look like a motion-blur problem when nothing was blurred.
    """
    distance = sonar.measure_nearest()
    if distance is None:
        return "standoff: no sonar reading, cannot confirm the camera has room"
    if distance < minimum_cm:
        # One decimal: rounding to whole cm printed "50 cm < 50 cm", which reads
        # as a broken comparison rather than a 49.6 cm reading.
        return f"standoff: {distance:.1f} cm < {minimum_cm:.1f} cm, too close to a surface"
    return None


def _quality_reason(path: Path, min_textured_tiles: int):
    """Assess a capture; return ``(quality, reason)`` with reason None when usable."""
    try:
        quality = assess_file(str(path))
    except (RuntimeError, ValueError) as exc:
        return None, f"quality: unavailable ({exc})"
    if quality.textured_tiles < min_textured_tiles:
        return quality, (
            f"quality: only {quality.textured_tiles}/{quality.total_tiles} textured tiles "
            f"(need {min_textured_tiles}), {quality.keypoints} keypoints"
        )
    return quality, None


if __name__ == "__main__":
    sys.exit(main())
