"""The Task-1 junction sequence: what to do at each junction, and when one counts.

Why the sequence decides, and not the reading
---------------------------------------------
The first attempt keyed the action off the reading, with one ``in_roundabout`` boolean to
separate the two junctions that share a signature. The 2026-08-19 track run showed all three
of its premises were false:

* The T junction reached from the start-box stem reads ``1111``, not ``0111`` — the crossbar
  runs both east and west, so it is symmetric. ``1111`` was assumed unique to the roundabout
  entry, so the very first junction of the run set the flag the wrong way.
* The roundabout entry that run read ``0111``, not ``1111`` — the car arrived skewed. The two
  signatures the design leaned on had swapped places.
* The roundabout produced four more sustained ``1111`` events. "Re-synchronise on every
  ``1111``" only works if ``1111`` is rare, and it is the most common junction reading there is.

Result: six junction events, six right turns, zero of the straight-through crossings the route
needs. The reading simply does not carry enough information — the same local pattern means
"turn" in one place and "straight on" in another.

What does carry it is *where the car is in the lap*, and the route is fixed and known. So the
reading's only job here is "a junction is under the bar"; the action comes from the sequence,
and a distance gate rejects re-reads of the junction just handled. The gaps between junctions
differ by more than 6x, which is what makes a coarse distance estimate enough to hold the
sequence together.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class JunctionAction(Enum):
    """What the car does at a junction the route has reached."""

    TURN_RIGHT = "turn_right"
    TURN_LEFT = "turn_left"
    CROSS = "cross"  # keep going straight; the extra black is off to one side
    STOP = "stop"  # the planned lap count ends here; halt


@dataclass(frozen=True)
class RouteJunction:
    name: str
    action: JunctionAction
    #: Distance the car must have covered since the previous junction before this one can be
    #: accepted. Set to roughly half the true spacing so a slow or wandering lap still clears
    #: it, while a second reading of the junction just handled does not.
    min_cm_since_previous: float

    @property
    def turn_direction(self) -> int:
        """+1 right, -1 left, 0 straight — the convention `wheel_speeds` already uses."""
        if self.action is JunctionAction.TURN_RIGHT:
            return 1
        if self.action is JunctionAction.TURN_LEFT:
            return -1
        return 0


@dataclass(frozen=True)
class RoutePlan:
    """A one-time prologue, then a loop that repeats for as long as the car runs."""

    prologue: tuple[RouteJunction, ...]
    loop: tuple[RouteJunction, ...]

    def __post_init__(self) -> None:
        if not self.loop:
            raise ValueError("a route needs at least one junction in its loop")

    def at(self, index: int) -> RouteJunction:
        """The junction at `index`, counting the prologue first and then cycling the loop."""
        if index < 0:
            raise ValueError("junction index must be non-negative")
        if index < len(self.prologue):
            return self.prologue[index]
        return self.loop[(index - len(self.prologue)) % len(self.loop)]


#: Task 1, counter-clockwise, never returning to the start box. Distances come from
#: docs/task1-single-source-of-truth.md and the route map; the gates are about half of each.
#:
#:   start box --10cm--> T (right) --~150cm--> roundabout entry (right)
#:     --~85cm arc--> roundabout exit (right) --23cm--> T (cross) --~150cm--> ...
TASK1_ROUTE = RoutePlan(
    # No gate on the first one: there is no previous junction to mistake it for, and the
    # sensor sits 9.5cm ahead of the axle, so it can be over the T almost as soon as the car
    # leaves the start box.
    prologue=(RouteJunction("start stem T junction", JunctionAction.TURN_RIGHT, 0.0),),
    loop=(
        RouteJunction("roundabout entry", JunctionAction.TURN_RIGHT, 60.0),
        RouteJunction("roundabout exit", JunctionAction.TURN_RIGHT, 40.0),
        RouteJunction("T junction", JunctionAction.CROSS, 10.0),
    ),
)


#: The same lap without the one-time stem out of the start box, for starting the car already
#: on the east-west line facing east. The prologue T is the junction that contaminated the
#: 2026-08-19 run's sequence, so dropping it isolates the loop logic from that interaction.
TASK1_LOOP_ONLY = RoutePlan(prologue=(), loop=TASK1_ROUTE.loop)


def task1_route_for_laps(laps: int, *, start_on_loop: bool = False) -> RoutePlan:
    """Task 1 driven `laps` times, halting at the T junction that closes the last lap.

    The stop is a specific entry in the sequence, not a tally compared against a target,
    for the same reason the actions are: a counter that slips once stays wrong. Every
    junction before the last is spelled out in the prologue, so reaching the stop means the
    car has actually been through all of them. `RoutePlan.at` cycles the one-entry loop, so
    once the route is complete it stays complete.
    """
    if laps < 1:
        raise ValueError("laps must be at least 1")
    base = TASK1_LOOP_ONLY if start_on_loop else TASK1_ROUTE
    final_t = RouteJunction(
        "final T junction", JunctionAction.STOP, base.loop[-1].min_cm_since_previous
    )
    return RoutePlan(
        prologue=base.prologue + base.loop * (laps - 1) + base.loop[:-1],
        loop=(final_t,),
    )


class JunctionSequencer:
    """Tracks which junction is next and how far the car has come since the last one."""

    def __init__(self, plan: RoutePlan | None = None) -> None:
        self.plan = plan or TASK1_ROUTE
        self.index = 0
        self.cm_since_previous = 0.0

    @property
    def pending(self) -> RouteJunction:
        """The junction the route says comes next."""
        return self.plan.at(self.index)

    def travel(self, cm: float) -> None:
        """Add forward distance. Pure rotation must not be counted."""
        if cm < 0:
            raise ValueError("distance travelled must be non-negative")
        self.cm_since_previous += cm

    def shortfall_cm(self) -> float:
        """How much further the car must travel before the pending junction is believable."""
        return max(0.0, self.pending.min_cm_since_previous - self.cm_since_previous)

    def accept(self) -> RouteJunction:
        """Consume the pending junction and start measuring toward the next one."""
        junction = self.pending
        self.index += 1
        self.cm_since_previous = 0.0
        return junction
