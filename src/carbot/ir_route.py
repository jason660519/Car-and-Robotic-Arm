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

2026-08-20 two-lap track run: still failed, two more premises down
--------------------------------------------------------------------
Running the two-lap plan end to end on real hardware did not complete. Two more assumptions
this design still leaned on turned out false:

* **The roundabout exit's dwell timer never completed.** The exit produced ``0111``, ``1001``,
  ``1111`` and ``1110`` across the approach, in no fixed order. ``0111``/``1111``/``1110`` are
  ``Kind.JUNCTION`` and fed the dwell counter; ``1001`` is ``Kind.NOISE`` (not a signature one
  2cm line can produce) and was outside it. Every time a ``1001`` frame landed between
  qualifying ones, ``IRLineNav._follow_step`` reset the dwell counter to zero (the same "not a
  junction reading, reset" branch that normally protects against noise mid-line). The sustained
  bar was real; the counter just never survived long enough to see it. ``ROUNDABOUT_EXIT_SIGNATURES``
  below widens the confirm set for this one junction so ``1001`` no longer interrupts it.
* **Steering did not stop just because a reading was junction-shaped.** Before the dwell timer
  finishes (and, separately, whenever the distance gate rejects an early reading), the nav layer
  was still steering proportionally on the confirming reading's ``offset_cm``. That offset is
  derived from where a single straight 2cm line sits under the bar; it does not describe a
  roundabout exit curve or a T-junction crossbar, so correcting on it pulled the car off its
  approach before the route-driven turn/cross ever got to run. ``carbot.ir_line_nav.IRLineNav``
  now holds the last steady line-following command instead of steering during that dwell window
  (the distance-gate-rejected case is unchanged — see its own comment, that one has to keep
  steering to avoid a different, already-fixed failure).
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


#: Physical P1..P4 readings that count as "this junction has arrived", for junctions that
#: have not shown a real-hardware anomaly. Every signature carbot.ir_geometry classifies
#: Kind.JUNCTION -- the symmetric crossbar plus a curve/branch read from either side or at
#: too shallow an angle to separate the sensor pairs.
DEFAULT_JUNCTION_SIGNATURES: frozenset[tuple[int, int, int, int]] = frozenset(
    {
        (1, 1, 1, 1),
        (0, 1, 1, 1),
        (1, 1, 1, 0),
        (0, 0, 1, 1),
        (1, 1, 0, 0),
    }
)


@dataclass(frozen=True)
class RouteJunction:
    name: str
    action: JunctionAction
    #: Distance the car must have covered since the previous junction before this one can be
    #: accepted. Set to roughly half the true spacing so a slow or wandering lap still clears
    #: it, while a second reading of the junction just handled does not.
    min_cm_since_previous: float
    #: Physical readings that confirm this specific junction. Defaults to
    #: DEFAULT_JUNCTION_SIGNATURES; widen only where a real track run showed this junction
    #: producing a reading outside that default (see ROUNDABOUT_EXIT_SIGNATURES).
    confirm_signatures: frozenset[tuple[int, int, int, int]] = DEFAULT_JUNCTION_SIGNATURES

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
#: 2026-08-20 track run: the roundabout exit produced (1,0,0,1) alongside the expected
#: junction signatures. carbot.ir_geometry classifies it Kind.NOISE (no single 2cm line can
#: produce it), so left out of this set it was resetting the dwell counter every time it
#: landed between qualifying frames -- see the module docstring above.
ROUNDABOUT_EXIT_SIGNATURES: frozenset[tuple[int, int, int, int]] = DEFAULT_JUNCTION_SIGNATURES | {
    (1, 0, 0, 1)
}

# ---------------------------------------------------------------------------------------
# Task-1 junction map / 任務一路口對照表
#
# Where each named corner/junction of the lap lives in code, and how it's decided.
# 每個轉角/路口的邏輯寫在哪裡、怎麼判定。
#
#   a. Start~T junction, ~90 deg right turn / 發車區~T路口，右轉約90度
#      -> TASK1_ROUTE.prologue[0] below. Runs once, lap 1 only.
#      執行一次，僅第一圈。confirm_signatures 用 DEFAULT_JUNCTION_SIGNATURES。
#      Turn itself: IRLineNav._commit_junction -> _creep_step -> _turn_step
#      (src/carbot/ir_line_nav.py) 實際轉彎動作在 ir_line_nav.py。
#
#   b/c/d. ARC 1 SE / ARC 2 NE / ARC 3 NW corners / 三個轉角弧線
#      NOT a junction -- continuous printed curve, sensor tracks it the whole way.
#      不是路口，是連續黑色弧線，感測器全程持續讀線，不會停下來判定。
#      -> TASK1_CORNER_WINDOWS below (temporary speed/gain boost, never a blind turn).
#      執行：IRLineNav._active_corner_window / IRLineNav._steer (ir_line_nav.py)。
#
#   e. Phase 8 entry into the roundabout, right turn / 圓環入口，右轉
#      -> TASK1_ROUTE.loop[0] below ("roundabout entry").
#      confirm_signatures 用 DEFAULT_JUNCTION_SIGNATURES（未回報異常，沿用預設）。
#
#   f. Roundabout exit into Phase 10, right turn / 離開圓環進入 Phase 10，右轉
#      -> TASK1_ROUTE.loop[1] below ("roundabout exit").
#      confirm_signatures 額外加了 (1,0,0,1)，見 ROUNDABOUT_EXIT_SIGNATURES 下方註解。
#
#   g. Lap 2+: Start~T junction, NO turn, straight through into Phase 2
#      第二圈起：Start~T路口不轉彎，直行接 Phase 2
#      -> TASK1_ROUTE.loop[2] below ("T junction"), JunctionAction.CROSS.
#      執行：IRLineNav._reach_junction 的 CROSS 分支（ir_line_nav.py）。
#
#   h. Final lap: car stops centred on the T junction, task complete
#      最後一圈：車身中心停在 T 路口，任務結束
#      -> task1_route_for_laps() below synthesizes a JunctionAction.STOP entry
#      from loop[2] ("T junction" -> "final T junction"). Same confirm_signatures
#      as g, since it's physically the same junction, just the last time through.
#      跟 g 是同一個實體路口，只是最後一次經過，共用同一組 confirm_signatures。
#      執行：IRLineNav._reach_junction 的 STOP 分支 -> _halt（ir_line_nav.py）。
# ---------------------------------------------------------------------------------------
TASK1_ROUTE = RoutePlan(
    # 2026-08-20 correction: this used to be 0.0 with the reasoning "no previous junction to
    # mistake it for" -- true, but that only rules out *re-reading* a junction, not a spurious
    # trigger before the car has gone anywhere (e.g. noise off the departure-box printing, or a
    # motor-start electrical transient). A gate of 0 accepts either the instant the dwell timer
    # clears, with no distance requirement at all. Photo evidence (2026-08-20) put the sensor
    # roughly 6cm from the T at rest -- half of that, ~3cm, follows the same "half the real
    # distance" rule used for every other gate below.
    # 2026-08-20 修正：原本是 0.0，理由「沒有上一個路口可搞混」沒錯，但那只防得住「重複讀到
    # 同一個路口」，防不住車子還沒真的往前走、就被雜訊（發車區印刷邊框、馬達啟動電氣雜訊）
    # 誤判成路口——0 公分的距離要求形同虛設。實測（2026-08-20 照片）感測器靜止時離 T 路口約
    # 6cm，取一半約 3cm，跟下面其他路口「取實際距離一半」的規則一致。
    prologue=(
        # (a) Start~T junction, ~90° right / 發車區~T路口，右轉約90度 -- lap 1 only, 僅第一圈
        RouteJunction("start stem T junction", JunctionAction.TURN_RIGHT, 3.0),
    ),
    loop=(
        # (e) Phase 8 entry -> roundabout, right / 圓環入口，右轉
        RouteJunction("roundabout entry", JunctionAction.TURN_RIGHT, 60.0),
        # (f) roundabout exit -> Phase 10, right / 圓環出口，右轉
        RouteJunction(
            "roundabout exit",
            JunctionAction.TURN_RIGHT,
            40.0,
            confirm_signatures=ROUNDABOUT_EXIT_SIGNATURES,
        ),
        # (g on lap 2+, h on the final lap) T junction: cross straight through, or --
        # on the last lap -- stop here. Which one applies is decided by
        # task1_route_for_laps() below, not by this entry itself.
        # (g/h) T路口：直行穿越，或在最後一圈停在這裡；由下面 task1_route_for_laps() 決定。
        RouteJunction("T junction", JunctionAction.CROSS, 10.0),
    ),
)


@dataclass(frozen=True)
class CornerWindow:
    """A stretch of continuous curve too tight for the steady-state follow gains.

    This is NOT a scripted/blind turn -- the sensor keeps reading the printed line the whole
    way through. It only asks IRLineNav to drive slower and correct harder while the estimated
    position falls inside the window, so the reactive proportional steering (carbot.ir_geometry)
    can actually keep the bar on a curve tighter than its steady-state gains were tuned for.

    ``start_cm``/``end_cm`` are cm since the *pending* junction's own last accept (i.e.
    ``JunctionSequencer.cm_since_previous``), not since some junction named here -- the window
    is keyed to ``while_pending`` (which junction is currently expected next) because the
    physical stretch a corner sits on is walked once per lap while the junction the car most
    recently left differs by lap (the start-stem T on lap 1's prologue, the crossed T junction
    every lap after), whereas the pending one (roundabout entry) does not.
    """

    name: str
    while_pending: str
    start_cm: float
    end_cm: float
    speed_scale: float = 1.0
    inner_ratio_scale: float = 1.0


#: 2026-08-20: continuous proportional line-following was not tight enough to track these three
#: corners -- ARC 1's radius (~2.3cm, back-computed from its 3.6cm arc length over a 90deg
#: heading change) is smaller than the car's own footprint, so at full speed and steady-state
#: gains the car ran wide off the curve and off the map before the correction caught up.
#: These windows slow down and sharpen the correction for that stretch without ever stopping
#: line tracking or scripting a blind turn -- unlike a T junction, a single continuous curve
#: gives the sensor everything it needs; it just needs a tighter response to keep up.
#:
#: Distances (cm since the pending "roundabout entry" junction's last accept) are derived from
#: docs/task1-single-source-of-truth.md section 3 (Phase 2 = 16.0, ARC 1 ~3.6, Phase 4 = 19.2,
#: ARC 2 ~14.2, Phase 6 = 58.5, ARC 3 ~7.2, Phase 8 = 7.5), with a margin that widens for the
#: later corners because the 10cm/s distance estimate drifts further from the real position the
#: longer the car has driven since the last confirmed junction. The margins and scale factors
#: are a first estimate, not a measured constant -- re-tune from real track logs.
TASK1_CORNER_WINDOWS: tuple[CornerWindow, ...] = (
    CornerWindow("ARC 1 SE corner", "roundabout entry", 12.0, 23.0, 0.6, 0.5),  # (b)
    CornerWindow("ARC 2 NE corner", "roundabout entry", 33.0, 58.0, 0.6, 0.5),  # (c)
    CornerWindow("ARC 3 NW corner", "roundabout entry", 102.0, 124.0, 0.6, 0.5),  # (d)
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
    # (h) Final lap: the T junction that would normally CROSS (g) becomes a STOP instead --
    # same physical junction, same confirm_signatures, just the last time through.
    # 第二圈以後每次經過 T 路口都是 (g) 直行(CROSS)；最後一圈的這一次改成 (h) STOP 停車，
    # 是同一個實體路口、同一組 confirm_signatures，只差在這是最後一次。
    final_t = RouteJunction(
        "final T junction",
        JunctionAction.STOP,
        base.loop[-1].min_cm_since_previous,
        confirm_signatures=base.loop[-1].confirm_signatures,
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
