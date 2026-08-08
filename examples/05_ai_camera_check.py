#!/usr/bin/env python3
"""Verify the Raspberry Pi AI Camera (IMX500) is detected and captures frames.

Run this ON the Raspberry Pi, not on the Mac:

    python3 examples/05_ai_camera_check.py           # detection only
    python3 examples/05_ai_camera_check.py --photo   # also capture a test still

Checks performed:
1. A libcamera camera tool (`rpicam-hello` / `libcamera-hello`) is installed
2. The tool lists at least one camera and an IMX500 sensor is among them
3. IMX500 pre-trained model files are present (informational)
4. Picamera2 can open the camera and capture a still image (only with --photo)

Exit code 0 = every hard check passed.

Notes:
- Prefer the system interpreter. Picamera2 ships as an apt package
  (`sudo apt install python3-picamera2`), not in this project's uv venv.
- If the camera was just plugged in, reboot the Pi once before testing.
- If no camera is listed, check the ribbon cable and camera port
  (the AI Camera uses the two-lane CSI connector next to the HDMI ports).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

CAMERA_TOOLS = ("rpicam-hello", "libcamera-hello")
IMX500_NET_DIR = Path("/usr/share/rpicam-apps/imx500")
PHOTO_PATH = Path("/tmp/ai-camera-check.jpg")

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    """Print a PASS/FAIL line and remember failures for the summary."""
    status = "PASS" if ok else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")
    if not ok:
        failures.append(label)


def camera_listing() -> str | None:
    """Return combined stdout+stderr of the first available camera tool, or None."""
    for tool in CAMERA_TOOLS:
        if shutil.which(tool) is None:
            continue
        try:
            result = subprocess.run(
                [tool, "--list-cameras"], capture_output=True, text=True, timeout=30, check=False
            )
            return f"{result.stdout}\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return None
    return None


def check_tool_and_camera() -> None:
    listing = camera_listing()
    if listing is None:
        check(
            "camera tool installed",
            False,
            "neither rpicam-hello nor libcamera-hello found — install with: "
            "sudo apt install rpicam-apps",
        )
        return

    lowered = listing.lower()
    check("camera tool runs", listing.strip() != "", "got output from the tool")
    if "no cameras available" in lowered:
        check(
            "at least one camera detected",
            False,
            "the tool reports 'no cameras available' — check the ribbon cable and reboot",
        )
        return

    has_imx500 = "imx500" in lowered
    check(
        "IMX500 (AI Camera) detected",
        has_imx500,
        "found in the camera list" if has_imx500 else "camera(s) present but no IMX500 in the list",
    )


def check_model_files() -> None:
    if not IMX500_NET_DIR.is_dir():
        print(f"[INFO] IMX500 model directory not found: {IMX500_NET_DIR}")
        print("       The camera still works; models are only needed for on-sensor inference.")
        return
    files = sorted(IMX500_NET_DIR.iterdir())
    print(f"[INFO] IMX500 models available: {len(files)} file(s) in {IMX500_NET_DIR}")
    for entry in files[:8]:
        print(f"       - {entry.name}")


def capture_still(picamera2_cls: type) -> None:
    try:
        camera = picamera2_cls()
        camera.configure(camera.create_still_configuration())
        camera.start()
        time.sleep(1.5)  # let auto-exposure converge
        camera.capture_file(str(PHOTO_PATH))
        camera.stop()
        ok = PHOTO_PATH.exists() and PHOTO_PATH.stat().st_size > 0
        check(
            "still capture",
            ok,
            f"wrote {PHOTO_PATH} ({PHOTO_PATH.stat().st_size} bytes)" if ok else "capture produced no file",
        )
    except Exception as exc:  # noqa: BLE001 - report any backend error
        check("still capture", False, str(exc))


def check_picamera2(photo: bool) -> None:
    try:
        from picamera2 import Picamera2
    except ImportError:
        check(
            "picamera2 import",
            False,
            "run with the system python3 (picamera2 is an apt package, not a uv dependency)",
        )
        return

    try:
        cameras = Picamera2.global_camera_info()
    except Exception as exc:  # noqa: BLE001 - report any backend error
        check("picamera2 enumerates cameras", False, str(exc))
        return

    if not cameras:
        check("picamera2 sees a camera", False, "no cameras reported")
        return

    models = [c.get("Model", "?") for c in cameras]
    check("picamera2 sees a camera", True, ", ".join(models))
    check(
        "IMX500 visible to picamera2",
        any("imx500" in m.lower() for m in models),
        f"models: {', '.join(models)}",
    )

    if photo:
        capture_still(Picamera2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the Raspberry Pi AI Camera (IMX500).")
    parser.add_argument(
        "--photo",
        action="store_true",
        help="capture a test still image to /tmp/ai-camera-check.jpg",
    )
    args = parser.parse_args()

    print("Raspberry Pi AI Camera check")
    print("=" * 30)
    check_tool_and_camera()
    check_model_files()
    check_picamera2(args.photo)

    print()
    if failures:
        print(f"FAILED — {len(failures)} check(s) failed:")
        for item in failures:
            print(f"  - {item}")
        print("If the camera was just connected, reboot the Pi and try again.")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
