# 2026-08-16 — Line-follow on Yahboom paper: BEV plan, camera geometry, still not on-route

## Scope and result

Continued supervised line-follow on the Yahboom / 有方机器人 paper (2 cm black
line). The **agreed route** is: 发车 → stem to first T → **right** onto the
outer loop (poem) → roundabout **counter-clockwise, exit 3** → back to 发车.

**Result:** topology of the paper is understood and drawn. Closed-loop driving
still does **not** follow that route. The last two supervised runs (45 s then
20 s @ speed 150) moved for ~7–8 s with stuttering steer/stop, then held still
on `search: hold`. No verified 90° T-turn. Operator described the motion as
wandering.

Intentionally not committed (user did not ask).

## Verification

```text
# Mac
uv run pytest -q tests/test_line_follow.py tests/test_line_nav.py tests/test_ground_view.py
  # 65+ tests in line_follow/nav; ground_view tests exist if the extra is installed

# Pi (operator beside the car)
PYTHONPATH=src python3 examples/25_line_follow_capture.py --output /tmp/line-follow
printf "yes\n" | PYTHONPATH=src python3 examples/26_line_follow_drive.py \
  --duration 20 --start-turn-s 0 --speed 150
```

Operator-observed (2026-08-16 ~03:10–03:20): car in 发车 box, then ~6–8 s of
lurching (strong right-wheel cut, jump-stops), then motionless until the script
ended. Not a clean stem follow and not a T-right.

## Measurements and configuration

| Item | Value | Notes |
|---|---|---|
| Line width | 2 cm | User-confirmed |
| Stem 2 cm width on inventory BEV | ~27 px | `scratch/line-follow-2026-08-15/` |
| Scale from that width | 13.5 px/cm | Photo BEV, folds remain |
| Planned path length | ~259 cm | stem ~10, outer ~126, roundabout ~93, return ~30 |
| Travel @ speed 200 / 150 | 0.117 m/s / ~0.088 m/s | existing calibration |
| Spin @ speed 200 | 53.5 deg/s | examples/23 |
| Fixed exposure | 50 ms, gain 4.5 | examples/25 and 26 |
| Capture size | 2028×1520 | IMX500 preview |
| Near 2 cm width in camera | ~110–150 px | start-zone stills |
| Far T / poem bar | ~18 px, often `err=0` at x=1014 | forward-tilted camera |
| Camera mount | **right of axle**, tilted **forward/down** | user photos IMG_0576, IMG_0578 |
| `expected_center_fraction` | 0.46 | not 0.5; unmeasured offset |
| `t_bar_min_width_px` | 70 | far bars must not spin |
| SEARCH | hold still (`L0 R0`) | spin-search walked off paper |
| Roundabout FSM | **off** (`--roundabout` not set) | |

Scratch (Mac, not committed):
`scratch/line-follow-2026-08-15/` — overlays, BEV maps,
`planned-route-inventory.jpg`, `draw_planned_route.py`.

Paper topology (发车 at **bottom** of rotated BEV): stem **up** to T; **right**
= outer rounded rectangle (poem); **left** = 有方 circle. Inventory photo
`assets/inventory/101_Yahboom_Line_Tracking_Track_Instructions.jpg` is the same
map rotated ~90° (发车 on the **right**).

## Problems encountered

1. **Forward camera sees the whole map.** From 发车 the T and poem appear as a
   horizontal bar. Early code treated that as “arrived at T” and spun or drove
   off the top of the paper. Timed 90° rights were rejected by the operator.
2. **Detector lock is not unique.** 发车 box edges, stem, far T, and chairs all
   produce 2 cm-scale dark strips. Overlay: **one green cross** is the steer
   target; cyan = other candidates. Green was often on a box edge or far bar,
   not the stem under the wheels.
3. **Jump-stop.** `max_error_jump=0.35` stops on lock flips. Combined with
   multi-branch 发车 views, the car stutters then loses the line and holds.
4. **Do not drive back from tiles.** Off-paper views lock chairs/grout. Operator
   must place the car in 发车; a 0.7 s @ 150 open-loop nudge (~6 cm) was used
   once from inside the box.
5. **Ground-view homography** (`src/carbot/ground_view.py`, example 27) was
   written and unit-tested but **never calibrated on the robot** (no
   `/tmp/line-follow/ground-view.json` on the Pi). Phone BEV of the paper is
   planning only, not the live controller.

## Follow-up

See [`docs/handoff-2026-08-16-line-follow.md`](../handoff-2026-08-16-line-follow.md).
The next owner should assume closed-loop follow is **not** working and should
not add more route states until the green cross stays on the stem while the
chassis moves ~10 cm on paper.
