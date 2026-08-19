# IR Tracking — Sensor Model and Route Logic

## Conventions

`1 = 亮 = 黑` (LED lit, GPIO LOW, `invert={0,1,2,3}` applied).
Bit order below is **physical `P1 P2 P3 P4`, left to right along the bar** —
not channel order.

| Position | Channel | BCM GPIO | Pi pin | Offset |
|---|---|---|---|---|
| `P1` leftmost | `Out2` | 25 | Pin 22 | −3.2 cm |
| `P2` | `Out1` | 24 | Pin 18 | −0.4 cm |
| `P3` | `Out3` | 22 | Pin 15 | +0.4 cm |
| `P4` rightmost | `Out4` | 23 | Pin 16 | +3.2 cm |

Spacing `2.8 / 0.8 / 2.8 cm`, bar spans 6.4 cm, line is 2.0 cm wide.

**Blind band = gap − line width = 2.8 − 2.0 = 0.8 cm**, centred at ±1.8 cm.
**Detection limit = ±4.2 cm.**

## The 16 readings

Implemented in [`carbot.ir_geometry.STATE_TABLE`](../../src/carbot/ir_geometry.py).
A unit test asserts the noise class is *exactly* the non-contiguous readings, so
the split is a consequence of geometry rather than a hand-written list.

### A. Line-following — the only readings one 2 cm line can produce

| Reading | Line centre | Window | Meaning | L | R |
|---|---|---|---|--:|--:|
| `1000` | −4.2…−2.2 | 2.0 cm | far left | **20** | 150 |
| `0000` | −2.2…−1.4 | 0.8 cm | **left blind band — still on the line** | see below | |
| `0100` | −1.4…−0.6 | 0.8 cm | slight left | **110** | 150 |
| `0110` | −0.6…+0.6 | 1.2 cm | **centred** | 150 | 150 |
| `0010` | +0.6…+1.4 | 0.8 cm | slight right | 150 | **110** |
| `0000` | +1.4…+2.2 | 0.8 cm | **right blind band — still on the line** | see below | |
| `0001` | +2.2…+4.2 | 2.0 cm | far right | 150 | **20** |

Only **0.8 cm** of warning separates centred from blind, which is why the slight
correction is not gentle.

### B. Junction / curve — needs a second dark feature

| Reading | Meaning | Action |
|---|---|---|
| `1111` | symmetric crossbar | sustained ≥0.15 s → **roundabout entry** |
| `0111` | branch or curve on the right | sustained → exit *or* T junction (below) |
| `1110` | branch or curve on the left | steer left (medium); not on this route |
| `0011` | needs >2.8 cm of black | roundabout skew → steer right (medium) |
| `1100` | needs >2.8 cm of black | roundabout skew → steer left (medium) |

`0011` and `1100` are impossible on a straight line. They occur when the bar
passes a curve at a shallow angle, so their meaning is "skewed on the
roundabout", not "offset on a straight".

### C. Noise — non-contiguous black, one line cannot produce it

`1010`, `0101`, `1001`, `1011`, `1101` → **hold the previous command, count it.**

Causes, in order of likelihood on this build: undulating paper lifting a channel
out of range (which reads as *black*), a potentiometer drifting to the edge of
its working range, or a genuine second dark feature. These readings are a
diagnostic gauge, never a steering input — if they exceed ~5% of frames, raise
the bar or re-tune the pots.

## `0000` — resolved by history, not a timer

The line can only leave the bar past an **outer** sensor, so the previous
reading is decisive:

| Previous | Verdict | Action |
|---|---|---|
| `0010` | right blind band, still on the line | steer right, inner wheel 60 |
| `0100` | left blind band, still on the line | steer left, inner wheel 60 |
| `0001` | line has passed +4.2 cm | SEARCH |
| `1000` | line has passed −4.2 cm | SEARCH |
| `0110` | unreachable in one step | undulation → hold previous |

## Route — continuous loop, no return to the start box

Counter-clockwise. Per lap the car passes three junctions:

| Order | Where | Reading | Action |
|---|---|---|---|
| 1 | Roundabout entry (12 o'clock, perpendicular) | `1111` | creep 9.5 cm → **right 90°** |
| 2 | Roundabout exit (3 o'clock) | `0111` | creep 9.5 cm → **right 90°** |
| 3 | T junction (crossed heading east) | `0111` | **straight through** |

Junctions 2 and 3 have identical signatures — a right branch — and the map gives
no way to tell them apart from a single reading. One boolean does it:

```
1111 sustained          → in_roundabout = True,  creep → right 90°
0111 sustained + True   → exit:  in_roundabout = False, creep → right 90°
0111 sustained + False  → T junction: cross straight
```

`1111` is unambiguous and appears once per lap, so a mis-sequenced lap
**re-synchronises at the next entry** instead of staying wrong forever. This is
deliberately not a counter: a counter that slips once stays wrong.

The three outer corners (ARC 1 SE, ARC 2 NE, ARC 3 NW) are **left** curves and
are not junctions — they produce no `1111` and are followed by ordinary
steering. Together with the roundabout's 270°, roughly 43% of the route is a
left-hand curve, which is why a blanket "turn right when lost" rule was rejected.

## Timing constants

| Parameter | Value | Source |
|---|---|---|
| `speed` | 150 | verified |
| Spin rate | 40.5 °/s | measured 2026-08-18, 5-point sweep |
| Spin dead time | 0.2 s | measured 2026-08-18 |
| **90° turn** | **2.42 s** | `0.2 + 90/40.5` |
| Creep before turn | 9.5 cm | sensor sits 9.5 cm ahead of the axle |
| Forward speed | 10 cm/s | measured on the map paper |
| **Creep duration** | **0.95 s** | `9.5 / 10.0` |
| `junction_min_s` | 0.15 s | verified |

The creep exists because the sensor detects the crossbar 9.5 cm before the axle
reaches it. Turning immediately was measured on 2026-08-18 to leave the axle
short of the junction: the car pivoted onto the gap, read nothing, and spent the
rest of the run searching — 22 searches in 60 s.
