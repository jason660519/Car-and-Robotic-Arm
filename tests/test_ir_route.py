"""The junction sequence and its distance gate.

These encode the 2026-08-19 track failure: six junction events, six right turns, and not one
of the straight-through crossings the lap needs. See `carbot.ir_route` for the diagnosis.
"""

from __future__ import annotations

import pytest

from carbot.ir_route import (
    TASK1_LOOP_ONLY,
    TASK1_ROUTE,
    JunctionAction,
    JunctionSequencer,
    RouteJunction,
    RoutePlan,
    task1_route_for_laps,
)


def test_task1_lap_is_two_turns_and_one_crossing():
    actions = [j.action for j in TASK1_ROUTE.loop]
    assert actions == [
        JunctionAction.TURN_RIGHT,
        JunctionAction.TURN_RIGHT,
        JunctionAction.CROSS,
    ]


def test_the_t_junction_is_crossed_not_turned():
    """The failure being fixed: the return T was turned into, landing back in the start box."""
    t_junction = TASK1_ROUTE.loop[-1]
    assert t_junction.name == "T junction"
    assert t_junction.action is JunctionAction.CROSS
    assert t_junction.turn_direction == 0


def test_the_first_junction_is_turned_even_though_the_looping_one_is_crossed():
    """Same physical T, opposite action — which is exactly why the reading cannot decide."""
    assert TASK1_ROUTE.prologue[0].action is JunctionAction.TURN_RIGHT
    assert TASK1_ROUTE.loop[-1].action is JunctionAction.CROSS


def test_plan_runs_the_prologue_once_then_cycles():
    names = [TASK1_ROUTE.at(i).name for i in range(8)]
    assert names == [
        "start stem T junction",
        "roundabout entry",
        "roundabout exit",
        "T junction",
        "roundabout entry",
        "roundabout exit",
        "T junction",
        "roundabout entry",
    ]


def test_plan_rejects_a_negative_index():
    with pytest.raises(ValueError, match="non-negative"):
        TASK1_ROUTE.at(-1)


def test_plan_needs_a_loop():
    with pytest.raises(ValueError, match="at least one junction"):
        RoutePlan(prologue=(), loop=())


def test_sequencer_walks_the_route_in_order():
    seq = JunctionSequencer()
    seq.travel(500.0)
    assert seq.accept().name == "start stem T junction"
    seq.travel(500.0)
    assert seq.accept().name == "roundabout entry"
    seq.travel(500.0)
    assert seq.accept().name == "roundabout exit"
    seq.travel(500.0)
    assert seq.accept().name == "T junction"
    seq.travel(500.0)
    assert seq.accept().name == "roundabout entry"


def test_gate_blocks_a_junction_read_again_too_soon():
    """The roundabout fired four sustained crossbars in 18s; the gate is what discards them."""
    seq = JunctionSequencer()
    seq.travel(100.0)
    seq.accept()  # prologue T
    seq.travel(5.0)
    assert seq.shortfall_cm() == pytest.approx(55.0)  # roundabout entry gate is 60cm


def test_gate_opens_once_the_distance_is_covered():
    seq = JunctionSequencer()
    seq.accept()
    seq.travel(60.0)
    assert seq.shortfall_cm() == 0.0


def test_accepting_restarts_the_distance_measurement():
    seq = JunctionSequencer()
    seq.travel(999.0)
    seq.accept()
    assert seq.cm_since_previous == 0.0


def test_exit_to_t_gate_fits_between_the_real_spacings():
    """23cm from the roundabout exit to the T, ~150cm from the T to the next entry.

    The gate has to clear the short hop without also clearing a re-read, which is only
    possible because the two spacings differ by more than 6x.
    """
    exit_to_t = TASK1_ROUTE.loop[2].min_cm_since_previous
    t_to_entry = TASK1_ROUTE.loop[0].min_cm_since_previous
    assert exit_to_t < 23.0
    assert t_to_entry < 150.0
    assert t_to_entry > 23.0  # a stray reading on the 23cm hop cannot pass as an entry


def test_travel_rejects_reverse():
    with pytest.raises(ValueError, match="non-negative"):
        JunctionSequencer().travel(-1.0)


def test_turn_direction_maps_to_the_wheel_speed_convention():
    assert RouteJunction("x", JunctionAction.TURN_RIGHT, 0.0).turn_direction == 1
    assert RouteJunction("x", JunctionAction.TURN_LEFT, 0.0).turn_direction == -1
    assert RouteJunction("x", JunctionAction.CROSS, 0.0).turn_direction == 0


def test_loop_only_route_starts_at_the_roundabout_entry():
    """`--start-on-loop`: the car is placed on the east-west line, past the stem."""
    assert TASK1_LOOP_ONLY.prologue == ()
    assert TASK1_LOOP_ONLY.at(0).name == "roundabout entry"
    assert TASK1_LOOP_ONLY.loop == TASK1_ROUTE.loop


def test_two_lap_route_crosses_the_first_t_and_stops_at_the_second():
    """The behaviour asked for on the track: lap 1 crosses phase 10, lap 2 halts there."""
    plan = task1_route_for_laps(2)
    walked = [plan.at(i) for i in range(7)]
    assert [j.action for j in walked] == [
        JunctionAction.TURN_RIGHT,  # start-box stem T
        JunctionAction.TURN_RIGHT,  # lap 1 roundabout entry
        JunctionAction.TURN_RIGHT,  # lap 1 roundabout exit
        JunctionAction.CROSS,  # lap 1 phase 10 T junction — straight through
        JunctionAction.TURN_RIGHT,  # lap 2 roundabout entry
        JunctionAction.TURN_RIGHT,  # lap 2 roundabout exit
        JunctionAction.STOP,  # lap 2 phase 10 T junction — halt
    ]


def test_the_stop_stays_put_once_reached():
    plan = task1_route_for_laps(2)
    assert plan.at(7).action is JunctionAction.STOP
    assert plan.at(99).action is JunctionAction.STOP


def test_one_lap_route_stops_at_the_first_t_junction():
    plan = task1_route_for_laps(1)
    assert [j.action for j in (plan.at(0), plan.at(1), plan.at(2), plan.at(3))] == [
        JunctionAction.TURN_RIGHT,
        JunctionAction.TURN_RIGHT,
        JunctionAction.TURN_RIGHT,
        JunctionAction.STOP,
    ]


def test_lap_route_started_on_the_loop_skips_the_stem():
    plan = task1_route_for_laps(2, start_on_loop=True)
    assert plan.at(0).name == "roundabout entry"
    assert [plan.at(i).action for i in range(6)] == [
        JunctionAction.TURN_RIGHT,
        JunctionAction.TURN_RIGHT,
        JunctionAction.CROSS,
        JunctionAction.TURN_RIGHT,
        JunctionAction.TURN_RIGHT,
        JunctionAction.STOP,
    ]


def test_lap_count_must_be_positive():
    with pytest.raises(ValueError):
        task1_route_for_laps(0)


def test_the_stop_keeps_the_t_junction_distance_gate():
    plan = task1_route_for_laps(2)
    assert plan.at(6).min_cm_since_previous == TASK1_ROUTE.loop[-1].min_cm_since_previous
