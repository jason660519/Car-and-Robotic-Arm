#!/usr/bin/env python3
"""Capture one downward frame and report the black-line detection on it.

Stationary, **no motors** — safe to run over SSH. The camera looks down at the
track map; :func:`carbot.line_follow.detect_line` finds the dark tracking line
and this script saves the raw frame plus an annotated overlay so the operator
can eyeball whether the ROI, threshold, and centroid look right before any
closed-loop driving is attempted.

    # on the Pi, from the repo root
    PYTHONPATH=src python3 examples/25_line_follow_capture.py
    PYTHONPATH=src python3 examples/25_line_follow_capture.py --threshold 100 --output /tmp/line-follow

The overlay draws: the ROI band, the frame centre line, a dot for every scan
row that saw the line, and a cross at the aggregated centroid. The printed
summary line is what the future controller will steer on.

Run with the system python3: picamera2 is an apt package and OpenCV ships with
Raspberry Pi OS. See `examples/05_ai_camera_check.py` for the same rationale.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from carbot.line_follow import LinePolicy, detect_line

PREVIEW_SIZE = (2028, 1520)  # same stream shape the closed-loop run will use


def _capture(size: tuple[int, int]) -> object:
    from picamera2 import Picamera2

    camera = Picamera2()
    camera.configure(camera.create_preview_configuration(main={"size": size}))
    camera.start()
    time.sleep(1.5)  # let auto-exposure converge
    frame = camera.capture_array("main")
    camera.close()
    return frame


def _overlay(frame, reading: object, cv2) -> object:
    """Annotate the frame for human inspection."""
    image = frame.copy()
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    height, width = image.shape[:2]
    y_top, y_bottom, _, _ = reading.roi

    cv2.rectangle(image, (0, y_top), (width - 1, y_bottom - 1), (255, 0, 0), 4)
    cv2.line(image, (width // 2, 0), (width // 2, height - 1), (0, 0, 255), 2)

    if reading.centroid_x is not None:
        cv2.drawMarker(
            image, (int(reading.centroid_x), (y_top + y_bottom) // 2),
            (0, 255, 0), cv2.MARKER_CROSS, 40, 6,
        )
    if reading.visible:
        cv2.putText(
            image, f"err={reading.error_px:+.0f}px ({reading.error_fraction:+.2f})",
            (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 255, 0), 4,
        )
        cv2.putText(
            image, f"width={reading.line_width_px:.0f}px rows={reading.tracked_rows}",
            (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3,
        )
    else:
        cv2.putText(
            image, "NO LINE", (20, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 0, 255), 5,
        )
    return image


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture one downward frame and detect the line")
    parser.add_argument("--threshold", type=int, default=LinePolicy().dark_threshold,
                        help="gray value below which a pixel counts as line")
    parser.add_argument("--roi-top", type=float, default=LinePolicy().roi_top,
                        help="ROI top as a fraction of frame height")
    parser.add_argument("--roi-bottom", type=float, default=LinePolicy().roi_bottom,
                        help="ROI bottom as a fraction of frame height")
    parser.add_argument("--output", type=Path, default=Path("/tmp/line-follow"),
                        help="directory for raw and overlay images")
    args = parser.parse_args()

    try:
        frame = _capture(PREVIEW_SIZE)
    except Exception as exc:  # noqa: BLE001 - report any camera backend error
        print(f"camera failed: {exc}", file=sys.stderr)
        print("If the camera was just connected, reboot the Pi once and retry.", file=sys.stderr)
        return 1

    policy = LinePolicy(
        dark_threshold=args.threshold,
        roi_top=args.roi_top,
        roi_bottom=args.roi_bottom,
    )
    reading = detect_line(frame, policy)

    args.output.mkdir(parents=True, exist_ok=True)
    raw_path = args.output / "line-follow-raw.jpg"
    overlay_path = args.output / "line-follow-overlay.jpg"

    import cv2

    cv2.imwrite(str(raw_path), frame)
    cv2.imwrite(str(overlay_path), _overlay(frame, reading, cv2))

    print(f"frame {frame.shape[1]}x{frame.shape[0]}  roi=({policy.roi_top}-{policy.roi_bottom}) "
          f"threshold={policy.dark_threshold}")
    print(f"detection: {reading.summary}")
    print(f"saved: {raw_path}")
    print(f"saved: {overlay_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
