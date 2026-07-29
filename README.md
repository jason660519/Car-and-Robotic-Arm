# Car and Robotic Arm

A Raspberry Pi driven four-wheel robot car with a three-degree-of-freedom robotic arm.

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

Start with the verified bring-up guide:
[docs/setup/raspberry-pi-first-run.md](docs/setup/raspberry-pi-first-run.md)

```bash
uv sync
```

```bash
uv run python examples/01_i2c_probe.py
uv run python examples/02_motor_check.py
uv run python examples/03_drive.py
```

Run the examples in order:

1. `01_i2c_probe.py` checks communication without moving the hardware.
2. `02_motor_check.py` maps each wheel to `M1`-`M4` and confirms direction.
3. `03_drive.py` runs a minimal differential-drive movement test.

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
