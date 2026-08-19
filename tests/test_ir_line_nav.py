"""Tests for the IR line-nav state machine, with synthetic sensor readings.

No hardware: :class:`carbot.ir_line_nav.IRLineNav` decides from plain
:class:`~carbot.ir_line_nav.IRLineReading` values built directly (the same
pattern as ``test_line_nav.py``). Covers proportional follow, the scripted
junction creep+turn, and the line-recovery search: on a lost line the car
sweeps ``search_sweep_deg`` left, sweeps back through centre to the same
angle right, then creeps forward step by step until the line is seen again.
"""

from __future__ import annotations

import pytest

from carbot.ir_line_nav import IRLineNav, IRNavPolicy, IRNavState, make_reading

CENTRED = (1, 0, 1, 0)  # physical 0110 — P2+P3, the only two-sensor line reading
CROSSBAR = (1, 1, 1, 1)  # physical 1111 — symmetric, the roundabout entry
GAP = (0, 0, 0, 0)  # physical 0000 — blind band or a real loss
DRIFT_RIGHT = (0, 0, 1, 0)  # physical 0010 — P3 only
DRIFT_LEFT = (1, 0, 0, 0)  # physical 0100 — P2 only
FAR_RIGHT = (0, 0, 0, 1)  # physical 0001 — P4 only
FAR_LEFT = (0, 1, 0, 0)  # physical 1000 — P1 only


def default_nav(**policy_kwargs) -> IRLineNav:
    return IRLineNav(IRNavPolicy(**policy_kwargs))


# ------------------------------------------------------------- follow


def test_follow_centered_drives_straight():
    nav = default_nav()
    cmd = nav.step(make_reading(CROSSBAR), dt=0.01)
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


def test_post_turn_0000_starts_a_search_not_a_stale_pre_turn_blind_band():
    """The pivot is timed, not angle-verified (85-93 deg measured on the real track, not a
    clean 90), so a 0000 right after landing is common. The line position from before the
    turn belongs to the old heading and must not decide whether this is the "blind band":
    that only makes sense while still on the same line the reading was taken from."""
    nav = default_nav(junction_min_s=0.05, creep_before_turn_cm=1.0)  # 1cm @ 10cm/s = 0.1s
    # DRIFT_RIGHT is in ir_geometry.BLIND_AFTER_RIGHT -- if this survived the turn, the
    # post-turn 0000 below would be misread as "blind band, keep going" instead of "lost".
    nav.step(make_reading(DRIFT_RIGHT), 0.01)
    on_line = make_reading(CROSSBAR)
    nav.step(on_line, 0.1)  # junction confirmed -> JUNCTION_CREEP
    nav.step(on_line, 0.2)  # creep done -> JUNCTION_TURN
    cmd = nav.step(on_line, 5.0)  # nominal turn time done -> FOLLOW
    assert cmd.state is IRNavState.FOLLOW
    cmd = nav.step(make_reading(GAP), dt=0.1)  # 0000 immediately after landing
    assert cmd.state is IRNavState.SEARCH
    assert "sweep left" in cmd.reason


def test_line_lost_after_junction_turn_enters_search():
    """The reported failure: after the T-junction the car faces the ~2.4cm
    gap between the sensor pairs and reads nothing — it must search, not stop."""
    nav = default_nav(junction_min_s=0.05, creep_before_turn_cm=1.0)  # 1cm @ 10cm/s = 0.1s
    on_line = make_reading(CROSSBAR)
    nav.step(on_line, 0.1)  # junction confirmed -> JUNCTION_CREEP
    nav.step(on_line, 0.2)  # creep done -> JUNCTION_TURN
    cmd = nav.step(on_line, 5.0)  # nominal turn time done -> FOLLOW
    assert cmd.state is IRNavState.FOLLOW
    cmd = nav.step(make_reading(GAP), dt=0.1)  # gap under the bar
    assert cmd.state is IRNavState.SEARCH
    assert cmd.left < 0 < cmd.right


# ------------------------------------------------------------- junction


def test_junction_commits_creep_then_timed_turn():
    nav = default_nav(junction_min_s=0.15, creep_before_turn_cm=4.0)  # 4cm @ 10cm/s = 0.4s
    on_line = make_reading(CROSSBAR)
    cmd = nav.step(on_line, 0.1)
    assert cmd.state is IRNavState.FOLLOW  # still confirming
    cmd = nav.step(on_line, 0.1)  # 0.2s >= 0.15 -> committed
    assert cmd.state is IRNavState.JUNCTION_CREEP
    assert cmd.left == cmd.right == 150
    cmd = nav.step(on_line, 0.5)  # 0.5s >= 0.4 -> pivot
    assert cmd.state is IRNavState.JUNCTION_TURN
    assert cmd.left > 0 and cmd.right < 0  # default right turn
    cmd = nav.step(on_line, 3.0)  # past nominal turn time -> follow
    assert cmd.state is IRNavState.FOLLOW
    assert cmd.left == cmd.right == 150


def test_junction_creep_duration_is_distance_over_speed():
    """Default policy: creep_before_turn_cm=9.5 @ forward_speed_cm_per_s=10
    -> 0.95s of blind creep before the pivot (the 2026-08-18 fix: the old
    0.3s time-based creep turned ~3cm short of the crossbar and the car
    exited the turn onto the 2.4cm gap between the sensor pairs)."""
    nav = default_nav(junction_min_s=0.05)
    on_line = make_reading(CROSSBAR)
    nav.step(on_line, 0.1)  # junction confirmed -> JUNCTION_CREEP
    cmd = nav.step(on_line, 0.9)  # 0.9s < 0.95s -> still creeping
    assert cmd.state is IRNavState.JUNCTION_CREEP
    assert "creeping 9.5cm" in cmd.reason
    cmd = nav.step(on_line, 0.1)  # 1.0s >= 0.95s -> pivot
    assert cmd.state is IRNavState.JUNCTION_TURN


def test_creep_duration_helper_uses_distance_and_speed():
    policy = IRNavPolicy()
    assert policy.creep_duration_s() == pytest.approx(9.5 / 10.0)
    assert policy.creep_duration_s() == pytest.approx(0.95)
    faster = IRNavPolicy(forward_speed_cm_per_s=20.0)
    assert faster.creep_duration_s() == pytest.approx(9.5 / 20.0)


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


def test_search_reacquired_junction_crossbar_is_still_a_junction():
    """Reacquiring the line as a full all-4-black bar must be treated as a
    junction, not just plain follow — the search delegates back to follow."""
    nav = default_nav(junction_min_s=0.05)
    nav.step(make_reading(GAP), 0.1)  # into search
    cmd = nav.step(make_reading(CROSSBAR), 0.1)  # reacquired as crossbar
    assert cmd.state is IRNavState.FOLLOW
    assert "possible junction" in cmd.reason
    cmd = nav.step(make_reading(CROSSBAR), 0.1)  # sustained -> commit
    assert cmd.state is IRNavState.JUNCTION_CREEP


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
        {"creep_before_turn_cm": -1.0},
        {"forward_speed_cm_per_s": 0.0},
        {"forward_speed_cm_per_s": -5.0},
        {"search_sweep_deg": -1.0},
        {"search_creep_step_s": -0.1},
        {"search_creep_speed_ratio": 0.0},
        {"search_creep_speed_ratio": 1.5},
        {"search_creep_steps_per_cycle": 0},
        {"search_give_up_s": -1.0},
    ],
)
def test_invalid_search_policy_rejected(kwargs):
    with pytest.raises(ValueError):
        IRNavPolicy(**kwargs)


def test_sweep_duration_uses_calibrated_spin_model():
    policy = IRNavPolicy()
    # 0.41s dead time + 10 deg / 42.0 deg/s
    assert policy.sweep_duration(10.0) == pytest.approx(0.41 + 10.0 / 42.0)
    assert policy.sweep_duration(20.0) == pytest.approx(0.41 + 20.0 / 42.0)


# ------------------------------------------------- route-driven junctions
#
# The 2026-08-19 track run turned right at all six junctions it saw, including the return T
# that has to be crossed, and ended up back in the start box. The action now comes from
# `carbot.ir_route`, so these check the sequence rather than the reading.

RIGHT_BRANCH = (1, 1, 1, 0)  # physical 0111 — the roundabout exit *and* the T junction


def _drive(nav: IRLineNav, channels, seconds: float, dt: float = 0.01):
    """Hold one reading for a while, returning every command produced."""
    return [nav.step(make_reading(channels), dt) for _ in range(int(seconds / dt))]


def _reach_junction(nav: IRLineNav, channels=CROSSBAR, *, run_up_cm: float = 200.0):
    """Cover enough ground to open the gate, then hold a junction until it commits."""
    _drive(nav, CENTRED, run_up_cm / 10.0)  # forward_speed_cm_per_s defaults to 10
    return _drive(nav, channels, 0.5)


def test_first_junction_out_of_the_start_box_turns_right():
    nav = default_nav()
    _reach_junction(nav, run_up_cm=1.0)
    assert nav.last_junction == "start stem T junction"
    assert nav.junctions_seen == 1


def test_the_returning_t_junction_is_crossed_not_turned():
    """The exact bug: the same 0111 that means "exit, turn" earlier means "straight" here."""
    nav = default_nav()
    for _ in range(3):  # prologue T, roundabout entry, roundabout exit
        _reach_junction(nav)
        _settle(nav)

    cmds = _reach_junction(nav, RIGHT_BRANCH)
    assert nav.last_junction == "T junction"
    crossing = next(c for c in cmds if "crossing" in c.reason)
    assert crossing.state is IRNavState.FOLLOW
    assert crossing.left == crossing.right  # straight through, no pivot
    # Still holding the same bar afterwards must not start a second junction.
    assert all(c.left == c.right for c in cmds[cmds.index(crossing) :])
    assert nav.state is IRNavState.FOLLOW


def test_a_junction_read_again_immediately_is_rejected():
    nav = default_nav()
    _reach_junction(nav, run_up_cm=1.0)
    _settle(nav)

    cmds = _drive(nav, CROSSBAR, 0.5)  # no distance covered since the last one
    assert nav.junctions_rejected > 0
    assert nav.junctions_seen == 1
    assert cmds[-1].left == cmds[-1].right
    assert "short of the" in cmds[-1].reason


def test_the_action_does_not_depend_on_which_junction_reading_appears():
    """Entry read 0111 rather than 1111 on the real track; the lap must not care."""
    by_crossbar = default_nav()
    by_branch = default_nav()
    for nav, channels in ((by_crossbar, CROSSBAR), (by_branch, RIGHT_BRANCH)):
        for _ in range(2):
            _reach_junction(nav, channels)
            _settle(nav)
    assert by_crossbar.last_junction == by_branch.last_junction == "roundabout entry"


def test_a_pivot_does_not_count_toward_the_next_gate():
    """A spin covers no ground, so feeding it to the odometer would open the gate early."""
    nav = default_nav()
    _reach_junction(nav, run_up_cm=1.0)
    before = nav.junctions.cm_since_previous
    while nav.state is IRNavState.JUNCTION_TURN:
        nav.step(make_reading(CENTRED), 0.01)
    assert nav.junctions.cm_since_previous == pytest.approx(before)


def _settle(nav: IRLineNav):
    """Run the creep and pivot out to completion."""
    for _ in range(2000):
        if nav.state is IRNavState.FOLLOW:
            return
        nav.step(make_reading(CENTRED), 0.01)
    raise AssertionError("junction never finished")


# ------------------------------------------------------------- route completion


def _reach_next_junction(nav: IRLineNav) -> None:
    """Drive far enough to clear the next distance gate, then hold the crossbar."""
    gate = nav.junctions.pending.min_cm_since_previous
    seconds = gate / nav.policy.forward_speed_cm_per_s + 1.0
    steps = int(seconds / 0.01)
    for _ in range(steps):
        if nav.state is IRNavState.STOPPED:
            return
        nav.step(make_reading(CENTRED), dt=0.01)
    while nav.state is IRNavState.FOLLOW:
        cmd = nav.step(make_reading(CROSSBAR), dt=0.01)
        if cmd.state is IRNavState.STOPPED:
            return
    # Run the scripted creep and turn out to completion.
    for _ in range(2000):
        if nav.state is IRNavState.FOLLOW or nav.state is IRNavState.STOPPED:
            return
        nav.step(make_reading(CENTRED), dt=0.01)


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


def _hold_junction(nav: IRLineNav, reading, seconds: float = 0.3):
    cmd = None
    steps = int(seconds / 0.01)
    for _ in range(steps):
        cmd = nav.step(make_reading(reading), dt=0.01)
    return cmd


def _gated_nav() -> IRLineNav:
    """A nav whose next junction is 60cm away, so an immediate junction is gated out."""
    from carbot.ir_route import TASK1_LOOP_ONLY

    return default_nav(route=TASK1_LOOP_ONLY)


def test_a_gated_out_junction_still_steers_toward_the_line():
    """Regression: holding straight here drove the car off the paper on 2026-08-19.

    The gate rejecting a reading means "not the junction the route wants", not "ignore
    where the line is" — the curve that produced it still has to be steered on.
    """
    nav = _gated_nav()
    cmd = _hold_junction(nav, SKEW_LEFT)
    assert nav.junctions_rejected > 0
    assert cmd.left < cmd.right, "1100 means the line is left; the left wheel must slow"


def test_a_gated_out_junction_steers_the_other_way_too():
    nav = _gated_nav()
    cmd = _hold_junction(nav, SKEW_RIGHT)
    assert nav.junctions_rejected > 0
    assert cmd.right < cmd.left, "0011 means the line is right; the right wheel must slow"


def test_a_gated_out_junction_does_not_advance_the_route():
    nav = _gated_nav()
    pending_before = nav.junctions.pending.name
    _hold_junction(nav, SKEW_LEFT)
    assert nav.junctions.pending.name == pending_before
    assert nav.junctions_seen == 0


# ------------------------------------------------- 2026-08-20 real-track dwell fix
#
# Two failures on the two-lap track run: (1) the roundabout exit's dwell timer kept getting
# reset by an interleaved NOISE-classified reading the default signature set did not cover,
# so the sustained bar was never confirmed; (2) while still dwelling toward a confirmed
# junction, steering kept correcting on that reading's offset -- valid for a single straight
# line, not for a curve/branch/crossbar -- pulling the car off its approach before the
# route-driven action ever ran. See carbot.ir_route module docstring for the full diagnosis.

ROUNDABOUT_EXIT_NOISE = (0, 1, 0, 1)  # raw Out-order for physical 1001, seen mid-exit on track


def _exit_only_nav(**policy_kwargs) -> IRLineNav:
    """A nav whose only pending junction is the roundabout exit (0cm gate), so the dwell
    fix can be checked in isolation from the rest of the lap."""
    from carbot.ir_route import ROUNDABOUT_EXIT_SIGNATURES, JunctionAction, RouteJunction, RoutePlan

    exit_only = RoutePlan(
        prologue=(),
        loop=(
            RouteJunction(
                "roundabout exit",
                JunctionAction.TURN_RIGHT,
                0.0,
                confirm_signatures=ROUNDABOUT_EXIT_SIGNATURES,
            ),
        ),
    )
    return default_nav(route=exit_only, **policy_kwargs)


def test_dwelling_on_a_pending_junction_holds_instead_of_steering_on_its_offset():
    """Before the dwell reaches junction_min_s, the car must hold its last steady command,
    not correct on the confirming reading's offset (RIGHT_BRANCH here would otherwise steer
    hard toward one side purely because of how the generic table's offset happens to read)."""
    nav = default_nav(junction_min_s=1.0, speed=150)
    nav.step(make_reading(CENTRED), 0.01)  # establish a steady last-good command
    cmd = nav.step(make_reading(RIGHT_BRANCH), 0.1)  # 0.1s < 1.0s min_s: still dwelling
    assert cmd.state is IRNavState.FOLLOW
    assert cmd.left == cmd.right == 150  # held the centred command, not steered on the offset
    assert "possible junction" in cmd.reason
    assert "holding previous" in cmd.reason


def test_dwelling_with_no_history_yet_holds_centred_not_the_offset():
    nav = default_nav(junction_min_s=1.0)
    cmd = nav.step(make_reading(RIGHT_BRANCH), 0.1)
    assert cmd.left == cmd.right == 150
    assert "no history" in cmd.reason


def test_roundabout_exit_dwell_survives_the_noise_reading_seen_on_track():
    """1001 (Kind.NOISE) appeared between qualifying frames on the real exit and used to
    reset the dwell counter every time it did -- the sustained bar never registered. Four
    frames at dt=0.1s each interleave a NOISE-classified read with junction-shaped ones; the
    total (0.4s) clears junction_min_s only if none of them resets the counter."""
    nav = _exit_only_nav(junction_min_s=0.3)
    sequence = [RIGHT_BRANCH, ROUNDABOUT_EXIT_NOISE, CROSSBAR, ROUNDABOUT_EXIT_NOISE]
    cmd = None
    for reading in sequence:
        cmd = nav.step(make_reading(reading), 0.1)
    assert cmd.state is IRNavState.JUNCTION_CREEP


def test_roundabout_exit_confirm_reading_still_holds_instead_of_steering_mid_dwell():
    nav = _exit_only_nav(junction_min_s=1.0)
    nav.step(make_reading(CENTRED), 0.01)  # steady last-good command
    cmd = nav.step(make_reading(ROUNDABOUT_EXIT_NOISE), 0.1)  # under min_s: still dwelling
    assert cmd.state is IRNavState.FOLLOW
    assert cmd.left == cmd.right == 150
    assert "roundabout exit" in cmd.reason


# ------------------------------------------------- 2026-08-20 search distance + corner window
#
# The car reportedly ran off the map turning from Phase 2 onto Phase 4 (ARC 1). Two fixes:
# (1) JunctionSequencer.travel() was crediting SEARCH's sweep sub-phases -- pure rotation,
# like JUNCTION_TURN -- as forward progress, so a lost car could rack up fabricated distance
# and desynchronise the route from the physical map. (2) ARC 1/2/3 are tight enough (~2.3cm
# radius) that steady-state FOLLOW gains ran wide off the curve; corner windows slow down and
# sharpen the correction for those stretches without ever stopping line tracking.


def test_search_sweep_does_not_advance_the_distance_gate():
    """Regression: SEARCH used to be credited as forward motion like ordinary FOLLOW, so a
    lost car (spinning in place hunting for the line) could fabricate enough "distance" to
    open a gate it never physically reached. The frame that transitions FOLLOW -> SEARCH is
    still credited under the pre-transition state (the same rule JUNCTION_TURN already used);
    what must not happen is *further* accrual on later frames while still in SEARCH."""
    nav = default_nav()
    nav.step(make_reading(GAP), 0.5)  # transition frame: credited once, enters SEARCH
    assert nav.state is IRNavState.SEARCH
    after_entry = nav.junctions.cm_since_previous
    nav.step(make_reading(GAP), 0.5)  # still sweeping
    nav.step(make_reading(GAP), 0.5)
    assert nav.state is IRNavState.SEARCH
    assert nav.junctions.cm_since_previous == pytest.approx(after_entry)


def test_search_creep_sub_phase_also_does_not_advance_the_gate():
    """Even the forward-creep sub-phase of SEARCH is excluded -- its speed differs from the
    forward_speed_cm_per_s the gate assumes, and the car's real position is not known while
    still lost, so no partial credit is given until the line is reacquired and FOLLOW resumes."""
    nav = default_nav(search_creep_step_s=0.1)
    nav.step(make_reading(GAP), 0.05)  # transition frame: one credit, enters SEARCH
    assert nav.state is IRNavState.SEARCH
    after_entry = nav.junctions.cm_since_previous
    for _ in range(80):  # sweep left, sweep right, several creep steps
        nav.step(make_reading(GAP), 0.05)
        if nav.state is not IRNavState.SEARCH:
            break
    assert nav.state is IRNavState.SEARCH
    assert nav.junctions.cm_since_previous == pytest.approx(after_entry)


def _roundabout_entry_only_nav(cm_since_previous: float, **policy_kwargs) -> IRLineNav:
    """A nav whose pending junction is "roundabout entry" with cm_since_previous set directly,
    so a corner window's effect can be checked without driving through the whole approach."""
    from carbot.ir_route import JunctionAction, RouteJunction, RoutePlan

    entry_only = RoutePlan(
        prologue=(),
        loop=(RouteJunction("roundabout entry", JunctionAction.TURN_RIGHT, 0.0),),
    )
    nav = default_nav(route=entry_only, **policy_kwargs)
    nav.junctions.travel(cm_since_previous)
    return nav


def test_corner_window_slows_down_and_sharpens_the_correction():
    nav = _roundabout_entry_only_nav(cm_since_previous=18.0)  # inside ARC 1's 12-23cm window
    cmd = nav.step(make_reading(DRIFT_RIGHT), 0.001)
    assert cmd.state is IRNavState.FOLLOW
    assert cmd.left == 90  # speed scaled 150 * 0.6
    assert cmd.right == 33  # inner_ratio 0.73 * 0.5, off the scaled speed
    assert "ARC 1 SE corner window" in cmd.reason


def test_corner_window_does_not_apply_outside_its_range():
    nav = _roundabout_entry_only_nav(cm_since_previous=5.0)  # Phase 2 straight, before ARC 1
    cmd = nav.step(make_reading(DRIFT_RIGHT), 0.001)
    assert cmd.left == 150
    assert cmd.right == round(150 * 0.73)
    assert "window" not in cmd.reason


def test_corner_windows_do_not_apply_while_a_different_junction_is_pending():
    """The windows are keyed to "roundabout entry" being pending -- the same cm_since_previous
    range means nothing while approaching a different junction."""
    nav = default_nav(junction_min_s=999.0)  # start stem T pending, never confirms
    nav.junctions.travel(18.0)  # would be inside ARC 1's window if entry were pending
    cmd = nav.step(make_reading(DRIFT_RIGHT), 0.001)
    assert cmd.left == 150
    assert "window" not in cmd.reason
