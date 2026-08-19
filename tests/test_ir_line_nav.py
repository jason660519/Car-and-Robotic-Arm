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
    0.2 + 10/40.5 = 0.447s; right sweep is 2x the angle = 0.694s)."""
    nav = default_nav()
    gap = make_reading(GAP)
    cmd = nav.step(gap, 0.1)
    assert "sweep left" in cmd.reason
    cmd = nav.step(gap, 0.5)  # left sweep done -> sweep right
    assert cmd.left == 150 and cmd.right == -150
    assert "sweep right" in cmd.reason
    cmd = nav.step(gap, 0.8)  # right sweep done -> creep
    assert cmd.left == cmd.right == 75  # 150 * search_creep_speed_ratio 0.5
    assert "creep step 1/4" in cmd.reason


def test_search_creep_steps_then_restarts_sweep_cycle():
    nav = default_nav(search_creep_steps_per_cycle=2)
    gap = make_reading(GAP)
    nav.step(gap, 0.5)  # enters search (transition consumes no search time)
    nav.step(gap, 0.5)  # finishes left sweep -> sweep right
    nav.step(gap, 0.7)  # finishes right sweep -> creep step 1/2
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
    # 0.2s dead time + 10 deg / 40.5 deg/s
    assert policy.sweep_duration(10.0) == pytest.approx(0.2 + 10.0 / 40.5)
    assert policy.sweep_duration(20.0) == pytest.approx(0.2 + 20.0 / 40.5)
