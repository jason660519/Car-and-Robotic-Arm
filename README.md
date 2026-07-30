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
| Robotic arm | Still evolving because of damaged parts and compatibility tradeoffs |

## Start Here

1. Read the verified bring-up guide: [docs/setup/raspberry-pi-first-run.md](docs/setup/raspberry-pi-first-run.md)
2. Browse the project website: [Live Site](https://jason660519.github.io/Car-and-Robotic-Arm/)
3. Run the hardware checks in order:

```bash
uv sync
uv run python examples/01_i2c_probe.py
uv run python examples/02_motor_check.py
uv run python examples/03_drive.py
uv run python examples/04_servo_check.py
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

## Quick Start

Run the examples in order:

1. `01_i2c_probe.py` checks communication without moving the hardware.
2. `02_motor_check.py` maps each wheel to `M1`-`M4` and confirms direction.
3. `03_drive.py` runs a minimal differential-drive movement test.
4. `04_servo_check.py` interactively checks arm servos `S2`-`S4`, one channel at a time, while
   the operator remains beside the robot.

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
