"""Tests for the IR line-nav state machine, with synthetic sensor readings.

No hardware: :class:`carbot.ir_line_nav.IRLineNav` decides from plain
:class:`~carbot.ir_line_nav.IRLineReading` values built directly (the same
pattern as ``test_line_nav.py``). Covers proportional follow, junction approach-sequence
matching, the closed-loop turn, and the line-recovery search: on a lost line the car sweeps
``search_sweep_deg`` left, sweeps back through centre to the same angle right, then creeps
forward step by step until the line is seen again.
"""

from __future__ import annotations

import pytest

from carbot.ir_line_nav import IRLineNav, IRNavPolicy, IRNavState, make_reading
from carbot.ir_route import JunctionAction, RouteJunction, RoutePlan, SequenceStep

# Raw Out1..Out4 tuples -> physical P1..P4 after to_physical (PHYSICAL_ORDER swaps 0,1).
CENTRED = (1, 0, 1, 0)  # physical 0110 — P2+P3, the only two-sensor line reading
CROSSBAR = (1, 1, 1, 1)  # physical 1111 — symmetric, the start stem / roundabout entry
GAP = (0, 0, 0, 0)  # physical 0000 — blind band, a real loss, or a T/entry approach trigger
DRIFT_RIGHT = (0, 0, 1, 0)  # physical 0010 — P3 only
DRIFT_LEFT = (1, 0, 0, 0)  # physical 0100 — P2 only (also the roundabout exit's 3rd step)
FAR_RIGHT = (0, 0, 0, 1)  # physical 0001 — P4 only
FAR_LEFT = (0, 1, 0, 0)  # physical 1000 — P1 only
RIGHT_BRANCH_0111 = (1, 0, 1, 1)  # physical 0111 — T-junction/roundabout-exit approach start
ROUNDABOUT_ENTRY_SHOULDER = (0, 1, 0, 1)  # physical 1001 — roundabout entry's middle step
ROUNDABOUT_EXIT_NOISE = (1, 0, 0, 1)  # physical 0101 — roundabout exit's 2nd step, Kind.NOISE


def default_nav(**policy_kwargs) -> IRLineNav:
    return IRLineNav(IRNavPolicy(**policy_kwargs))


# ------------------------------------------------------------- follow


def test_follow_centered_drives_straight():
    nav = default_nav()
    cmd = nav.step(make_reading(CENTRED), dt=0.01)
    assert cmd.state is IRNavState.FOLLOW
    assert cmd.left == cmd.right == 150


def test_follow_steers_toward_the_line():
    # Only P3 lit -> the line sits right of the bar centre, so the car has
    # drifted left and must steer right: slow the right wheel.
    nav = default_nav()
    cmd = nav.step(make_reading(DRIFT_RIGHT), dt=0.01)
    assert cmd.state is IRNavState.FOLLOW
    assert cmd.right < cmd.left == 150


def test_follow_steers_the_mirror_way_for_the_mirror_reading():
    nav = default_nav()
    right = nav.step(make_reading(DRIFT_RIGHT), dt=0.01)
    nav = default_nav()
    left = nav.step(make_reading(DRIFT_LEFT), dt=0.01)
    assert (right.left, right.right) == (left.right, left.left)


def test_outer_sensor_demands_a_harder_correction():
    nav = default_nav()
    slight = nav.step(make_reading(DRIFT_RIGHT), dt=0.01)
    nav = default_nav()
    hard = nav.step(make_reading(FAR_RIGHT), dt=0.01)
    assert hard.right < slight.right


def test_line_lost_enters_search_with_left_sweep():
    nav = default_nav()
    cmd = nav.step(make_reading(GAP), dt=0.1)
    assert cmd.state is IRNavState.SEARCH
    assert cmd.left == -150 and cmd.right == 150  # spinning left
    assert "sweep left" in cmd.reason


# --------------------------------------------------------- junction approach sequences
#
# 2026-08-20 third pass: every real junction produces an ORDERED sequence of readings, not
# one sustained reading. `_approach_step` tracks progress through
# `RouteJunction.approach`; only the last step completing counts as arrival.


def _single_junction_nav(junction: RouteJunction, **policy_kwargs) -> IRLineNav:
    """A nav whose only pending junction is `junction` (0cm gate), so approach-sequence
    behaviour can be checked in isolation."""
    plan = RoutePlan(prologue=(), loop=(junction,))
    return default_nav(route=plan, **policy_kwargs)


def test_approach_step_holds_while_the_first_steps_persistence_is_unmet():
    junction = RouteJunction(
        "x",
        JunctionAction.TURN_RIGHT,
        0.0,
        approach=(SequenceStep((1, 1, 1, 1), min_cm=2.0), SequenceStep((0, 0, 0, 0))),
        creep_cm=5.0,
        turn_deg=90.0,
    )
    nav = _single_junction_nav(junction)
    cmd = nav.step(make_reading(CROSSBAR), 0.1)  # 1cm < 2cm required
    assert cmd.state is IRNavState.FOLLOW
    assert cmd.left == cmd.right == 150  # held centred (no history yet -> centred default)
    assert "approaching x, step 1/2" in cmd.reason
    assert "1.00/2.00cm" in cmd.reason


def test_approach_step_does_not_steer_on_the_confirming_readings_offset():
    """The whole point of holding instead of steering: RIGHT_BRANCH_0111 has a real offset
    under STATE_TABLE, but during approach that offset must never reach the wheels."""
    junction = RouteJunction(
        "x", JunctionAction.TURN_RIGHT, 0.0,
        approach=(SequenceStep((0, 1, 1, 1), min_cm=2.0), SequenceStep((0, 1, 1, 0))),
        creep_cm=5.0, turn_deg=90.0,
    )
    nav = _single_junction_nav(junction)
    nav.step(make_reading(CENTRED), 0.01)  # steady last-good command
    cmd = nav.step(make_reading(RIGHT_BRANCH_0111), 0.1)  # 1cm < 2cm required
    assert cmd.left == cmd.right == 150
    assert "holding previous" in cmd.reason


def test_approach_step_advances_past_a_satisfied_step():
    junction = RouteJunction(
        "x", JunctionAction.TURN_RIGHT, 0.0,
        approach=(SequenceStep((1, 1, 1, 1), min_cm=1.0), SequenceStep((0, 0, 0, 0))),
        creep_cm=5.0, turn_deg=90.0,
    )
    nav = _single_junction_nav(junction)
    # 1cm satisfies step 1's min_cm on this very call, which advances immediately -- the
    # returned reason already reflects step 2, not step 1.
    cmd = nav.step(make_reading(CROSSBAR), 0.1)
    assert "step 2/2" in cmd.reason


def test_approach_step_completes_and_commits_a_turn():
    junction = RouteJunction(
        "x", JunctionAction.TURN_RIGHT, 0.0,
        approach=(SequenceStep((1, 1, 1, 1), min_cm=1.0), SequenceStep((0, 0, 0, 0))),
        creep_cm=5.0, turn_deg=90.0,
    )
    nav = _single_junction_nav(junction)
    nav.step(make_reading(CROSSBAR), 0.1)  # step 1 satisfied
    cmd = nav.step(make_reading(GAP), 0.1)  # step 2 (0000) -> arrival
    assert cmd.state is IRNavState.JUNCTION_CREEP
    assert nav.last_junction == "x"


def test_a_reading_matching_neither_step_resets_and_falls_through():
    """A stray frame that matches neither the tracked step nor the next one resets progress
    to step 0 and is handled as ordinary FOLLOW (not held as noise)."""
    junction = RouteJunction(
        "x", JunctionAction.TURN_RIGHT, 0.0,
        approach=(SequenceStep((1, 1, 1, 1), min_cm=1.0), SequenceStep((0, 0, 0, 0))),
        creep_cm=5.0, turn_deg=90.0,
    )
    nav = _single_junction_nav(junction)
    nav.step(make_reading(CROSSBAR), 0.1)  # step 1 satisfied -> now tracking step 2 (0000)
    cmd = nav.step(make_reading(CENTRED), 0.1)  # unrelated: ordinary centred line
    assert cmd.state is IRNavState.FOLLOW
    assert cmd.reason == "centred"
    # And the sequence really did reset: CROSSBAR again must re-satisfy step 1 from scratch.
    cmd = nav.step(make_reading(CROSSBAR), 0.5)  # comfortably >= 1cm
    assert "step 2/2" in cmd.reason


def test_a_skewed_approach_reading_before_the_first_step_still_steers():
    """2026-08-20 real-track observation: 0111/1110 commonly appear just BEFORE a symmetric
    1111 (and 0001/1000 just before the post-crossbar 0000) as the car approaches a real
    crossbar from a skewed angle -- an ordinary, expected transitional reading, not noise.
    Before any approach progress has been made (index still 0) it must keep steering on it,
    same as any other curve -- see test_a_gated_out_junction_still_steers_toward_the_line for
    the 2026-08-19 regression this preserves."""
    junction = RouteJunction(
        "x", JunctionAction.TURN_RIGHT, 0.0,
        approach=(SequenceStep((1, 1, 1, 1), min_cm=2.0), SequenceStep((0, 0, 0, 0))),
        creep_cm=5.0, turn_deg=90.0,
    )
    nav = _single_junction_nav(junction)
    # 1110 ("branch or curve on the left") is Kind.JUNCTION but not this junction's step 0 --
    # no approach progress has been made yet, so it must still steer.
    cmd = nav.step(make_reading((1, 1, 1, 0)), 0.1)
    assert cmd.state is IRNavState.FOLLOW
    assert cmd.left < cmd.right  # "branch or curve on the left" steers left: right wheel faster


def test_a_junction_shaped_reading_that_breaks_a_started_sequence_holds():
    """Unlike the skewed-approach case above, a reading that interrupts a sequence already
    partway matched is close to a real junction and about to commit to an action -- hold
    instead of steering hard on an offset that risks throwing off an approach already mostly
    confirmed (2026-08-20 real-track regression, distinct from the case above)."""
    junction = RouteJunction(
        "x", JunctionAction.TURN_RIGHT, 0.0,
        approach=(SequenceStep((1, 1, 1, 1), min_cm=2.0), SequenceStep((0, 0, 0, 0))),
        creep_cm=5.0, turn_deg=90.0,
    )
    nav = _single_junction_nav(junction)
    nav.step(make_reading(CROSSBAR), 0.1)  # step 0 (1111) partway satisfied: index/cm > 0
    # An unrelated junction-shaped reading now breaks the in-progress sequence.
    cmd = nav.step(make_reading((1, 1, 1, 0)), 0.1)
    assert cmd.state is IRNavState.FOLLOW
    assert cmd.left == cmd.right  # held, not steered left on the -1.6cm offset
    assert "broke x's approach mid-sequence" in cmd.reason


def test_roundabout_entry_shoulder_1001_is_part_of_the_sequence_not_noise():
    """1001 is Kind.NOISE under carbot.ir_geometry, but as the roundabout entry's own 2nd
    approach step it must advance the sequence, not get held as generic noise."""
    junction = RouteJunction(
        "roundabout entry", JunctionAction.TURN_RIGHT, 0.0,
        approach=(
            SequenceStep((1, 1, 1, 1), min_cm=1.0),
            SequenceStep((1, 0, 0, 1), min_cm=0.1),
            SequenceStep((0, 0, 0, 0)),
        ),
        creep_cm=8.0, turn_deg=42.5,
    )
    nav = _single_junction_nav(junction)
    nav.step(make_reading(CROSSBAR), 0.1)  # step 1
    cmd = nav.step(make_reading(ROUNDABOUT_ENTRY_SHOULDER), 0.2)  # step 2, 2cm >= 0.1cm
    assert "step 3/3" in cmd.reason
    cmd = nav.step(make_reading(GAP), 0.1)  # step 3 -> arrival
    assert cmd.state is IRNavState.JUNCTION_CREEP


def test_roundabout_exit_four_step_sweep_including_noise_classified_reading():
    """0101 is Kind.NOISE, 0100/0110 are ordinary DRIFT/ON_LINE -- none look like a junction
    in isolation, only the order matters."""
    junction = RouteJunction(
        "roundabout exit", JunctionAction.TURN_RIGHT, 0.0,
        approach=(
            SequenceStep((0, 1, 1, 1)),
            SequenceStep((0, 1, 0, 1)),
            SequenceStep((0, 1, 0, 0)),
            SequenceStep((0, 1, 1, 0)),
        ),
        creep_cm=6.5, turn_deg=90.0,
    )
    nav = _single_junction_nav(junction)
    nav.step(make_reading(RIGHT_BRANCH_0111), 0.1)
    nav.step(make_reading(ROUNDABOUT_EXIT_NOISE), 0.1)
    nav.step(make_reading(DRIFT_LEFT), 0.1)
    cmd = nav.step(make_reading(CENTRED), 0.1)  # 0110 -> arrival
    assert cmd.state is IRNavState.JUNCTION_CREEP
    assert nav.last_junction == "roundabout exit"


def test_cross_action_needs_no_creep_or_turn():
    """(g) Reaching the last approach step IS arrival -- no JUNCTION_CREEP/JUNCTION_TURN."""
    junction = RouteJunction(
        "T junction", JunctionAction.CROSS, 0.0,
        approach=(SequenceStep((0, 1, 1, 1), min_cm=1.0), SequenceStep((0, 1, 1, 0))),
    )
    nav = _single_junction_nav(junction)
    nav.step(make_reading(RIGHT_BRANCH_0111), 0.2)  # satisfies 1cm
    cmd = nav.step(make_reading(CENTRED), 0.1)  # 0110 -> CROSS fires immediately
    assert cmd.state is IRNavState.FOLLOW
    assert cmd.left == cmd.right
    assert "crossing T junction straight through" in cmd.reason


def test_stop_action_halts_the_wheels():
    junction = RouteJunction(
        "final T junction", JunctionAction.STOP, 0.0,
        approach=(SequenceStep((0, 1, 1, 1), min_cm=1.0), SequenceStep((0, 1, 1, 0))),
    )
    nav = _single_junction_nav(junction)
    nav.step(make_reading(RIGHT_BRANCH_0111), 0.2)
    cmd = nav.step(make_reading(CENTRED), 0.1)
    assert cmd.state is IRNavState.STOPPED
    assert cmd.left == cmd.right == 0


# ------------------------------------------------------------- creep + closed-loop turn


def _turning_junction(creep_cm=4.0, turn_deg=90.0) -> RouteJunction:
    return RouteJunction(
        "x", JunctionAction.TURN_RIGHT, 0.0,
        approach=(SequenceStep((1, 1, 1, 1), min_cm=0.0),),
        creep_cm=creep_cm, turn_deg=turn_deg,
    )


def test_junction_commits_creep_then_closed_loop_turn():
    nav = _single_junction_nav(_turning_junction(creep_cm=4.0))  # 4cm @ 10cm/s = 0.4s
    cmd = nav.step(make_reading(CROSSBAR), 0.1)  # approach completes on the very first frame
    assert cmd.state is IRNavState.JUNCTION_CREEP
    assert cmd.left == cmd.right == 150
    cmd = nav.step(make_reading(CROSSBAR), 0.5)  # 0.5s >= 0.4 -> pivot
    assert cmd.state is IRNavState.JUNCTION_TURN
    assert cmd.left > 0 and cmd.right < 0  # default right turn
    assert "watching for 0110" in cmd.reason
    cmd = nav.step(make_reading(CENTRED), 3.0)  # 0110 reached -> turn ends
    assert cmd.state is IRNavState.FOLLOW
    assert cmd.left == cmd.right == 150
    assert "line reacquired (0110)" in cmd.reason


def test_turn_ignores_readings_other_than_0110():
    """Mid-turn, the crossbar itself and other transitional readings must not end the turn --
    only TURN_COMPLETE_READING (0110) does."""
    nav = _single_junction_nav(_turning_junction(creep_cm=1.0))
    nav.step(make_reading(CROSSBAR), 0.1)  # arrival
    nav.step(make_reading(CROSSBAR), 0.2)  # creep done -> JUNCTION_TURN
    for reading in (CROSSBAR, RIGHT_BRANCH_0111, ROUNDABOUT_EXIT_NOISE, DRIFT_LEFT, FAR_LEFT):
        cmd = nav.step(make_reading(reading), 0.1)
        assert cmd.state is IRNavState.JUNCTION_TURN
    cmd = nav.step(make_reading(CENTRED), 0.1)  # only 0110 ends it
    assert cmd.state is IRNavState.FOLLOW


def test_turn_requires_the_minimum_spin_dead_time_before_trusting_0110():
    """A 0110 in the very first instant (e.g. residual alignment right as the pivot starts)
    must not be trusted -- spin_dead_time_s is the same "motor hasn't really moved yet"
    floor the spin calibration itself uses."""
    nav = _single_junction_nav(
        _turning_junction(creep_cm=1.0), spin_dead_time_s=0.5, spin_rate_deg_per_s=42.0
    )
    nav.step(make_reading(CROSSBAR), 0.1)
    nav.step(make_reading(CROSSBAR), 0.2)  # -> JUNCTION_TURN
    cmd = nav.step(make_reading(CENTRED), 0.1)  # 0110 immediately, but < 0.5s dead time
    assert cmd.state is IRNavState.JUNCTION_TURN
    cmd = nav.step(make_reading(CENTRED), 0.5)  # now past dead time, still reading 0110
    assert cmd.state is IRNavState.FOLLOW


def test_turn_times_out_if_0110_never_returns():
    """A chassis fault or misalignment that never reproduces 0110 must not spin forever."""
    nav = _single_junction_nav(
        _turning_junction(creep_cm=1.0, turn_deg=90.0),
        spin_rate_deg_per_s=42.0,
        spin_dead_time_s=0.41,
        turn_timeout_scale=2.0,
    )
    nav.step(make_reading(CROSSBAR), 0.1)
    nav.step(make_reading(CROSSBAR), 0.2)  # -> JUNCTION_TURN
    timeout_s = nav.policy.turn_timeout_s(90.0)
    cmd = nav.step(make_reading(FAR_LEFT), timeout_s + 1.0)  # never reads 0110
    assert cmd.state is IRNavState.FOLLOW
    assert "timeout" in cmd.reason
    assert "0110 never seen" in cmd.reason


def test_creep_duration_is_the_junctions_own_creep_cm_over_speed():
    nav = _single_junction_nav(_turning_junction(creep_cm=9.5))
    cmd = nav.step(make_reading(CROSSBAR), 0.1)
    assert cmd.state is IRNavState.JUNCTION_CREEP
    cmd = nav.step(make_reading(CROSSBAR), 0.9)  # 0.9s < 0.95s -> still creeping
    assert cmd.state is IRNavState.JUNCTION_CREEP
    assert "creeping 9.5cm" in cmd.reason
    cmd = nav.step(make_reading(CROSSBAR), 0.1)  # 1.0s >= 0.95s -> pivot
    assert cmd.state is IRNavState.JUNCTION_TURN


def test_turn_timeout_scales_with_expected_angle():
    policy = IRNavPolicy(spin_rate_deg_per_s=42.0, spin_dead_time_s=0.41, turn_timeout_scale=2.0)
    assert policy.turn_timeout_s(90.0) == pytest.approx(2.0 * (0.41 + 90.0 / 42.0))
    assert policy.turn_timeout_s(42.5) == pytest.approx(2.0 * (0.41 + 42.5 / 42.0))


def test_post_turn_0000_starts_a_search_not_a_stale_pre_turn_blind_band():
    """The turn's real angle is not otherwise verified, so a 0000 right after landing must
    not be resolved with the line position from before the turn: that geometry belongs to
    the old heading and says nothing about where the line is on the new one."""
    nav = _single_junction_nav(_turning_junction(creep_cm=1.0))
    # DRIFT_RIGHT is in ir_geometry.BLIND_AFTER_RIGHT -- if this survived the turn, the
    # post-turn 0000 below would be misread as "blind band, keep going" instead of "lost".
    nav.step(make_reading(DRIFT_RIGHT), 0.01)
    nav.step(make_reading(CROSSBAR), 0.1)
    nav.step(make_reading(CROSSBAR), 0.2)  # -> JUNCTION_TURN
    cmd = nav.step(make_reading(CENTRED), 5.0)  # 0110 -> turn done
    assert cmd.state is IRNavState.FOLLOW
    cmd = nav.step(make_reading(GAP), dt=0.1)  # 0000 immediately after landing
    assert cmd.state is IRNavState.SEARCH
    assert "sweep left" in cmd.reason


def test_line_lost_after_junction_turn_enters_search():
    """The reported failure: after the T-junction the car faces the ~2.4cm
    gap between the sensor pairs and reads nothing — it must search, not stop."""
    nav = _single_junction_nav(_turning_junction(creep_cm=1.0))
    nav.step(make_reading(CROSSBAR), 0.1)
    nav.step(make_reading(CROSSBAR), 0.2)  # -> JUNCTION_TURN
    cmd = nav.step(make_reading(CENTRED), 5.0)  # 0110 -> turn done
    assert cmd.state is IRNavState.FOLLOW
    cmd = nav.step(make_reading(GAP), dt=0.1)  # gap under the bar
    assert cmd.state is IRNavState.SEARCH
    assert cmd.left < 0 < cmd.right


def test_a_pivot_does_not_count_toward_the_next_gate():
    """A spin covers no ground, so feeding it to the odometer would open the gate early."""
    nav = _single_junction_nav(_turning_junction(creep_cm=1.0))
    nav.step(make_reading(CROSSBAR), 0.1)
    nav.step(make_reading(CROSSBAR), 0.2)  # -> JUNCTION_TURN
    before = nav.junctions.cm_since_previous
    while nav.state is IRNavState.JUNCTION_TURN:
        nav.step(make_reading(FAR_LEFT), 0.01)
    assert nav.junctions.cm_since_previous == pytest.approx(before)


# ------------------------------------------------------------- search


def test_search_sweeps_left_then_right_then_creeps():
    """Full phase sequence with the calibrated spin model (10 deg sweep =
    0.41 + 10/42.0 = 0.648s; right sweep is 2x the angle = 0.886s)."""
    nav = default_nav()
    gap = make_reading(GAP)
    cmd = nav.step(gap, 0.1)
    assert "sweep left" in cmd.reason
    cmd = nav.step(gap, 0.7)  # left sweep done (0.8s total) -> sweep right
    assert cmd.left == 150 and cmd.right == -150
    assert "sweep right" in cmd.reason
    cmd = nav.step(gap, 1.0)  # right sweep done -> creep
    assert cmd.left == cmd.right == 75  # 150 * search_creep_speed_ratio 0.5
    assert "creep step 1/4" in cmd.reason


def test_search_creep_steps_then_restarts_sweep_cycle():
    nav = default_nav(search_creep_steps_per_cycle=2)
    gap = make_reading(GAP)
    nav.step(gap, 0.5)  # enters search (transition consumes no search time)
    nav.step(gap, 0.7)  # finishes left sweep (0.648s) -> sweep right
    nav.step(gap, 1.0)  # finishes right sweep (0.886s) -> creep step 1/2
    cmd = nav.step(gap, 0.3)  # creep step 1 done -> creep step 2/2
    assert "creep step 2/2" in cmd.reason
    cmd = nav.step(gap, 0.3)  # step 2 done -> new sweep cycle from here
    assert "sweep left" in cmd.reason
    assert cmd.state is IRNavState.SEARCH


def test_search_reacquires_line_and_resumes_follow():
    nav = default_nav()
    nav.step(make_reading(GAP), 0.1)  # into search
    cmd = nav.step(make_reading(CENTRED), 0.1)  # line back under bar
    assert cmd.state is IRNavState.FOLLOW
    assert cmd.left == cmd.right == 150  # centred: straight, no correction


def test_search_reacquired_junction_approach_is_still_tracked():
    """Reacquiring the line as the pending junction's first approach reading must be treated
    as the start of that sequence, not just plain follow — the search delegates back to
    follow, which runs _approach_step first."""
    junction = RouteJunction(
        "x", JunctionAction.TURN_RIGHT, 0.0,
        approach=(SequenceStep((1, 1, 1, 1), min_cm=5.0), SequenceStep((0, 0, 0, 0))),
        creep_cm=1.0, turn_deg=90.0,
    )
    nav = _single_junction_nav(junction)
    nav.step(make_reading(GAP), 0.1)  # into search
    cmd = nav.step(make_reading(CROSSBAR), 0.1)  # reacquired as the approach's first step
    assert cmd.state is IRNavState.FOLLOW
    assert "approaching x, step 1/2" in cmd.reason


def test_search_gives_up_and_stops():
    nav = default_nav(search_give_up_s=1.0)
    gap = make_reading(GAP)
    nav.step(gap, 0.5)  # enters search (transition itself takes no search time)
    nav.step(gap, 0.5)  # finishes left sweep -> sweep right
    cmd = nav.step(gap, 0.5)  # 1.0s of searching >= give-up -> stop
    assert cmd.left == cmd.right == 0
    assert cmd.state is IRNavState.SEARCH
    assert "give up" in cmd.reason


def test_search_zero_give_up_never_stops():
    nav = default_nav(search_give_up_s=0.0)
    gap = make_reading(GAP)
    for _ in range(50):
        cmd = nav.step(gap, 0.5)
        assert cmd.state is IRNavState.SEARCH
    assert not (cmd.left == cmd.right == 0)


# ------------------------------------------------------------- policy


@pytest.mark.parametrize(
    "kwargs",
    [
        {"speed": -1},
        {"speed": 1001},
        {"turn_gain": 0.0},
        {"deadband": 1.0},
        {"turn_direction": 0},
        {"spin_rate_deg_per_s": 0.0},
        {"spin_dead_time_s": -1.0},
        {"turn_timeout_scale": 0.0},
        {"forward_speed_cm_per_s": 0.0},
        {"search_sweep_deg": -1.0},
        {"search_creep_step_s": -0.1},
        {"search_creep_speed_ratio": 0.0},
        {"search_creep_speed_ratio": 1.5},
        {"search_creep_steps_per_cycle": 0},
        {"search_give_up_s": -1.0},
    ],
)
def test_invalid_policy_rejected(kwargs):
    with pytest.raises(ValueError):
        IRNavPolicy(**kwargs)


def test_sweep_duration_uses_calibrated_spin_model():
    policy = IRNavPolicy()
    # 0.41s dead time + 10 deg / 42.0 deg/s
    assert policy.sweep_duration(10.0) == pytest.approx(0.41 + 10.0 / 42.0)
    assert policy.sweep_duration(20.0) == pytest.approx(0.41 + 20.0 / 42.0)


# ------------------------------------------------- route-driven junctions (integration)
#
# End-to-end with the real TASK1_ROUTE data, not a synthetic minimal junction.

RIGHT_BRANCH = RIGHT_BRANCH_0111  # physical 0111 — the roundabout exit and the T junction


def _drive(nav: IRLineNav, channels, seconds: float, dt: float = 0.01):
    """Hold one reading for a while, returning every command produced."""
    return [nav.step(make_reading(channels), dt) for _ in range(int(seconds / dt))]


def _settle(nav: IRLineNav):
    """Run the creep and pivot out to completion (or a STOP action's halt)."""
    for _ in range(4000):
        if nav.state in (IRNavState.FOLLOW, IRNavState.STOPPED):
            return
        nav.step(make_reading(CENTRED), 0.01)
    raise AssertionError("junction never finished")


def _reach_next_junction(nav: IRLineNav) -> None:
    """Drive far enough to clear the next distance gate, then walk its real approach
    sequence to completion (always feeding whatever step `_approach_index` is currently
    tracking, so persistence requirements are satisfied step by step in order), then settle
    out any creep/turn."""
    gate = nav.junctions.pending.min_cm_since_previous
    seconds = gate / nav.policy.forward_speed_cm_per_s + 1.0
    for _ in range(int(seconds / 0.01) + 10):
        if nav.state is IRNavState.STOPPED:
            return
        nav.step(make_reading(CENTRED), dt=0.01)
    approach = nav.junctions.pending.approach
    seen_before = nav.junctions_seen
    for _ in range(4000):
        if nav.junctions_seen > seen_before or nav.state is IRNavState.STOPPED:
            break
        raw = _raw_for(approach[nav._approach_index].bits)
        nav.step(make_reading(raw), dt=0.01)
    else:
        raise AssertionError("approach sequence never completed")
    _settle(nav)


def _raw_for(physical: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """Invert to_physical's PHYSICAL_ORDER swap (0<->1) to get a raw Out-order tuple that
    decodes to `physical`."""
    p1, p2, p3, p4 = physical
    return (p2, p1, p3, p4)


def test_first_junction_out_of_the_start_box_turns_right():
    nav = default_nav()
    _reach_next_junction(nav)
    assert nav.last_junction == "start stem T junction"
    assert nav.junctions_seen == 1


def test_the_returning_t_junction_is_crossed_not_turned():
    nav = default_nav()
    for _ in range(3):  # prologue T, roundabout entry, roundabout exit
        _reach_next_junction(nav)
    assert nav.last_junction == "roundabout exit"
    assert nav.state is IRNavState.FOLLOW
    _reach_next_junction(nav)  # the lap-crossing T: CROSS, no pivot
    assert nav.last_junction == "T junction"
    assert nav.state is IRNavState.FOLLOW


def test_a_junction_read_again_immediately_is_rejected():
    """After the start-stem T, immediately walking the roundabout entry's full approach
    sequence (without covering its 60cm gate) must be rejected, not accepted."""
    nav = default_nav()
    _reach_next_junction(nav)  # start stem T, accepted
    assert nav.last_junction == "start stem T junction"
    approach = nav.junctions.pending.approach  # roundabout entry's sequence, too soon
    cmd = None
    for _ in range(2000):
        raw = _raw_for(approach[nav._approach_index].bits)
        cmd = nav.step(make_reading(raw), dt=0.01)
        if nav.junctions_rejected > 0:
            break
    assert nav.junctions_rejected > 0
    assert nav.junctions_seen == 1
    assert cmd.left == cmd.right
    assert "short of the" in cmd.reason


def test_a_stop_junction_halts_the_wheels():
    from carbot.ir_route import task1_route_for_laps

    nav = default_nav(route=task1_route_for_laps(1))
    for _ in range(4):
        _reach_next_junction(nav)
    assert nav.state is IRNavState.STOPPED
    assert nav.last_junction == "final T junction"


def test_the_stop_is_latched_against_further_readings():
    from carbot.ir_route import task1_route_for_laps

    nav = default_nav(route=task1_route_for_laps(1))
    for _ in range(4):
        _reach_next_junction(nav)
    assert nav.state is IRNavState.STOPPED
    for reading in (CENTRED, CROSSBAR, DRIFT_RIGHT, GAP):
        cmd = nav.step(make_reading(reading), dt=0.01)
        assert cmd.left == 0 and cmd.right == 0
        assert cmd.state is IRNavState.STOPPED


# ------------------------------------------------- gate rejection keeps steering

SKEW_LEFT = (1, 1, 0, 0)  # physical 1100 — left pair, a curve read at a shallow angle
SKEW_RIGHT = (0, 0, 1, 1)  # physical 0011 — right pair


def _gated_directional_nav() -> IRLineNav:
    """A nav whose only junction has a 60cm gate and an approach that completes in a single,
    directional reading -- isolates the gate-rejection path (which must keep steering, see
    the 2026-08-19 regression below) from the mid-sequence-interrupt path above (which must
    not, since none of the real Task-1 junctions' final steps carry directional offset:
    0000/0110 both resolve to direction 0)."""
    junction = RouteJunction("x", JunctionAction.TURN_RIGHT, 60.0, approach=(SequenceStep(SKEW_LEFT),))
    return _single_junction_nav(junction)


def test_a_gated_out_junction_still_steers_toward_the_line():
    """Regression: holding straight here drove the car off the paper on 2026-08-19.

    The gate rejecting a reading means "not the junction the route wants", not "ignore
    where the line is" — the approach sequence completing early still has to be steered on
    if the gate then rejects it.
    """
    nav = _gated_directional_nav()
    cmd = nav.step(make_reading(SKEW_LEFT), 0.01)  # completes the approach; gate rejects it
    assert nav.junctions_rejected > 0
    assert cmd.left < cmd.right, "1100 means the line is left; the left wheel must slow"


def test_a_gated_out_junction_steers_the_other_way_too():
    junction = RouteJunction("x", JunctionAction.TURN_RIGHT, 60.0, approach=(SequenceStep(SKEW_RIGHT),))
    nav = _single_junction_nav(junction)
    cmd = nav.step(make_reading(SKEW_RIGHT), 0.01)
    assert nav.junctions_rejected > 0
    assert cmd.right < cmd.left, "0011 means the line is right; the right wheel must slow"


def test_a_gated_out_junction_does_not_advance_the_route():
    nav = _gated_directional_nav()
    pending_before = nav.junctions.pending.name
    nav.step(make_reading(SKEW_LEFT), 0.01)
    assert nav.junctions.pending.name == pending_before
    assert nav.junctions_seen == 0
    assert nav.junctions_rejected > 0
