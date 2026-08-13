#!/usr/bin/env python3
"""Battery and power-health check for the Raspberry Pi 5 car build.

Run on the Raspberry Pi (safe over SSH, no moving parts):

    python3 examples/08_battery_check.py

Reads (all without sudo on Raspberry Pi OS Bookworm+):
  - EXT5V_V: the external 5V rail voltage (battery feeds the NeZha board, which
    feeds this rail via Pin 4). Expect >= 4.8V on this build.
  - get_throttled: historical + current undervoltage / throttling / soft-temp bits
  - measure_temp: SoC temperature

Exit code 0 = no active warning (EXT5V_V >= threshold and no "now" throttle bits set);
1 = at least one active problem detected.
"""

from __future__ import annotations

import subprocess
import sys

EXT5V_MIN = 4.8  # volts; below this warn
TEMP_MAX = 80.0  # °C; soft limit is around 85°C on Pi 5

# get_throttled bits (from the Raspberry Pi documentation)
THROTTLE_BITS: dict[int, tuple[str, str]] = {
    0x1: ("Undervoltage occurred", "past"),
    0x2: ("ARM frequency capped occurred", "past"),
    0x4: ("Throttled occurred", "past"),
    0x8: ("Soft temperature limit occurred", "past"),
    0x10000: ("Undervoltage now", "current"),
    0x20000: ("ARM frequency capped now", "current"),
    0x40000: ("Throttled now", "current"),
    0x80000: ("Soft temperature limit now", "current"),
}


def vcgencmd(*args: str) -> str:
    out = subprocess.run(["vcgencmd", *args], capture_output=True, text=True, timeout=10)
    return out.stdout.strip()


def main() -> int:
    problems = 0

    print("Battery / power-health check")
    print("=" * 40)

    # 1. External 5V rail (fed from the battery via the NeZha board)
    raw = vcgencmd("pmic_read_adc", "EXT5V_V")
    volt = None
    try:
        volt = float(raw.split("=")[1].replace("V", "").strip())
    except (IndexError, ValueError):
        print(f"[FAIL] could not parse EXT5V_V: {raw!r}")
        problems += 1
    else:
        ok = volt >= EXT5V_MIN
        mark = "OK" if ok else "LOW"
        print(f"[{mark}] EXT5V_V = {volt:.3f} V  (threshold {EXT5V_MIN} V)")
        if not ok:
            problems += 1

    # 2. Throttling / undervoltage status
    throttled_raw = vcgencmd("get_throttled")
    bits = 0
    try:
        bits = int(throttled_raw.split("=")[1].strip(), 16)
    except (IndexError, ValueError):
        print(f"[FAIL] could not parse get_throttled: {throttled_raw!r}")
        problems += 1
    else:
        active = False
        for mask, (label, kind) in THROTTLE_BITS.items():
            if bits & mask:
                active = True
                print(f"[WARN] {label} ({kind})")
                if kind == "current":
                    problems += 1
        if not active:
            print("[OK] get_throttled = 0x0 — no undervoltage or throttling recorded")

    # 3. Temperature
    temp_raw = vcgencmd("measure_temp")
    try:
        temp = float(temp_raw.split("=")[1].replace("'C", "").strip())
    except (IndexError, ValueError):
        print(f"[FAIL] could not parse temperature: {temp_raw!r}")
        problems += 1
    else:
        ok = temp < TEMP_MAX
        print(f"[{'OK' if ok else 'HOT'}] temperature = {temp:.1f} °C  (limit {TEMP_MAX:.0f} °C)")
        if not ok:
            problems += 1

    print("-" * 40)
    if problems:
        print(f"⚠️  {problems} problem(s) found — check the battery / power supply.")
        return 1
    print("✓ Power health OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
