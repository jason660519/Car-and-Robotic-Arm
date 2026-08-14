"""Tests for the line-navigation state machine, with synthetic readings.

No camera and no car: :class:`carbot.line_nav.LineNav` decides from plain
:class:`~carbot.line_follow.LineReading` values. Each test feeds a scripted
sequence of readings and checks the resulting wheel commands and state
transitions. The roundabout timings use the verified spin rate anchor (53.5
deg/s at speed 200 => one lap ~6.7 s), so a 6.5 s ``roundabout_loop_min_s``
only releases the exit fork after a real lap's worth of time.
"""

from __future__ import annotations

import pytest

from carbot.line_follow import LineReading
from carbot.line_nav import LineNav, NavPolicy, NavState, steer_command

ROI = (48, 326, 0, 640)


def line_reading(
    visible: bool = True,
    error_fraction: float = 0.0,
    junction: bool = False,
    branch_count: int = 1,
    line_width: float = 20.0,
    candidate_centroids: tuple[float, ...] | None = None,
) -> LineReading:
    centroid = 320 + (error_fraction or 0) * 320
    return LineReading(
        visible=visible,
        error_px=error_fraction * 320 if error_fraction is not None else None,
        error_fraction=error_fraction,
        centroid_x=centroid,
        line_width_px=line_width,
        dark_fraction=0.02,
        tracked_rows=100,
        roi=ROI,
        branch_count=branch_count,
        branch_centroids=(centroid,) * branch_count,
        junction=junction,
        candidate_centroids=candidate_centroids or (centroid,),
    )


# ------------------------------------------------------------- steering


def test_line_right_of_centre_slows_the_right_wheel():
    cmd = steer_command(line_reading(error_fraction=0.5), NavPolicy(speed=200))
    assert cmd.action == "follow"
    assert cmd.left == 200
    assert cmd.right < 200
    assert cmd.left > cmd.right


def test_line_left_of_centre_slows_the_left_wheel():
    cmd = steer_command(line_reading(error_fraction=-0.5), NavPolicy(speed=200))
    assert cmd.left < cmd.right
    assert cmd.right == 200


def test_centred_line_drives_straight():
    cmd = steer_command(line_reading(error_fraction=0.0), NavPolicy(speed=200))
    assert cmd.left == cmd.right == 200


def test_turn_is_bounded_by_min_ratio():
    cmd = steer_command(line_reading(error_fraction=1.0), NavPolicy(speed=200, turn_gain=1.0))
    assert cmd.right == round(200 * NavPolicy().min_ratio)


def test_invisible_line_steers_nowhere():
    cmd = steer_command(line_reading(visible=False), NavPolicy(speed=200))
    assert cmd.left == cmd.right == 0


# ----------------------------------------------------------------- states


def test_follows_while_line_visible():
    nav = LineNav(NavPolicy(speed=200))
    cmd = nav.step(line_reading(error_fraction=0.2), dt=1.0 / 15)
    assert nav.state is NavState.FOLLOW
    assert cmd.action == "follow"


def test_lost_line_search_after_timeout():
    nav = LineNav(NavPolicy(speed=200, search_timeout_s=2.0))
    nav.step(line_reading(visible=False), dt=0.5)
    nav.step(line_reading(visible=False), dt=0.5)
    nav.step(line_reading(visible=False), dt=0.5)
    cmd = nav.step(line_reading(visible=False), dt=0.5)  # 2.0 s elapsed -> SEARCH
    assert nav.state is NavState.SEARCH
    assert cmd.action == "search"
    assert cmd.left == -200 and cmd.right == 200  # spin left first


def test_search_alternates_direction():
    nav = LineNav(NavPolicy(speed=200, search_timeout_s=0.0))
    first = nav.step(line_reading(visible=False), dt=0.1)
    second = nav.step(line_reading(visible=False), dt=0.1)
    assert (first.left, first.right) == (-200, 200)
    assert (second.left, second.right) == (200, -200)


def test_reacquired_line_returns_to_follow():
    nav = LineNav(NavPolicy(speed=200, search_timeout_s=1.0))
    nav.step(line_reading(visible=False), dt=1.1)
    assert nav.state is NavState.SEARCH
    cmd = nav.step(line_reading(error_fraction=-0.3), dt=0.1)
    assert nav.state is NavState.FOLLOW
    assert cmd.action == "follow"


def test_persistent_junction_enters_roundabout():
    nav = LineNav(NavPolicy(speed=200, junction_min_s=1.0))
    nav.step(line_reading(error_fraction=0.0), dt=0.5)  # baseline width 20
    nav.step(line_reading(error_fraction=0.0, junction=True, line_width=40), dt=0.5)
    assert nav.state is NavState.FOLLOW  # under junction_min_s
    nav.step(line_reading(error_fraction=0.0, junction=True, line_width=40), dt=0.5)
    assert nav.state is NavState.ROUNDABOUT


def test_junction_without_width_jump_stays_follow():
    """Environment shadows fork the reading but keep the line narrow: no roundabout."""
    nav = LineNav(NavPolicy(speed=200, junction_min_s=0.5))
    nav.step(line_reading(error_fraction=0.0), dt=0.5)  # baseline 20
    nav.step(line_reading(error_fraction=0.0, junction=True, line_width=22), dt=0.5)
    nav.step(line_reading(error_fraction=0.0, junction=True, line_width=22), dt=0.5)
    assert nav.state is NavState.FOLLOW


def test_roundabout_stays_until_lap_time_elapsed():
    nav = LineNav(NavPolicy(speed=200, junction_min_s=0.1, roundabout_loop_min_s=6.5))
    nav.step(line_reading(error_fraction=0.1), dt=0.1)  # baseline
    for _ in range(5):
        nav.step(line_reading(error_fraction=0.1, junction=True, line_width=40), dt=0.1)
    assert nav.state is NavState.ROUNDABOUT
    # 3 s in, no exit fork yet
    for _ in range(25):
        cmd = nav.step(line_reading(error_fraction=0.1), dt=0.1)
    assert nav.state is NavState.ROUNDABOUT
    assert cmd.reason.startswith("roundabout:")


def test_roundabout_exits_after_lap_and_fork():
    nav = LineNav(NavPolicy(speed=200, junction_min_s=0.1, roundabout_loop_min_s=2.0))
    nav.step(line_reading(error_fraction=0.1), dt=0.1)  # baseline
    for _ in range(5):
        nav.step(line_reading(error_fraction=0.1, junction=True, line_width=40), dt=0.1)
    # drive the lap: 2.0 s with no junction
    for _ in range(20):
        nav.step(line_reading(error_fraction=0.1), dt=0.1)
    assert nav.state is NavState.ROUNDABOUT
    # exit fork after the lap minimum
    cmd = nav.step(line_reading(error_fraction=0.1, junction=True, line_width=40), dt=0.1)
    assert nav.state is NavState.FOLLOW
    assert "roundabout exit" in cmd.reason


def test_roundabout_does_not_exit_before_lap_minimum():
    nav = LineNav(NavPolicy(speed=200, junction_min_s=0.1, roundabout_loop_min_s=10.0))
    nav.step(line_reading(error_fraction=0.1), dt=0.1)  # baseline
    for _ in range(5):
        nav.step(line_reading(error_fraction=0.1, junction=True, line_width=40), dt=0.1)
    for _ in range(20):
        nav.step(line_reading(error_fraction=0.1), dt=0.1)
    nav.step(line_reading(error_fraction=0.1, junction=True, line_width=40), dt=0.1)
    assert nav.state is NavState.ROUNDABOUT


def test_line_lock_keeps_target_when_detector_flips():
    """The detector flipping main line to a distant shadow must not yank the wheel."""
    nav = LineNav(NavPolicy(speed=200, expected_center_fraction=0.5))
    nav.step(line_reading(error_fraction=0.0), dt=0.1)  # track centroid 320
    # next frame: detector reports main at 0, but candidate 320 is closest to the lock
    flipped = line_reading(
        error_fraction=-1.0, candidate_centroids=(0.0, 320.0)
    )
    cmd = nav.step(flipped, dt=0.1)
    assert cmd.action == "follow"
    assert cmd.left == cmd.right == 200  # locked 320 = centre -> straight


def test_nav_rejects_negative_dt():
    nav = LineNav()
    with pytest.raises(ValueError):
        nav.step(line_reading(), dt=-1.0)


def test_policy_rejects_invalid_values():
    with pytest.raises(ValueError):
        NavPolicy(speed=1001)
    with pytest.raises(ValueError):
        NavPolicy(min_ratio=0.9, max_ratio=0.1)
    with pytest.raises(ValueError):
        NavPolicy(roundabout_loop_min_s=0)
