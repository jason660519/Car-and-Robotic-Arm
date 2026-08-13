# 2026-08-14 Sensor & AI Camera Verification

## Result

The HC-SR04 obstacle sensor was wired around the NeZha I2C pin conflict and verified over SSH;
the AI Camera (IMX500) was verified end-to-end including **on-sensor NPU inference (30 fps)**.
Three new test scripts were added (`examples/06/07/08`), the rule about running motor tests over
SSH was relaxed to a conditional form, and the README now documents all eight test scripts.

## HC-SR04 Wiring Correction (NeZha I2C Pin Conflict)

The stock wiring table used `Pin 6` for GND, but this build's NeZha driver board already occupies
`Pin 3 (SDA)`, `Pin 4 (5V)`, `Pin 5 (SCL)`, and `Pin 6 (GND)` for I2C + power.

Verified alternative wiring (documented in `docs/hardware/hc-sr04-ultrasonic-sensor.md`):

| HC-SR04 | Pi Pin | BCM GPIO |
|---|---|---|
| VCC | Pin 2 | 5V |
| GND | Pin 9 | Ground |
| TRIG | Pin 11 | GPIO 17 |
| ECHO | Pin 13 | GPIO 27 (via 2.2k/1k divider) |

GND, TRIG, ECHO sit together on the left column (9, 11, 13); only 5V is pulled separately.

## SSH Verification (Mac -> Pi)

Connection: `ssh carpi` → `dannypi@danny-raspberrypi5-8gram-225gssd.local` (192.168.1.27, Pi 5,
kernel 6.18.34 aarch64).

| Check | Command | Result |
|---|---|---|
| HC-SR04 distance | `python3 /tmp/hc_sr04_test.py` | 6/6 readings, stable 255.6 cm |
| NeZha I2C link | `.venv/bin/python examples/01_i2c_probe.py` | `0x40` responded, reset OK, LED OK |
| Motor mapping | `.venv/bin/python examples/02_motor_check.py` | M1-M4 all moved, matches `config.py` |
| AI Camera | `python3 examples/05_ai_camera_check.py --photo` | IMX500 detected, 4056x3040 still captured |
| AI Camera inference | `python3 examples/05_ai_camera_check.py --inference` | mobilenet-ssd, 30 fps for 120 s |
| Obstacle detector | `python3 examples/06_ultrasonic_avoidance.py --trials 8 --threshold 50` | 8/8, avg 31.3 cm, warning triggered |
| Avoidance loop (dry-run) | `PYTHONPATH=src python3 examples/07_obstacle_avoidance_drive.py --dry-run` | 33 loops, sensor logic OK |
| Avoidance loop (ground) | `PYTHONPATH=src python3 examples/07_obstacle_avoidance_drive.py --ground --duration 30 --threshold 40` | 109 loops, stop+spin on obstacle |
| Battery health | `python3 examples/08_battery_check.py` | EXT5V_V 4.89 V, **throttle warning, see below** |

## New Test Scripts (committed)

- `examples/06_ultrasonic_avoidance.py` — HC-SR04 distance + obstacle warning (`--trials`,
  `--threshold`). Runs with the system interpreter; no motors involved.
- `examples/07_obstacle_avoidance_drive.py` — closed-loop avoidance: distance > threshold → forward,
  distance <= threshold → stop + spin. `--dry-run` never drives motors; `--ground` for a floor run.
  Needs `PYTHONPATH=src python3` (system interpreter has RPi.GPIO; the uv venv does not).
- `examples/08_battery_check.py` — reads `EXT5V_V`, `get_throttled` bits, and temperature; all
  readable without sudo.

## Rule Change (AGENTS.md / CLAUDE.md)

Rule 3 changed from "do not run motor-moving programs on behalf of the user" to: motor tests may
run over SSH when **an operator is physically beside the robot and the wheels are lifted or the
chassis secured**. This matches the existing safety section in `docs/setup/mac-to-raspberry-pi-access.md`.

## Pitfalls Hit Today

1. **`sudo` needs a password over SSH** — `sudo -n` fails; `i2cdetect` and `apt install` had to be
   run by the user on the Pi (or with `ssh -t`).
2. **NeZha occupies Pin 3/4/5/6** — any new sensor wiring must avoid them; HC-SR04 GND moved to Pin 9.
3. **The uv venv has no `RPi.GPIO`/`gpiozero`** — sensor scripts use the system `python3`; to use the
   `carbot` package too, run with `PYTHONPATH=src python3` (src-layout).
4. **IMX500 model path is `/usr/share/imx500-models`** — not `/usr/share/rpicam-apps/imx500` (that
   directory does not exist). 23 `.rpk` models are installed.
5. **IMX500 postprocess package paths** — `rpicam-apps-imx500-postprocess` installs json configs to
   `/usr/share/rpi-camera-assets/` and the lib to
   `/usr/lib/aarch64-linux-gnu/rpicam-apps-postproc/imx500-postproc.so`.
6. **First inference run uploads the network firmware (~3.8 MB)** — takes minutes; a 5 s timeout
   aborts it with exit 255. The check now allows 120 s and warns about the upload.
7. **Wrong default model choice** — `face_detect_cv.json` was picked by name; the check now prefers
   `mobilenet`/`ssd` object-detection configs.
8. **Battery:** `get_throttled = 0x50000` = **undervoltage now + throttling now** (EXT5V_V 4.89 V is
   within range). The 1200 mAh battery is marginal for motor loads — recharge/replace before
   demanding runs.

## Git

- `2abac93` Add HC-SR04 avoidance scripts and document verified hardware tests (8 files)
- `55f4406` fix(05): locate IMX500 postprocess config in rpi-camera-assets; verify on-sensor inference
- Both pushed to `origin/main`.

## Next Steps

- `examples/03_drive.py` ground run (operator beside the car)
- `examples/04_servo_check.py` arm servos (operator beside the car)
- Recharge/replace the battery and re-run `examples/08_battery_check.py` until `✓ Power health OK`
- Optionally wire IMX500 detections into the avoidance loop (vision + ultrasonic fusion)
