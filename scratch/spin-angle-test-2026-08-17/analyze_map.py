#!/usr/bin/env python3
"""Analyse a ground-map photo: detect AprilTags, report id/position/size.

Runs on the Pi with the system python3 (OpenCV + aruco required):

    python3 /tmp/analyze_map.py /tmp/ground_map_view.jpg
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, "/home/dannypi/Car-and-Robotic-Arm/src")

from carbot.vision import DEFAULT_TAG_SIZE_M, detect_apriltag_poses, load_calibration

CALIBRATION = Path(
    "/home/dannypi/Car-and-Robotic-Arm/assets/reference/"
    "camera-calibration/2026-08-14-imx500-4056x3040/calibration.json"
)


def main() -> int:
    image_path = Path(sys.argv[1])
    tag_size = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_TAG_SIZE_M
    print(f"image: {image_path}  tag_size_m assumed: {tag_size}")

    image = cv2.imread(str(image_path))
    if image is None:
        print(f"cannot read {image_path}")
        return 1
    calibration = load_calibration(CALIBRATION)
    poses = detect_apriltag_poses(image, calibration, tag_size_m=tag_size)
    print(f"detected {len(poses)} AprilTag(s) (36h11)")
    for p in poses:
        corners = np.asarray(p.corners_px, dtype=np.float64)
        side_px = float(np.mean(
            [np.linalg.norm(corners[1] - corners[0]), np.linalg.norm(corners[2] - corners[1])]
        ))
        center = corners.mean(axis=0)
        t = np.asarray(p.translation_m, dtype=np.float64)
        print(
            f"  id={p.tag_id:>3d}  center_px=({center[0]:7.1f},{center[1]:7.1f})  "
            f"side_px={side_px:6.1f}  "
            f"tvec_m=({t[0]:+.3f},{t[1]:+.3f},{t[2]:+.3f})  "
            f"yaw={p.yaw_deg:6.1f}  pitch={p.pitch_deg:6.1f}  roll={p.roll_deg:6.1f}  "
            f"reproj={p.reprojection_error_px:.2f}px"
        )
    if not poses:
        print("no tags found — check the map has 36h11 AprilTags and try other tag sizes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
