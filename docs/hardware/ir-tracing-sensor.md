# Yahboom 4-Channel IR Tracing Sensor Integration

This document records the verified wiring and signal convention for the Yahboom
4-channel IR tracing (line-follower) module in `assets/inventory/` (photos
`041`/`042`). **Verified on the real car (2026-08-17)** — tested with
`examples/36_ir_tracing_check.py`.

## Overview

The module is a 4-channel reflective IR line sensor built around an LM339
comparator. Each channel has an IR LED/phototransistor pair and its own
sensitivity potentiometer. It distinguishes a black line on a white surface and
provides four independent TTL digital outputs (`Out1`–`Out4`).

**Detection distance**: ~1–3 cm, adjustable per-channel via the onboard
potentiometers.

## Reading Convention (Applied in Code)

`src/carbot/ir_tracing.py` normalizes every channel to the same convention used
by the rest of the line-following code:

```
normalized 1  ->  black line under the channel
normalized 0  ->  white surface under the channel
```

Raw comparator polarity varies between boards, so the driver takes an
`invert` set of channel indices. The default assumes **raw HIGH = black**
(`BLACK_IS_HIGH = True`); if a channel reads 0 while over black, add its index
to `invert`.

## Verified Wiring (2026-08-17)

This build uses these GPIO pins:

- NeZha driver board: `Pin 3` (SDA), `Pin 4` (5V), `Pin 5` (SCL), `Pin 6` (GND)
- HC-SR04 ultrasonic: `Pin 2` (5V), `Pin 9` (GND), `Pin 11` (GPIO 17, TRIG),
  `Pin 13` (GPIO 27, ECHO)
- **IR tracing sensor (verified):** powered from 3.3V, no level-shifting needed

| Tracing Pin | Raspberry Pi Pin | BCM GPIO | Purpose |
|---|---|---|---|
| **VCC** | Pin 1 | 3.3V | Power supply (safe for 3.3V logic outputs) |
| **GND** | Pin 14 | Ground | Ground reference |
| **Out1** | Pin 18 | GPIO 24 | Channel 1 digital out |
| **Out2** | Pin 22 | GPIO 25 | Channel 2 digital out |
| **Out3** | Pin 15 | GPIO 22 | Channel 3 digital out |
| **Out4** | Pin 16 | GPIO 23 | Channel 4 digital out |

### Pin Conflict Resolution (HC-SR04)

The original planned wiring conflicted with the HC-SR04 TRIG/ECHO pins (GPIO 17/27).
The conflict was **resolved by moving the IR tracing sensor to free GPIOs** (GPIO 24/25),
avoiding the need for voltage-level shifting. The 3.3V power rail is used directly.

## Signal Logic

```
raw HIGH (default) -> black line under the channel  -> normalized 1
raw LOW            -> white surface under the channel -> normalized 0
```

Flip a channel with `invert={index}` when its raw polarity is opposite.

## Python Usage

```python
from RPi import GPIO
from carbot.ir_tracing import IRTracingSensor

PINS = (24, 25, 22, 23)  # Out1..Out4 — verified on this build

GPIO.setmode(GPIO.BCM)
for pin in PINS:
    GPIO.setup(pin, GPIO.IN)

sensor = IRTracingSensor(PINS, GPIO)  # no inversion needed
readings = sensor.read()  # (1, 0, 1, 0): 1 = black, 0 = white, in Out order
```

Test on hardware (no motors, safe over SSH):

```bash
PYTHONPATH=src python3 examples/36_ir_tracing_check.py --pins 24,25,22,23
```

**Calibration result (2026-08-17):** All four channels verified:
- Over black surface: 1, 1, 1, 1 ✓
- Over white surface: 0, 0, 0, 0 ✓
- No inversion required

Tune each potentiometer with the car powered but wheels lifted, watching the
readout while moving the sensor between black and white.

## Related Files in This Project

- [docs/hardware/raspberry-pi-5-pinout.md](raspberry-pi-5-pinout.md) — Complete GPIO reference and this build's sensor wiring table
- [docs/hardware/hc-sr04-ultrasonic-sensor.md](hc-sr04-ultrasonic-sensor.md) — Ultrasonic sensor (shares planned GPIO 17/27)
- [docs/hardware/ir-obstacle-sensor.md](ir-obstacle-sensor.md) — Single-channel IR obstacle sensor (different module)
- [docs/progress/2026-08-17-ir-tracing-sensor.md](../progress/2026-08-17-ir-tracing-sensor.md) — Work log for this driver
- `assets/inventory/041_Yahboom_4Channel_Tracing_Sensor_*.jpg` — Physical module photos
- `site/src/data/modules.json` — Module catalog entry with the original wiring plan
