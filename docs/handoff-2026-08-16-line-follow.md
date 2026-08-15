# Handoff — 2026-08-16 Line-follow: pass to next engineer

> **Read first**: work log
> [`docs/progress/2026-08-16-line-follow.md`](progress/2026-08-16-line-follow.md)
> (today) and [`docs/progress/2026-08-15-line-follow.md`](progress/2026-08-15-line-follow.md)
> · camera [`docs/hardware/ai-camera.md`](hardware/ai-camera.md)
> · NeZha [`docs/hardware/nezha-i2c-protocol.md`](hardware/nezha-i2c-protocol.md)
> · bring-up [`docs/setup/raspberry-pi-first-run.md`](setup/raspberry-pi-first-run.md)
> · SSH [`docs/setup/mac-to-raspberry-pi-access.md`](setup/mac-to-raspberry-pi-access.md)
> · rules [`AGENTS.md`](../AGENTS.md) / [`CONVENTIONS.md`](../CONVENTIONS.md).

**Supersedes** [`docs/handoff-2026-08-15-line-follow.md`](handoff-2026-08-15-line-follow.md).
That file’s “confirm green cross then tune gain” is stale: gain, jump-hold, and
T-spin rules all changed, and **closed-loop still fails**.

The operator asked to transfer this work after watching a run that **did not
follow the planned line** (stutter, then stop). Do not defend the current
controller; replace the sensing approach if needed.

---

## 1. Goal (operator-approved)

On the printed Yahboom / 有方机器人 sheet, 2 cm black line:

1. Start **in 发车区**, chassis on the short **vertical stem**, heading toward
   the first T (not toward the poem, not on the floor tiles).
2. Drive **straight** along that stem to the T (~10 cm). The camera sees the T
   early; **do not turn at launch**.
3. When the **wheels** reach the T, **right** onto the outer loop (poem
   「少年中国说」). Left at that T is the roundabout — wrong for this plan.
4. Follow the outer loop, enter the 有方 circle from the top, **counter-clockwise**,
   take **exit 3** (right / 3 o’clock back toward the T), return down the stem
   to 发车.

Planned overlay (photo BEV, scale from 2 cm = 27 px, **not used to drive**):

`scratch/line-follow-2026-08-15/planned-route-inventory.jpg`

Generator: `scratch/line-follow-2026-08-15/draw_planned_route.py`.

Approximate lengths: stem 10 cm, outer 126 cm, roundabout arc 93 cm, return
30 cm, **total ~259 cm**. Residual warp from folds/oblique photos is several cm.

Inventory still of the same paper (发车 on the **right**):
`assets/inventory/101_Yahboom_Line_Tracking_Track_Instructions.jpg`.

---

## 2. Honest status

| Claim | Reality |
|---|---|
| Detector + nav unit tests | Pass on Mac (`tests/test_line_follow.py`, `test_line_nav.py`) |
| Overlay protocol | Green = the only steer target; cyan = other candidates; red = frame centre |
| Car follows the 2 cm route | **No** |
| First T right on hardware | **Never verified** |
| Roundabout / exit 3 | Code exists, **disabled** (`enable_roundabout=False`) |
| Metric bird’s-eye on the live camera | Module exists, **not calibrated on the Pi** |

**Last hardware (2026-08-16 ~03:10–03:24, operator at the car):**

- Speed 150, `--start-turn-s 0`, 45 s then a 20 s rerun so the operator could
  watch.
- Typical start capture from 发车: `JUNCTION`, width ~140–150 px, `err≈+0.26`,
  `x≈1280` (right of centre) — often the **box edge / near bar**, not a clean
  stem.
- Motion: ~7–8 s of `L150 R22` (hard right) mixed with `jump: stop` and brief
  deadband straight, then `no line` → **SEARCH hold `L0 R0`** until timeout.
- **No** `horizontal stroke: spin to align` in those logs.

Root cause to treat as default: **perspective line-follow on a forward, low,
off-centre camera looking at a whole A-series map.** The controller cannot tell
“stem under the wheels” from “T and poem 40 cm ahead” or “发车 box ink.” Adding
more FSM states on that detector is how we got here.

---

## 3. Hardware the next agent must not guess

- **Pi:** `ssh carpi`, user `dannypi`, repo `~/Car-and-Robotic-Arm`. Often
  **behind Mac `main`**. Copy files with `scp`; do not assume git pull is current.
- **Mac repo:** `/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm`.
- **Motors:** only with a person beside the car who can cut power. Prompt in
  `examples/26_line_follow_drive.py`. If the car is on **tiles**, do **not**
  vision-drive back onto the paper.
- **I2C:** address `0x40`, ≤200 kHz, 500 ms init / 100 ms reset. Protocol:
  `docs/hardware/nezha-i2c-protocol.md`. `vendor/` is read-only.
- **Do not power** the Pi from both NeZha 5V and USB-C.
- **Drive:** `car.drive(left, right)` differential only — **no strafe helper**.
  Forward @ 200 ≈ 0.117 m/s; @ 150 ≈ 0.088 m/s. In-place yaw @ 200 ≈ 53.5 deg/s.
- **Camera:** IMX500, 2028×1520 preview. Mounted **to the right of the axle**,
  **tilted forward and down** (not nadir). User photos (session assets):
  front `IMG_0576`, side `IMG_0578`.
- **Track:** 2 cm black line on folded white paper on tiles. 发车 is a labelled
  box; stem is short; first T is left=circle, right=outer loop.

---

## 4. Git / files (uncommitted)

Branch `main`, **not committed** (do not commit unless the user asks).

Modified:

- `src/carbot/line_follow.py` — look-ahead 2 cm lock, vertical vs horizontal
  axis, width bounds (~2 cm, max 0.10 of frame so 发车 box is not the path).
- `src/carbot/line_nav.py` — FOLLOW / SEARCH hold / optional RIGHT_TURN /
  optional ROUNDABOUT; jump-stop; far thin horizontal → drive straight; near
  fat low bar → spin right; `expected_center_fraction=0.46`.
- `examples/25_line_follow_capture.py`, `examples/26_line_follow_drive.py`
- `tests/test_line_follow.py`, `tests/test_line_nav.py`

Untracked:

- `src/carbot/ground_view.py` — floor homography → metric BEV +
  `detect_line_on_ground`
- `examples/27_ground_view_calibrate.py` — `--charuco` or `--corners`
- `tests/test_ground_view.py`

Pi copies: last intended sync was `scp` of `line_follow.py` / `line_nav.py`
into `~/Car-and-Robotic-Arm/src/carbot/` and example 26 into `examples/`.
A mistaken scp to the **repo root** was deleted; **re-scp before the next
drive.** Docs and scratch are Mac-only unless you copy them.

Scratch (Mac, gitignored): `scratch/line-follow-2026-08-15/`.
Pi captures: `/tmp/line-follow/`.

---

## 5. What the current controller will do (so you can delete it)

`detect_line` scans a look-ahead band (`lookahead_top=0.40` …
`lookahead_bottom=0.98`). It prefers a **vertical** ~2 cm stroke near centre;
if none, a **horizontal** bar. Overlay green = that choice.

`LineNav._follow_step`:

- Far / thin horizontal (`width < 70 px` or high in ROI):
  `far crossing: keep straight to T` (both wheels 150).
- Near T (width ≥ 70, low in ROI, centred) after `right_turn_after_s` (1.0 s):
  in-place right spin ~90° using `spin_deg_per_s_at_200`.
- Error jump > 0.35: stop, then SEARCH hold.
- SEARCH: **does not spin** (`search_give_up_s=0`).

This was meant to stop early T-spins. On hardware it still **never** got a
clean stem lock, so it never executed a real T-right; it yawed toward
right-side box ink and then quit.

---

## 6. Acceptance gates (do these in order)

Do **not** enable `--roundabout` or full 259 cm until gate A passes.

**Gate A — lock (no motors, or wheels lifted):** car in 发车, nose on stem.
`examples/25_line_follow_capture.py`. Green cross on the **outgoing 2 cm
stem**, width ~110–150 px, not on the box rectangle, not on the far T/poem
(18 px class). Repeat after a 5 cm roll.

**Gate B — 10 cm stem (motors, operator beside):** `--duration 8 --speed 150`.
Car stays on the stem, does not leave the paper, does not 90° spin. Overlay
sequence (`--save-every 10`) shows green staying on the stem.

**Gate C — T right:** only when the **bumper** is on the crossing (near, fat
bar). Then right onto the outer loop 2 cm line and hold it for ≥2 s.

**Gate D — outer loop then roundabout exit 3.** Separate work.

If Gate A fails twice, **stop patching `detect_line` heuristics.** Calibrate
`examples/27_ground_view_calibrate.py` (ChArUco on the paper or four floor
corners + `--size-m`) and steer in the bird’s-eye patch where 2 cm is a
constant pixel width. Live drive already accepts `--ground-view JSON`.

---

## 7. Commands

```bash
# Mac tests
cd /Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm
uv run pytest -q tests/test_line_follow.py tests/test_line_nav.py tests/test_ground_view.py

# Sync (do this; Pi tree lags)
scp src/carbot/line_follow.py src/carbot/line_nav.py src/carbot/ground_view.py \
  carpi:~/Car-and-Robotic-Arm/src/carbot/
scp examples/25_line_follow_capture.py examples/26_line_follow_drive.py \
  examples/27_ground_view_calibrate.py \
  carpi:~/Car-and-Robotic-Arm/examples/

# Pi
ssh carpi
cd ~/Car-and-Robotic-Arm
PYTHONPATH=src python3 examples/25_line_follow_capture.py --output /tmp/line-follow
# pull overlay
# scp carpi:/tmp/line-follow/line-follow-overlay.jpg ...

# motors: operator at the car
printf "yes\n" | PYTHONPATH=src python3 examples/26_line_follow_drive.py \
  --duration 8 --start-turn-s 0 --speed 150 --save-every 10 --log-dir /tmp/line-follow
```

Open-loop nudge if already **in** the box (not from tiles):
`Car().move_for(0.7, 150, 150)` ≈ 6 cm @ 150.

---

## 8. Operator protocol (they were clear)

- Do not ask them to micro-place the car every iteration. Capture, small
  forward/back yourself, then run — but **not** from off the paper.
- If a run fails: stop; if still on the line, continue from there; if on
  tiles, ask them to put it in 发车 once, then you adjust.
- Overlay: they do **not** need “everything green.” One green cross on the
  path they care about.
- No commit/push unless they ask.
- Chinese is fine for talking to them; keep docs in the repo’s usual English.

---

## 9. Suggested first hour for the incoming agent

1. Read this file and the 2026-08-16 progress log. Look at
   `planned-route-inventory.jpg` and one recent overlay in
   `scratch/line-follow-2026-08-15/` (`after-nudge-overlay.jpg`,
   `place-ok-overlay.jpg`, `go2-overlay.jpg`).
2. Re-scp sources. Capture from 发车. If green is not on the stem, **do not
   drive a 20–45 s follow.** Either calibrate ground-view or change the
   look-ahead so **near-field vertical 2 cm** wins over a map-wide horizontal.
3. Gate B only after Gate A. Tell the operator what they should see (e.g.
   “8 seconds, both wheels, no spin”) before motors run.

Do not add another timed turn, search spin, or roundabout flag to “finish the
map.” The last agent already did that class of fix; the car still wandered.
