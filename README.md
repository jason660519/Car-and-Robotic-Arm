# Car and Robotic Arm

![Smart car and robotic arm build](assets/assembly/021_RobotCar_With_RoboticArm_Combined.jpg)

A Raspberry Pi 5 smart car project with real hardware notes, verified wiring, and step-by-step build records.

[Live Site](https://jason660519.github.io/Car-and-Robotic-Arm/) · [Inventory](https://jason660519.github.io/Car-and-Robotic-Arm/inventory/) · [Assembly Guide](https://jason660519.github.io/Car-and-Robotic-Arm/assembly-guide/)

## Why This Repo

- Verified Raspberry Pi 5 to NeZha I2C communication on real hardware
- Real photos, wiring notes, and assembly references collected in one place
- Runnable Python checks for bring-up, motor mapping, and basic driving
- A bilingual project site for browsing parts and build progress

## Current Status

| Area | Status |
|---|---|
| I2C communication | Verified at address `0x40` |
| Motor mapping | Verified and written back into `src/carbot/config.py` |
| Driving test | First low-speed ground run passed |
| AI Camera (IMX500) | Detected and still capture verified (2026-08) |
| Obstacle sensor (HC-SR04) | Wiring verified, distance readings OK (2026-08) |
| Robotic arm | Still evolving because of damaged parts and compatibility tradeoffs |

## Start Here

1. Read the verified bring-up guide: [docs/setup/raspberry-pi-first-run.md](docs/setup/raspberry-pi-first-run.md)
2. Browse the project website: [Live Site](https://jason660519.github.io/Car-and-Robotic-Arm/)
3. Run the hardware checks in order:

```bash
uv sync
uv run python examples/01_i2c_probe.py              # I2C link to the NeZha board — no moving parts
uv run python examples/02_motor_check.py            # ⚠️ lift the car; operator beside it
uv run python examples/03_drive.py                  # ⚠️ low-speed ground run; operator beside it
uv run python examples/04_servo_check.py            # ⚠️ arm servos; operator beside it
python3 examples/05_ai_camera_check.py --photo      # AI Camera (IMX500) — system interpreter
python3 examples/06_ultrasonic_avoidance.py         # HC-SR04 obstacle detector — no moving parts
PYTHONPATH=src python3 examples/07_obstacle_avoidance_drive.py --dry-run  # sensor only first
PYTHONPATH=src python3 examples/07_obstacle_avoidance_drive.py            # ⚠️ avoidance run, operator beside it
python3 examples/08_battery_check.py                # battery / power health — no moving parts
PYTHONPATH=src python3 examples/09_room_scan.py     # ⚠️ spin-scan the room (HC-SR04), operator beside it
PYTHONPATH=src python3 examples/10_calibrate_motion.py  # ⚠️ calibrate fwd speed via ultrasonic
PYTHONPATH=src python3 examples/11_explore_mapping.py --steps 8  # ⚠️ M3 exploration loop
```

The chassis and arm are controlled by the **Yourfun NeZha bus driver board**. A Raspberry Pi 5
communicates with the board over I2C at address `0x40` to drive four DC motors, four servo
channels, the onboard LEDs, and optional encoder inputs.

## Hardware

| Item | Model |
|---|---|
| Main controller | Raspberry Pi 5 |
| Driver board | Yourfun NeZha bus driver board (`0x40` over I2C) |
| Chassis | Dasheng multi-form robot car chassis, 4x N20 motors |
| Robotic arm | Desktop-class 3-DOF arm |
| Battery | HXS 18650 11.1V 1200mAh |

## Wiring: NeZha to Raspberry Pi 5 (Verified)

| Raspberry Pi Pin | BCM GPIO | NeZha Signal | Purpose |
|---|---|---|---|
| Pin 3 | GPIO 2 | SDA | I2C data |
| Pin 4 | Power | 5V | Power supply |
| Pin 5 | GPIO 3 | SCL | I2C clock |
| Pin 6 | Ground | GND | Ground reference |

For complete wiring notes, see [docs/hardware/nezha-integration-notes.md](docs/hardware/nezha-integration-notes.md).

## Quick Start

Run the examples in order. Scripts `01` and `05`-`06` are safe to run over SSH
(no motors or servos move); `02`-`04` require an operator standing beside the robot who can cut
main power instantly.

| # | Script | What it checks | Run with | Safety |
|---|---|---|---|---|
| 01 | `examples/01_i2c_probe.py` | I2C link to the NeZha driver board at `0x40`, reset command, head LED path | `uv run python examples/01_i2c_probe.py` | ✅ No moving parts |
| 02 | `examples/02_motor_check.py` | Wheel → motor port mapping (`M1`-`M4`) and forward/reverse direction | `uv run python examples/02_motor_check.py` | ⚠️ Lift the car, operator beside it |
| 03 | `examples/03_drive.py` | Minimal differential-drive movement on the ground | `uv run python examples/03_drive.py` | ⚠️ Low speed, operator beside it |
| 04 | `examples/04_servo_check.py` | Arm servos `S2`-`S4`, one channel at a time | `uv run python examples/04_servo_check.py` | ⚠️ Operator beside it |
| 05 | `examples/05_ai_camera_check.py` | AI Camera (IMX500) detected, picamera2 capture, models listed; `--photo` saves a still, `--inference` runs an on-sensor object-detection pass (first run uploads the model to the camera — takes a few minutes) | `python3 examples/05_ai_camera_check.py --photo` | ✅ No moving parts (use system interpreter, not `uv`) |
| 06 | `examples/06_ultrasonic_avoidance.py` | HC-SR04 obstacle detector: distance readings + obstacle warning; `--trials`/`--threshold` to tune | `python3 examples/06_ultrasonic_avoidance.py` | ✅ No moving parts |
| 07 | `examples/07_obstacle_avoidance_drive.py` | Closed-loop avoidance: HC-SR04 drives the car (forward / stop + spin); `--dry-run` tests the sensor loop only | `PYTHONPATH=src python3 examples/07_obstacle_avoidance_drive.py` | ⚠️ Operator beside it; lifted by default, `--ground` for a floor run |
| 08 | `examples/08_battery_check.py` | Battery / power health: `EXT5V_V`, `get_throttled` bits, temperature | `python3 examples/08_battery_check.py` | ✅ No moving parts |
| 09 | `examples/09_room_scan.py` | Room spin-scan (M1): logs the HC-SR04 polar distance profile while the car spins; one frame of the mapping loop | `PYTHONPATH=src python3 examples/09_room_scan.py` | ⚠️ Operator beside it (lifted or floor) |
| 10 | `examples/10_calibrate_motion.py` | Calibrate forward speed (cm/s) with the HC-SR04; needs a flat board 20-60 cm ahead | `PYTHONPATH=src python3 examples/10_calibrate_motion.py` | ⚠️ Operator beside it, car on floor |
| 11 | `examples/11_explore_mapping.py` | M3 exploration loop: spin-scan → ICP (gap-anchored) → occupancy grid → small step; crash detection stops on bad lock-in | `PYTHONPATH=src python3 examples/11_explore_mapping.py --steps 8` | ⚠️ Operator beside it |

Expected results (verified on this build, 2026-08):

- `01` prints `✓ Probe finished successfully`.
- `02` runs each motor forward then reverse for 1 s; all four wheels move, matching
  `src/carbot/config.py` (`M1`=rear-left, `M2`=rear-right, `M3`=front-right, `M4`=front-left,
  `INVERTED_MOTORS={2, 3}`).
- `03` performs a short low-speed differential-drive run.
- `04` sweeps each arm servo through a small range with the operator watching.
- `05` prints `All checks passed` and (with `--photo`) writes `/tmp/ai-camera-check.jpg`.
- `06` prints an average distance in cm and warns when it drops below the obstacle threshold.
- `07` prints one `clear`/`OBSTACLE` decision per loop; `--dry-run` never drives motors.
- `08` prints `✓ Power health OK.` when `EXT5V_V >= 4.8 V` with no current throttle bits
  (a non-zero `get_throttled` with current bits set means low battery / power problems —
  fix the power supply before motor tests).

## Working From a Mac

The code runs on the Raspberry Pi, not on your laptop — only the Pi is wired to the NeZha board
over I2C. [docs/setup/mac-to-raspberry-pi-access.md](docs/setup/mac-to-raspberry-pi-access.md)
covers how to reach it:

| Method | Use it for |
|---|---|
| **SSH** | Terminal work — `git`, `uv`, running the examples. The everyday default. |
| **[Raspberry Pi Connect](https://connect.raspberrypi.com)** | Reaching the Pi from outside your home network, through a browser. Free for personal use. |
| **VNC** | The graphical desktop over the local network. |
| **[Deskflow](docs/setup/deskflow-macos-raspberrypi.md)** | Sharing one keyboard and mouse across a Mac and a Pi on the same desk. |

### SSH Quick Reference (this build)

| Parameter | Value |
|---|---|
| Username | `dannypi` |
| mDNS hostname | `danny-raspberrypi5-8gram-225gssd.local` |
| Current IP | `192.168.1.27` — DHCP assigned, can change; prefer the hostname |

Set up passwordless login once — run these **on the Mac** (enter the Pi password when prompted):

```bash
ssh-copy-id dannypi@danny-raspberrypi5-8gram-225gssd.local

cat >> ~/.ssh/config <<'EOF'

Host carpi
    HostName danny-raspberrypi5-8gram-225gssd.local
    User dannypi
EOF
```

After that, `ssh carpi` connects directly:

```bash
ssh carpi 'whoami && hostname -I'
```

Power health checks — run on the Pi (e.g. via `ssh carpi`):

```bash
vcgencmd get_throttled                # 0x0 = healthy; non-zero bits mean past/active undervoltage or throttling
sudo vcgencmd pmic_read_adc EXT5V_V   # expect >= 4.8V when fed by the battery pack
```

Read the safety section before running anything remotely: the motor and servo scripts assume an
operator standing within reach of the main power switch.

## Repository Layout

| Path | Purpose |
|---|---|
| [CONVENTIONS.md](CONVENTIONS.md) | File placement and naming rules for this repository |
| [docs/hardware/](docs/hardware/) | NeZha protocol notes, Raspberry Pi pinout, integration notes |
| [docs/setup/](docs/setup/) | Setup and bring-up guides |
| [src/carbot/](src/carbot/) | Python driver and control code |
| [examples/](examples/) | Runnable hardware verification scripts |
| [site/](site/) | Astro source for the project website |
| [assets/](assets/) | Photos, diagrams, and other project assets |
| [vendor/](vendor/) | Vendor material kept for reference |

## Website

```bash
npm install
npm run dev
```

Local preview:
<http://localhost:4321/Car-and-Robotic-Arm/>

The website includes both bilingual and English routes. Architecture notes are recorded in
[ADR 0001](docs/adr/0001-static-site-architecture.md).

## Safety Notes

- The NeZha board must be powered from **12V**. Reversed polarity can destroy the board.
- If the board's `5V` rail powers the Raspberry Pi through `Pin 2` or `Pin 4`, do **not**
  connect USB-C power to the Raspberry Pi at the same time.
- Keep the I2C clock at or below **200kHz**. Raspberry Pi defaults to 100kHz, which is correct.
- Lift the car so all wheels are off the ground before the first motor test.
