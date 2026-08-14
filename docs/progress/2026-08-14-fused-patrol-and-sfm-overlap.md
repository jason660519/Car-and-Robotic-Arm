# Fused Patrol and the SfM Overlap Problem — Work Log (2026-08-14)

Continues
[`2026-08-14-camera-modes-exposure-and-preflight-fix.md`](2026-08-14-camera-modes-exposure-and-preflight-fix.md).
This session built the fused vision+sonar patrol the handoff asked for, ran it
on hardware three times, and used COLMAP to find out why the frames were not
reconstructing. The answer was not image quality.

## 1. Scope and Result

- **Fused patrol** — [`examples/22_fused_patrol_capture.py`](../../examples/22_fused_patrol_capture.py):
  sonar and IMX500 detections combined through `carbot.vision_avoid.fuse`,
  capture in mode `single`, back up before a random turn, `--dry-run` for a
  stationary logic test.
- **Spin rate measured, not assumed** —
  [`examples/23_spin_rate_check.py`](../../examples/23_spin_rate_check.py) with
  [`src/carbot/visual_yaw.py`](../../src/carbot/visual_yaw.py): the camera
  measures the car's own rotation by matching features across a spin, so no
  protractor and no encoders are needed (ADR 0002 ruled out measuring the robot
  by hand).
- **Capture gates** — a pose is only photographed when the sonar says the camera
  has room and `carbot.frame_quality` finds enough textured tiles.
- **Burst capture** — several overlapping frames per station instead of one.
- **Shared sonar helper** — `Sonar.measure_nearest` replaces the copy of
  `read_distance` that `examples/17` and `examples/18` each carried.

Registration across the three hardware runs:

| Run | Capture policy | Largest model | Points |
|---|---|---|---|
| 1 | one frame per station, no gates | not run (2 of 10 frames unusable) | — |
| 2 | one frame per station, gated | 3/10 (30%) | 202 |
| 3 | **burst of 5 at ~20 deg, gated** | **17/30 (57%)** | 1606 (and 3272 in a second model) |

## 2. Verification

```text
# Mac
uv run --extra vision --extra mapping pytest -q   -> 195 passed
uv run ruff check .                               -> All checks passed

# Pi: spin rate at speed 200 (14 measurements, 7 durations x 2 directions)
PYTHONPATH=src python3 examples/23_spin_rate_check.py --speed 200
  Direction: spin_left/spin_right match the chassis on all 14 trusted measurements
  Fitted: angle = 53.5 deg/s x (duration - 0.005s) at speed 200
  Previously assumed 43.9 deg/s with no dead time (measured at speed 150)

# Pi: 30-frame burst patrol, operator beside the car
PYTHONPATH=src python3 examples/22_fused_patrol_capture.py --frames 30 --frame-report
  Kept 30 frames in 10 stations (5 blocked, 5 forward, 18 rejected, 0 empty bursts)
    rejected 12x: standoff
    rejected  6x: quality

# Mac: reconstruction of those 30 frames
uv run python scripts/run_colmap_sfm.py sfm2/images sfm2/work
  model 0:  4/30 registered, 1716 points
  model 1: 17/30 registered, 1606 points
  model 2: 13/30 registered, 3272 points
```

## 3. Measurements and Configuration

**Spin rate**: 53.5 deg/s at speed 200, dead time 0.005 s. The previous
43.9 deg/s came from speed 150, so every turn the patrol commanded was about 22%
larger than intended. The dead time is negligible, which was the opposite of the
expectation that motivated measuring it — small turns need no compensation, so a
20 deg burst step is simply 0.374 s of spin.

**Motor direction**: all 14 measurements agreed with the commanded direction, so
`spin_right` really does rotate the car right and the `config.py` wheel mapping
is correct. This closes the "vendor docs and code comments disagree" hazard in
[CLAUDE.md](../../CLAUDE.md) with a measurement rather than an opinion.

**Overlap**, matched with `frame_quality.repeatable_keypoints` on run 3:

```text
within a burst (~20 deg apart):   199 - 823 matches
across a station boundary:        11, 19, 23, 25, 30, 63, 71 matches
```

Run 2, for contrast, had *no* strong links at all — its ten frames formed four
islands with 600-1500 matches inside an island and 10-40 between, which is why
COLMAP reported "no good initial image pair found" and registered only 3.

**Model membership** in run 3 shows the same boundary structure: model 2 holds
frames 0-1 and 14-24, model 1 holds 2-13 and 25-29. Each model spans roughly
three stations and then breaks, and the breaks line up with the stations where
an avoidance turn of 30-150 deg happened.

**Capture gates**: standoff 50 cm, minimum 6 of 12 textured tiles. In run 3 they
rejected 18 of 48 attempted captures (12 standoff, 6 quality) and left no
station empty. Exposure is back to `auto`.

## 4. Problems Encountered (the pitfalls)

1. **Frame quality was never the reason the sweep failed.** Run 2's frames were
   sharp, correctly exposed, and individually good; the reconstruction failed
   because consecutive frames shared nothing. Photogrammetry needs *pairs*, and
   every per-frame metric in `carbot.frame_quality` is blind to that. The
   pairwise match matrix is what diagnosed it in minutes after per-frame metrics
   had been chased for two sessions.
2. **A frame shot 30 cm from a whiteboard looks like motion blur.** Run 1
   produced frames scoring 12 and 15 sharpness with 1/12 textured tiles, which
   read as blur; the images turned out to be perfectly sharp pictures of a blank
   panel filling 70% of the frame. Looking at the image settled in seconds what
   the metrics could not.
3. **The 97 ms shutter blur risk was imaginary.** At 38 ms with a 1.0 s settle,
   captures from a moving car came back sharp, so the open question from the
   exposure sweep is closed.
4. **Spot metering does not survive a rotating camera.** The stationary sweep
   picked it, but the patrol faces every direction: two frames came back with
   12.4% and 43.3% of pixels clipped when the car turned toward a window. A
   setting tuned on a camera that never moves needs re-testing on one that does.
5. **A sign error in `visual_yaw` passed its own test**, because the synthetic
   fixture warped the image the same wrong way. Every one of the first 14 spin
   measurements was rejected as "direction disagrees with the command" while the
   underlying numbers were correct and consistent. The test now checks the sign
   against a stripe whose displacement is computed independently of the warp
   helper — a second, differently-derived source of truth.
6. **A direction disagreement should not discard a magnitude.** Rejecting those
   samples threw away a perfectly good rate measurement. Spin rate is a scalar;
   direction is a separate fact and is now reported as its own measurement.
7. **`--keep-rejected` saved nothing when standoff did all the rejecting**,
   because a standoff rejection happens before the shutter. The flag now
   captures anyway, purely to record what was skipped — that is the case where
   the threshold most needs calibrating.
8. **Rounding made a working comparison look broken**: `standoff: 50 cm < 50 cm`
   was a 49.6 cm reading printed to whole centimetres.
9. **A scratch file named `struct.py` shadows the standard library** and breaks
   `pycolmap` with a confusing circular-import trace.

## 5. Threshold Calibration Against Run 3

Run 3 is the first data set with reconstruction ground truth, so the provisional
`QualityPolicy` thresholds were checked against it. Two of the three results are
negative.

**All 30 kept frames registered.** Model membership covers every frame, so there
is no negative example in the kept set. `min_textured_tiles=6` is therefore not
too lenient: the weakest frame that passed sat exactly on the threshold (6 of 12
tiles, 738 keypoints) and still registered.

**`min_sharpness=20` was falsified by the only frame that tested it.** Frame 13
scored 19 sharpness with 925 keypoints — the softest and sparsest capture in the
set — and reconstructed normally. It was never rejected because the patrol gates
on `textured_tiles` alone; the other five thresholds are measured and printed but
not enforced. That inconsistency is now a deliberate, documented choice, and
`min_sharpness` dropped to 10 so it flags gross failure only.

**A consecutive-match threshold cannot gate connectivity.** The obvious next
gate — reject a capture that shares too few matches with the previous one — does
not work, and the data says so before it was built:

```text
same model, consecutive:      19, 30, 63, 71, 145, 199, ... 823
different model, consecutive: 11, 23, 25
lowest same-model link:  19
highest different gap:   25   -> the ranges overlap; not separable
```

A pair with 19 matches stayed in one model while pairs with 23 and 25 split.
COLMAP matches exhaustively, so a frame can join a model through a
*non-adjacent* pair: connectivity is a property of the whole match graph, not of
the link to the previous frame.

Still unanswered: whether the gates are too **strict**. Run 3 did not use
`--keep-rejected`, so its 18 rejected captures were not kept and cannot be
tested for whether they would have added usable pairs — 37% of attempted
captures were discarded on unverified thresholds.

## 6. Follow-up

**The next change is to photograph through the avoidance turn.** Bursts are now
internally connected and stations are not, and the breaks coincide with the
30-150 deg avoidance turns. That turn is currently dead time; stepping it in
~20 deg increments and capturing at each step would bridge the two headings with
exactly the kind of overlapping chain that works inside a burst. A 116 deg turn
becomes six linking frames.

Also open:

- Whether one connected model results, or whether the room needs a deliberate
  route rather than random bounce.
- A run with `--keep-rejected` to finish the calibration in section 5: are the
  gates throwing away usable captures? Worth combining with the
  photograph-through-the-turn test, since both need an operator.
- Scale is still unrecovered — the reconstruction is up to scale until the 70 mm
  wall AprilTag is used to anchor it.
- `examples/17` and `examples/18` still carry the old 43.9 deg/s constant.
