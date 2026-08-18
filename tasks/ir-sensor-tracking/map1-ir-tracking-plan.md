# Map1 IR Sensor Tracking Test Plan

**Date:** 2026-08-18  
**Objective:** Drive Map1 circular track using 4-channel IR sensor only (no camera)  
**Location:** /Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/Map1-North.JPG

---

## Hardware Setup

### IR Sensor Wiring (verified 2026-08-17)

```
Yahboom 4-Channel IR Tracing Sensor
  VCC   → Pi 3.3V (Pin 1)
  GND   → Pi GND (Pin 14)
  Out1  → GPIO 24 (Pin 18)  [Left channel 1]
  Out2  → GPIO 25 (Pin 22)  [Left channel 2]
  Out3  → GPIO 22 (Pin 15)  [Right channel 1]
  Out4  → GPIO 23 (Pin 16)  [Right channel 2]
```

### Normalized Reading Convention

- **Normalized 1** = black line under the channel
- **Normalized 0** = white surface under the channel
- All 4 channels verified: no inversion needed (2026-08-17)

### Physical Sensor Position

```
  Out1(L) Out2(L) | Out3(R) Out4(R)
  ├─ ~5mm ────┤ ├─ ~5mm ────┤
     left half      right half
     ~10mm total width (line is ~15mm)
```

---

## Three-Phase Test Plan

### ✅ Phase 1: IR Sensor Calibration Check (2 min, stationary)

**Objective:** Verify 4-channel IR sensor reads correctly over black and white

**Procedure:**
```bash
scripts/map1-phase1-ir-check.sh
```

Equivalent long form, run from the repository root:
```bash
PYTHONPATH=src python3 examples/36_ir_tracing_check.py --pins 24,25,22,23 --invert 0,1,2,3
```

**Steps:**
1. Hold sensor 1-3 cm above the **black line** — expect `(1, 1, 1, 1)`
2. Move sensor to **white paper** — expect `(0, 0, 0, 0)`
3. Repeat 3-5 times, watching for consistency

**Success Criteria:**
- ✓ Black line: all 4 channels read `1`
- ✓ White paper: all 4 channels read `0`
- ✓ `--invert 0,1,2,3` still correct — this replaces the original 2026-08-17
  "no inversion needed" result, which the 2026-08-18 potentiometer retune
  superseded. Polarity is not guaranteed to survive a retune, so treat the
  invert set as something this phase *verifies*, not something it assumes.
  See [docs/hardware/ir-tracing-sensor.md](../../docs/hardware/ir-tracing-sensor.md).

**If a channel is wrong:**
- Record which channel(s) are inverted
- Run with `--invert 0,3` etc. if needed

---

### ✅ Phase 2: Motor Low-Speed Test (3 min, wheels LIFTED)

**Objective:** Verify motor direction and steering ratio before autonomous run

**Procedure:**
```bash
# Wheels must be lifted or chassis secured
PYTHONPATH=src python3 examples/37_map1_motor_test.py
```

**Tests:**
1. Forward 2s — wheels should roll forward
2. Backward 2s — wheels should roll backward
3. Left turn 2s (30% inside ratio) — left wheels slower than right
4. Right turn 2s (30% inside ratio) — right wheels slower than left
5. Left spin 1.5s — rotate counterclockwise in place
6. Right spin 1.5s — rotate clockwise in place

**Success Criteria:**
- ✓ All directions work as expected
- ✓ Turn ratios are proportional (inside wheel ~30% of outside speed)
- ✓ Spin rate ≈ 53°/s at speed 200 (calibrated value)

---

### ✅ Phase 3: Autonomous IR Tracking (2-3 min, on the track)

**Objective:** Car follows Map1 black line using IR sensor only

**Pre-run Checklist:**
- [ ] Car positioned at start line (发车 zone)
- [ ] Black line visible and unobstructed
- [ ] **Operator standing beside car, power plug in hand, ready to cut instantly**
- [ ] All 4 wheels on the ground
- [ ] Raspberry Pi SSH connection confirmed

**Run Script:**
```bash
# Simulation (debug detection, no motor)
PYTHONPATH=src python3 examples/39_map1_ir_line_follow.py \
  --dry-run --duration 30

# Live tracking (operator standing beside car)
PYTHONPATH=src python3 examples/39_map1_ir_line_follow.py \
  --speed 150 --turn-gain 2.0 --duration 120
```

**Real-time Output:**
```
[  0.0s] #   1 OK   1111 err=+0.00 -> L150 R150 | centered 4+4
[  0.5s] #   2 OK   1110 err=+0.25 -> L130 R150 | steer err=+0.25
[  1.0s] #   3 OK   1111 err=-0.00 -> L150 R150 | centered 4+4
[  1.5s] #   4 OK   0111 err=+0.50 -> L100 R150 | steer err=+0.50
```

**Log Columns:**
- `[time]` — elapsed seconds
- `#N` — cycle number (IR reads per second ≈ 10-20 Hz)
- `OK|LOST` — line detection status
- `1111` — channel readings (Out1 Out2 Out3 Out4)
- `err` — steering error fraction (-1.0 = hard left, +1.0 = hard right)
- `L R` — wheel speeds sent to car

---

## Expected Behavior

### Success Trajectory

1. **0-10s:** Accelerate from start zone, stabilize on the line stem
2. **10-60s:** Smooth tracking around the circular path
   - Channels alternate: `1111` (straight) → `1110` (slight right) → `1111` (back center)
   - Error stays within ±0.3
3. **60-120s:** Continue loop, exit when circle is complete

### Error Conditions & Recovery

| Signal | Meaning | Normal? |
|--------|---------|---------|
| `0000` lasting 1-2 cycles | Sensor passes between grid squares or shadow | Yes, car pauses then continues |
| `0000` lasting 5+ cycles | Line completely lost | No — **STOP and check** |
| `1001` flicker | Sensor over line edge, oscillating | Yes, proportional steering corrects |
| `err > 0.5` sustained | Over-correction or line is far off center | No — reduce speed or check alignment |
| `LOST` in log > 30% of time | Sensor never locks the line | No — calibrate or reposition sensor |

---

## Parameter Tuning

If the car overshoots or undershoots curves:

### Too Much Steering (S-bend snake)
```bash
--turn-gain 1.5  # Reduce from 2.0
--speed 150      # Reduce from 200 if still oscillating
```

### Too Little Steering (drifts off line)
```bash
--turn-gain 2.5  # Increase from 2.0
--speed 120      # Reduce to stabilize
```

### Line Not Detected
- Move sensor 1 cm higher or lower (sweet spot ~1-2 cm above paper)
- Check if IR LED brightness is sufficient (adjust potentiometer if available)
- Verify black line is solid black, not gray

---

## Data Collection

### Frame Naming
Save logs to: `tasks/ir-sensor-tracking/` (relative to the repository root)

Name format:
```
2026-08-18_Map1-IR-run-N_speed-150_gain-2.0.log
```

### What to Record
1. **Full terminal output** (copy + paste from SSH session)
2. **Any anomalies** (channels that flicker, moments line was lost)
3. **Final stats** (total time, line visible %, completion status)

---

## Success Criteria

✅ **Test passes if:**
- Phase 1: All 4 IR channels read correctly (1 on black, 0 on white)
- Phase 2: All motor movements behave as expected
- Phase 3: Car completes 80%+ of the circular path without manual intervention

❌ **Test fails if:**
- Any phase cannot be completed or shows hardware errors
- Car cannot maintain line for >30 seconds in Phase 3
- Any safety hazard detected (e.g., erratic steering into walls)

---

## Next Steps After Test

1. **If successful:** Record data, then test with camera (examples/26_cam_line_follow_drive.py)
2. **If sensor issues:** Recalibrate potentiometers, adjust sensor height
3. **If motor issues:** Check wheel alignment, NeZha I2C address conflicts
4. **If steering issues:** Tune turn_gain parameter per tuning table above

---

## References

- [IR Tracing Sensor Setup](../../docs/hardware/ir-tracing-sensor.md)
- [NeZha I2C Protocol](../../docs/hardware/nezha-i2c-protocol.md)
- [Example: Motor Check](../../examples/02_motor_check.py)
- [Example: IR Sensor Check](../../examples/36_ir_tracing_check.py)
- [Example: Motor Test](../../examples/37_map1_motor_test.py)
- [Example: IR Tracking](../../examples/39_map1_ir_line_follow.py)
