"""IR sensor line following — 4-channel direct steering without camera.

The sensor's physical layout, the meaning of all 16 readings, and the geometry
that produces them live in :mod:`carbot.ir_geometry`. This module is only the
navigation state machine on top of it.

**The physical channel order was wrong here until 2026-08-19.** This docstring
previously recorded the bar as ``Out4 Out3 Out1 Out2`` left to right, read off
the potentiometer silkscreen. A card swept across the bar tripped the channels
in the order ``Out2 Out1 Out3 Out4`` instead — the leading and trailing edges of
the card agreed independently, and the operator separately confirmed ``Out4`` is
the rightmost sensor. The old order is the exact mirror of the truth, so every
steering correction was being applied to the wrong side.

Two other numbers here were also wrong: the bar spans **64 mm**, not the ~10 mm
once recorded, and the outer gap is **2.8 cm**, not 2.4 cm. What matters for
recovery is not the gap but ``gap - line width = 0.8 cm``: the band of line
positions no channel can see.

Steering comes from :data:`carbot.ir_geometry.STATE_TABLE`, which is total over
all 16 readings and splits them three ways — readings a single 2 cm line can
produce (steer on these), readings needing a second dark feature (junctions and
badly skewed passes over a curve), and non-contiguous readings that one line
cannot produce at all (hold the previous command, never steer).

``0000`` is deliberately not "line lost". Inside the 0.8 cm blind band the car
is squarely on the line and sees nothing, so the previous reading decides:
the line can only leave the bar past an *outer* sensor, making ``0000`` after
``0010``/``0100`` a blind band and ``0000`` after ``0001``/``1000`` a real loss.

Line-recovery search (SEARCH state): on a genuine loss the car probes rather
than stopping — sweep `search_sweep_deg` left, sweep back through centre to the
same angle right (watching for the line throughout), then creep forward in short
steps until the line is seen again, or give up after `search_give_up_s`.

Junctions are sequenced by :mod:`carbot.ir_route`, not by the reading — the reading only
says *that* a junction feature is under the bar, matched against an ordered signal sequence
specific to each junction (:class:`carbot.ir_route.SequenceStep`); which junction it is, and
whether to turn or cross, comes from the route plan plus a distance gate. See the
:mod:`carbot.ir_route` module docstring for the two earlier designs (a shared boolean, then a
single-reading dwell timer) this replaced and why each one broke on real track data.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from carbot.ir_geometry import (
    DETECTION_LIMIT_CM,
    IRState,
    Kind,
    classify,
    resolve_blind,
    to_physical,
    wheel_speeds,
)
from carbot.ir_route import (
    TASK1_CORNER_WINDOWS,
    TASK1_ROUTE,
    TURN_COMPLETE_READING,
    CornerWindow,
    JunctionAction,
    JunctionSequencer,
    RouteJunction,
    RoutePlan,
)

if TYPE_CHECKING:
    from carbot.ir_tracing import IRTracingSensor


@dataclass(frozen=True)
class IRLineReading:
    """One cycle of 4-channel IR sensor data, already classified."""

    channels: tuple[int, int, int, int]  # (Out1..Out4) as the driver reports them
    physical: tuple[int, int, int, int]  # (P1..P4) left to right, 1 = black
    state: IRState  # entry from carbot.ir_geometry.STATE_TABLE
    visible: bool  # any channel sees black

    @property
    def summary(self) -> str:
        bits = "".join(str(b) for b in self.physical)
        return f"{bits} {self.state.label}"

    @property
    def error_fraction(self) -> float:
        """Offset normalised to [-1, 1] against the detection limit, for logs."""
        if self.state.offset_cm is None:
            return 0.0
        return max(-1.0, min(1.0, self.state.offset_cm / DETECTION_LIMIT_CM))


def make_reading(channels: tuple[int, int, int, int]) -> IRLineReading:
    """Classify an ``Out1..Out4`` reading without touching hardware."""
    physical = to_physical(channels)
    return IRLineReading(
        channels=tuple(channels),  # type: ignore[arg-type]
        physical=physical,
        state=classify(physical, physical=True),
        visible=any(physical),
    )


def detect_ir_line(sensor: IRTracingSensor, speed: int = 200) -> IRLineReading:
    """Read the four channels and classify them. ``speed`` is unused, kept for
    call-site compatibility with the example scripts."""
    return make_reading(sensor.read())  # type: ignore[arg-type]


class IRNavState(Enum):
    """Where the car is in the scripted-route plan."""

    FOLLOW = "follow"  # proportional steering on the line (includes matching a junction's
    # approach sequence -- see IRLineNav._approach_step)
    JUNCTION_CREEP = "junction_creep"  # committed to the junction; blind creep before pivoting
    JUNCTION_TURN = "junction_turn"  # spinning right, closed-loop until 0110 or a timeout
    SEARCH = "search"  # line lost; sweep ±search_sweep_deg, then creep forward step by step
    STOPPED = "stopped"  # the route's planned laps are done; latched, wheels held at zero


class IRSearchPhase(Enum):
    """Sub-phases of the line-recovery search."""

    SWEEP_LEFT = "sweep_left"  # probing the left side of the heading where the line was lost
    SWEEP_RIGHT = "sweep_right"  # probing back through centre to the right side
    CREEP = "creep"  # one short forward step, then look again


@dataclass(frozen=True)
class IRNavPolicy:
    """Tunables for :class:`IRLineNav`.

    The Task-1 route is a fixed, known path (see :mod:`carbot.ir_route`), not a maze to be
    explored, so a junction does not need to be *classified* left/right by sensor pattern —
    the route already knows the action. What the sensor does need to do, per junction, is
    recognise its own **ordered signal sequence** (``RouteJunction.approach``, from real-track
    tracing 2026-08-20) — most of these readings are not even junction-shaped in isolation
    (e.g. the roundabout exit's sequence includes ``0101``, which
    :data:`carbot.ir_geometry.STATE_TABLE` classifies as noise, and ends on ``0110``, ordinary
    centred FOLLOW); only the *order* they arrive in is the real signal.
    """

    # ------------------------------------------------------------------
    # TUNING GUIDE — symptom observed on the real car -> field to change.
    # Change ONE field at a time and re-test; several of these interact so isolate which one
    # is wrong. Per-junction approach sequences, creep distances, and turn magnitudes live in
    # carbot.ir_route (RouteJunction.approach/.creep_cm/.turn_deg), not here — this table only
    # covers the policy-wide knobs below.
    #
    #   Symptom                                    -> Field to adjust
    #   ------------------------------------------------------------------
    #   Never detects a junction, drives straight    -> a RouteJunction.approach step's min_cm
    #   through onto blank paper                        in ir_route.py, v (persistence
    #                                                     requirement outlasting the real hold)
    #   Falsely "arrives" at a junction mid-line      -> that step's min_cm ^, or re-check the
    #                                                     approach sequence against a fresh
    #                                                     real-track log (see examples/39's
    #                                                     per-frame P1..P4 log)
    #   Turn stops short of the new heading            -> shouldn't happen -- the turn is
    #                                                     closed-loop on 0110 now, not timed.
    #                                                     If it does, spin_rate_deg_per_s/
    #                                                     spin_dead_time_s are themselves off;
    #                                                     re-run examples/41_motor_spin_angle_sweep.py
    #   Turn never ends, runs to the timeout           -> turn_timeout_scale ^ (if a slow but
    #     ("... timeout, 0110 never seen" in the log)      genuine turn just needs longer), OR
    #                                                     check wheel/axle alignment -- a
    #                                                     chassis fault can stop the car from
    #                                                     ever reacquiring 0110 at all (see
    #                                                     docs/progress/2026-08-20-map1-spin-
    #                                                     recalibration-carpet.md for the kind
    #                                                     of fault to look for)
    #   Wheel speeds during FOLLOW oscillate/snake     -> turn_gain v
    #   Car drifts off-centre before correcting         -> turn_gain ^
    #   Car "hunts" on an already-centred line          -> deadband ^
    #   Car ignores a real small offset                 -> deadband v
    #   After a turn the line is found by the sweep     -> search_sweep_deg ^
    #     but only just (edge of the probe arc)             (probe wider; the
    #                                                      gap-between-pairs
    #                                                      dead zone is ~2.4cm)
    #   Line is straight ahead past the gap and the     -> search_creep_step_s v
    #     creep blows past it without the sensor             or search_creep_speed_ratio v
    #     ever reading black                                (shorter/slower steps)
    #   Search creeps too far before sweeping again     -> search_creep_steps_per_cycle v
    #   Search never stops; car wanders off the map     -> search_give_up_s v (0 = never give up)
    # ------------------------------------------------------------------

    speed: int = 150
    # Proportional steering strength while FOLLOWing. Higher = the inside
    # wheel slows down more for the same line offset (sharper correction).
    # Too high -> oscillates/snakes; too low -> drifts off before correcting.
    turn_gain: float = 2.0
    # |error_fraction| below this counts as "on line" -> drive straight,
    # no correction. Too high -> ignores real small offsets; too low ->
    # constantly makes tiny corrections even when already centred.
    deadband: float = 0.15
    # +1 = right turn, -1 = left turn. Only a fallback used before the first junction commits
    # (every real junction sets its own direction from the route -- see
    # carbot.ir_route.RouteJunction.turn_direction) -- Task-1 never actually reaches this.
    turn_direction: int = 1
    # Measured directly on the Task-1 map paper at speed=150, on carpet
    # underneath the paper (verified 2026-08-20, examples/41_motor_spin_angle_sweep.py,
    # 5-point sweep 2-10s, all 5 confirmed a true in-place pivot -- no chassis
    # drift -- before being recorded; linear fit angle = rate*(duration -
    # dead_time)): rate 42.0 deg/s, dead_time 0.41s. See
    # docs/progress/2026-08-20-map1-spin-recalibration-carpet.md for the full
    # sweep data, including an earlier same-day attempt discarded because a
    # chassis/wheel issue was making the "pivot" drift sideways mid-spin.
    # Supersedes the 2026-08-18 reading (40.5 deg/s, 0.2s dead_time) taken on
    # the same paper -- the dead-time roughly doubled, most likely the surface
    # underneath (carpet vs. whatever the 08-18 measurement sat on) or
    # mechanical wear/realignment from the chassis issue above, not a fixed
    # property of the car. NOT extrapolated from the camera-based calibration
    # (examples/23_cam_spin_rate_check.py, measured on a different, textured
    # surface elsewhere in the room) — friction differs by surface, so that
    # number does not transfer here. These two constants are only valid at
    # `speed=150` on this paper, on this surface; re-run the sweep before
    # trusting them at a different speed, print, or underlying floor.
    spin_rate_deg_per_s: float = 42.0
    spin_dead_time_s: float = 0.41
    # Closed-loop junction turns (2026-08-20, see IRLineNav._turn_step) end on
    # TURN_COMPLETE_READING (0110), not a fixed duration, but still need a safety ceiling in
    # case that reading never comes back (misalignment, a genuine sensor fault) -- without
    # one a lost car here would spin forever. turn_timeout_s() multiplies the nominal timed
    # duration for a junction's expected turn_deg (RouteJunction.turn_deg) by this scale.
    turn_timeout_scale: float = 2.0
    # Forward speed used to convert a RouteJunction's per-junction creep_cm (see
    # carbot.ir_route) into a drive duration. Floor reference was 11.7 cm/s at speed=200 (see
    # docs/progress/2026-08-14-travel-speed-and-coverage.md); on the Map1 paper at speed=150
    # the operator picked 10 cm/s. Re-measure on the paper and update this constant if a
    # creep consistently travels short/long of its target distance -- also used to convert
    # a RouteJunction.approach step's min_cm into elapsed-time terms.
    forward_speed_cm_per_s: float = 10.0
    # ------------------------------------------------------------------
    # LINE-RECOVERY SEARCH — what to do when no channel sees black.
    #
    # The sensor bar spans ~10mm but the two pairs (Out4+Out3 left,
    # Out1+Out2 right) are separated by a ~2.4cm dead zone, and the
    # Task-1 route line is only ~2cm wide — so after a junction turn the
    # car can point straight into the gap and read (0,0,0,0) even though
    # the line is still just ahead. Stopping can never recover from that,
    # so on a lost line the car probes:
    #   1. sweep `search_sweep_deg` to the left,
    #   2. sweep back through centre to `search_sweep_deg` right
    #      (2x the left-sweep rotation, watching for the line the whole
    #      way — see `IRLineNav._search_step`),
    #   3. if still nothing, creep forward in `search_creep_step_s` steps
    #      at `search_creep_speed_ratio * speed` to bring the line under
    #      the bar, repeating steps 1-3 after `search_creep_steps_per_cycle`
    #      steps.
    # Any channel reading black at any moment ends the search and resumes
    # normal follow steering. Sweep timings use the same calibrated
    # spin model as the junction turn (`spin_rate_deg_per_s` +
    # `spin_dead_time_s`), which was measured at speed=150.
    # ------------------------------------------------------------------
    search_sweep_deg: float = 10.0
    # Forward creep per search step (seconds).
    search_creep_step_s: float = 0.3
    # Creep speed as a fraction of `speed` — slow enough that the sensor
    # catches the line while it is still under the bar.
    search_creep_speed_ratio: float = 0.5
    # Creep steps per search cycle before the sweep starts over.
    search_creep_steps_per_cycle: int = 4
    # Stop the car after this many total seconds of searching.
    # 0 disables the timeout (not recommended — the car will wander).
    search_give_up_s: float = 30.0
    # The junction sequence for the lap. `turn_direction` above is only the fallback used
    # before the first junction is reached; each junction carries its own direction.
    route: RoutePlan = TASK1_ROUTE
    # Stretches of continuous curve too tight for the steady-state gains above -- see
    # carbot.ir_route.CornerWindow. Applied only while FOLLOWing; never turns off line
    # tracking, only drives slower and corrects harder for that stretch.
    corner_windows: tuple[CornerWindow, ...] = TASK1_CORNER_WINDOWS

    def __post_init__(self) -> None:
        if not 0 <= self.speed <= 1000:
            raise ValueError("speed must be in [0, 1000]")
        if self.turn_gain <= 0:
            raise ValueError("turn_gain must be positive")
        if not 0.0 <= self.deadband < 1.0:
            raise ValueError("deadband must be in [0, 1)")
        if self.turn_direction not in (1, -1):
            raise ValueError("turn_direction must be 1 (right) or -1 (left)")
        if self.spin_rate_deg_per_s <= 0:
            raise ValueError("spin_rate_deg_per_s must be positive")
        if self.spin_dead_time_s < 0:
            raise ValueError("spin_dead_time_s must be non-negative")
        if self.turn_timeout_scale <= 0:
            raise ValueError("turn_timeout_scale must be positive")
        if self.forward_speed_cm_per_s <= 0:
            raise ValueError("forward_speed_cm_per_s must be positive")
        if self.search_sweep_deg < 0:
            raise ValueError("search_sweep_deg must be non-negative")
        if self.search_creep_step_s < 0:
            raise ValueError("search_creep_step_s must be non-negative")
        if not 0.0 < self.search_creep_speed_ratio <= 1.0:
            raise ValueError("search_creep_speed_ratio must be in (0, 1]")
        if self.search_creep_steps_per_cycle < 1:
            raise ValueError("search_creep_steps_per_cycle must be >= 1")
        if self.search_give_up_s < 0:
            raise ValueError("search_give_up_s must be non-negative")

    def turn_timeout_s(self, turn_deg: float) -> float:
        """Safety ceiling for a closed-loop junction turn (see `IRLineNav._turn_step`) --
        `turn_timeout_scale` times the nominal timed duration for `turn_deg`, generous enough
        that a turn genuinely slower than calibrated still gets to finish."""
        return self.turn_timeout_scale * (self.spin_dead_time_s + turn_deg / self.spin_rate_deg_per_s)

    def sweep_duration(self, deg: float) -> float:
        """Time to spin ``deg`` degrees, using the same calibrated spin model
        as the junction turn (rate 42.0 deg/s, dead time 0.41s at speed 150)."""
        return self.spin_dead_time_s + deg / self.spin_rate_deg_per_s


@dataclass(frozen=True)
class IRNavCommand:
    """One step of wheel speeds plus why, for the log."""

    left: int
    right: int
    reason: str
    state: IRNavState


class IRLineNav:
    """Tracks state across cycles: follow the line, matching a junction's ordered approach
    sequence as it comes into range, then creep + a closed-loop turn (or an immediate
    cross/stop) once that sequence completes.

    Call :meth:`step` once per IR read with the cycle-to-cycle ``dt`` in seconds. A junction
    is *detected* by matching its specific ``RouteJunction.approach`` sequence (see
    :mod:`carbot.ir_route`) but not *classified* by the reading alone — the turn direction,
    creep distance, and action all come from the pre-known route.
    """

    def __init__(self, policy: IRNavPolicy | None = None) -> None:
        self.policy = policy or IRNavPolicy()
        self.state = IRNavState.FOLLOW
        #: Progress through the pending junction's approach sequence -- see `_approach_step`.
        self._approach_index = 0
        self._approach_cm = 0.0
        self._creep_elapsed = 0.0
        self._creep_target_cm = 0.0  # set by _commit_junction before JUNCTION_CREEP is entered
        self._turn_elapsed = 0.0
        self._turn_target_deg = 0.0  # set by _commit_junction before JUNCTION_TURN is entered
        self._search_phase = IRSearchPhase.SWEEP_LEFT
        self._search_elapsed = 0.0  # time in the current search sub-phase
        self._search_total = 0.0  # total time spent searching
        self._search_creep_steps = 0  # creep steps done in the current search cycle
        self._last_command: IRNavCommand | None = None
        self._last_localising: tuple[int, int, int, int] | None = None
        #: Which junction the route expects next, and how far since the last one. The action
        #: comes from here rather than from the reading — see `carbot.ir_route`.
        self.junctions = JunctionSequencer(self.policy.route)
        #: Set while the car is inside the scripted turn, so the distance gate is not fed by
        #: a pivot that covers no ground.
        self._turn_direction = self.policy.turn_direction
        self.junctions_seen = 0
        self.last_junction: str | None = None
        self.junctions_rejected = 0
        self.noise_frames = 0
        #: True from a crossed junction until the bar clears it, so the same dark feature is
        #: not re-detected and does not steer the car onto the branch it just declined.
        self._crossing = False

    def step(self, reading: IRLineReading, dt: float) -> IRNavCommand:
        if dt < 0:
            raise ValueError("dt must be non-negative")
        # Latched: once the route is complete nothing the sensor reports can start the
        # wheels again. A stop that could be un-stopped by a stray reading is not a stop.
        if self.state is IRNavState.STOPPED:
            return self._halt("route complete")
        # Feed the junction distance gate. A pivot covers no ground, so it must not count --
        # and neither does SEARCH: its sweep sub-phases are rotations too (like JUNCTION_TURN,
        # not "close enough to forward motion"), and a search happening at all means the car's
        # position is not actually known, so crediting assumed forward progress during it is
        # exactly the kind of fabricated distance that let a lost car look, on paper, like it
        # was still making planned progress -- see the carbot.ir_route module docstring,
        # 2026-08-20. Distance resumes accruing once the line is reacquired and FOLLOW resumes.
        if self.state not in (IRNavState.JUNCTION_TURN, IRNavState.SEARCH):
            self.junctions.travel(dt * self.policy.forward_speed_cm_per_s)
        if self.state is IRNavState.JUNCTION_TURN:
            return self._turn_step(reading, dt)
        if self.state is IRNavState.JUNCTION_CREEP:
            return self._creep_step(reading, dt)
        if self.state is IRNavState.SEARCH:
            return self._search_step(reading, dt)
        return self._follow_step(reading, dt)

    def _halt(self, note: str) -> IRNavCommand:
        cmd = IRNavCommand(0, 0, note, IRNavState.STOPPED)
        self._last_command = cmd
        return cmd

    def _active_corner_window(self) -> CornerWindow | None:
        """(b/c/d) ARC 1/2/3 corners / 三個轉角弧線. Not a junction -- the pending junction
        (window.while_pending) stays "roundabout entry" for all three; this only says whether
        the current estimated position falls inside one of them.
        不是路口，pending 路口在這三段期間都還是「roundabout entry」；這裡只是判斷目前估計
        位置有沒有落在其中一段弧線的距離區間內。"""
        pending = self.junctions.pending
        cm = self.junctions.cm_since_previous
        for window in self.policy.corner_windows:
            if pending.name == window.while_pending and window.start_cm <= cm <= window.end_cm:
                return window
        return None

    def _steer(self, state: IRState, note: str) -> IRNavCommand:
        speed = self.policy.speed
        inner_ratio = state.inner_ratio
        window = self._active_corner_window()
        if window is not None:
            speed = round(speed * window.speed_scale)
            inner_ratio = max(0.0, min(1.0, inner_ratio * window.inner_ratio_scale))
            note = f"{note} [{window.name} window]"
        left, right = wheel_speeds(speed, state.direction, inner_ratio)
        cmd = IRNavCommand(left, right, note, IRNavState.FOLLOW)
        self._last_command = cmd
        return cmd

    def _hold(self, base_reason: str) -> IRNavCommand:
        """Keep driving the last steady command instead of correcting on this reading.

        Used for genuine noise (impossible from one line) and while still mid-way through a
        junction's approach sequence: neither should feed the generic offset-based
        correction, which is only valid for a single straight line under the bar.
        """
        if self._last_command is not None:
            return IRNavCommand(
                self._last_command.left,
                self._last_command.right,
                f"{base_reason}: holding previous",
                IRNavState.FOLLOW,
            )
        return self._steer(classify((0, 1, 1, 0), physical=True), f"{base_reason}: no history")

    def _approach_step(
        self, pending: RouteJunction, reading: IRLineReading, dt: float
    ) -> IRNavCommand | None:
        """(a/e/f/g/h) Advance `pending`'s ordered approach sequence
        (`carbot.ir_route.RouteJunction.approach`) if `reading` matches the step currently
        being tracked -- or the sequence's first step, after a reset.

        Returns a hold command while still mid-sequence, the arrival command
        (`_reach_junction`) once the last step completes, or ``None`` if this reading is not
        part of the sequence at all — the caller falls through to normal steering. A reading
        that matches neither the current nor the next expected step resets tracking to the
        first step (tried once more this same frame) rather than getting stuck partway
        through a stale match.
        """
        approach = pending.approach
        for _ in range(2):  # one reset-and-retry from step 0, for a stray mid-sequence frame
            step = approach[self._approach_index]
            if reading.physical == step.bits:
                self._approach_cm += dt * self.policy.forward_speed_cm_per_s
                if self._approach_cm < step.min_cm:
                    return self._hold(
                        f"approaching {pending.name}, step {self._approach_index + 1}/"
                        f"{len(approach)} ({reading.summary}) "
                        f"{self._approach_cm:.2f}/{step.min_cm:.2f}cm"
                    )
                if self._approach_index == len(approach) - 1:
                    return self._reach_junction(reading)
                self._approach_index += 1
                self._approach_cm = 0.0
                return self._hold(
                    f"approaching {pending.name}, step {self._approach_index + 1}/"
                    f"{len(approach)} ({reading.summary})"
                )
            if self._approach_index == 0:
                return None
            self._approach_index = 0
            self._approach_cm = 0.0
        return None

    def _commit_junction(
        self, label: str, direction: int, creep_cm: float, turn_deg: float, reading: IRLineReading
    ) -> IRNavCommand:
        """(a/e/f) The turn shared by the start-stem T, roundabout entry, and roundabout exit
        / 發車區T路口、圓環入口、圓環出口共用的轉彎. Approach sequence confirmed: creep to put
        the axle on it, then turn closed-loop. 判定成立後：先直行讓輪軸對齊路口中心，再原地
        轉彎（閉環，見 `_turn_step`）。
        """
        self.junctions_seen += 1
        self.last_junction = label
        self._turn_direction = direction
        self._creep_target_cm = creep_cm
        self._turn_target_deg = turn_deg
        self.state = IRNavState.JUNCTION_CREEP
        self._creep_elapsed = 0.0
        return self._creep_step(reading, 0.0)

    def _reach_junction(self, reading: IRLineReading) -> IRNavCommand:
        """This junction's approach sequence has completed. The route, not the reading, says
        what to do.

        The distance gate comes first: a junction that turns up well before the route expects
        the next one is the junction just handled being read a second time, or a curve taken at
        a shallow enough angle to coincidentally match part of a sequence. Acting on it
        desynchronises the lap.
        """
        state = reading.state
        shortfall = self.junctions.shortfall_cm()
        pending = self.junctions.pending
        if shortfall > 0:
            self.junctions_rejected += 1
            self._approach_index = 0
            self._approach_cm = 0.0
            # Rejected means "not the junction the route is waiting for", not "no information".
            # What produces these is a curve lighting extra channels, and the state table's
            # offset for them is that curve's direction. Steering must keep running on it:
            # the 2026-08-19 two-lap run held straight here instead and drove off the paper
            # in phase 2, with the line already hard left and `1100` rejected by the gate.
            return self._steer(
                state,
                f"junction ignored, {shortfall:.0f}cm short of the {pending.name} gate; "
                f"steering on {state.label}",
            )

        junction = self.junctions.accept()
        self._approach_index = 0
        self._approach_cm = 0.0
        if junction.action is JunctionAction.STOP:
            # (h) Final lap: car stops centred on the T junction, task complete.
            # 最後一圈：車身中心停在 T 路口，任務結束。
            self.junctions_seen += 1
            self.last_junction = junction.name
            self.state = IRNavState.STOPPED
            return self._halt(f"route complete at {junction.name}")
        if junction.action is JunctionAction.CROSS:
            # (g) Lap 2+: no turn, straight through into the next lap's Phase 2. The approach
            # sequence's last step (0110) already means the car is centred on the new line,
            # so there is nothing further to creep or turn through.
            # 第二圈起：T路口不轉彎，直行接下一圈的 Phase 2。approach 序列跑到最後一步
            # (0110) 時車身已經置中，不需要再直行對齊或轉彎。
            self.junctions_seen += 1
            self.last_junction = junction.name
            self._crossing = True
            return self._steer(
                classify((0, 1, 1, 0), physical=True),
                f"crossing {junction.name} straight through",
            )
        return self._commit_junction(
            junction.name, junction.turn_direction, junction.creep_cm, junction.turn_deg, reading
        )

    def _follow_step(self, reading: IRLineReading, dt: float) -> IRNavCommand:
        state = reading.state

        if self._crossing:
            if state.kind is Kind.JUNCTION:
                # Still driving over the junction just crossed. Steering on this reading would
                # pull the car onto the branch it decided not to take.
                return self._steer(
                    classify((0, 1, 1, 0), physical=True),
                    f"still over {self.last_junction}, holding straight",
                )
            self._crossing = False

        approached = self._approach_step(self.junctions.pending, reading, dt)
        if approached is not None:
            return approached

        if state.kind is Kind.NOISE:
            # Non-contiguous black: one 2 cm line cannot produce it, so it is
            # undulation, a mis-tuned pot, or a second feature. Never steer.
            self.noise_frames += 1
            return self._hold(f"noise {state.label}")

        if state.kind is Kind.AMBIGUOUS:
            verdict, offset = resolve_blind(self._last_localising)
            if verdict == "blind":
                blind = IRState(state.bits, Kind.DRIFT, offset, state.inner_ratio, "blind band")
                return self._steer(blind, f"blind band, line {'right' if offset > 0 else 'left'}")
            if verdict == "hold" and self._last_command is not None:
                self.noise_frames += 1
                return IRNavCommand(
                    self._last_command.left,
                    self._last_command.right,
                    "all dark straight from centred: undulation, holding previous",
                    IRNavState.FOLLOW,
                )
            self._enter_search()
            return self._search_step(reading, 0.0)

        # ON_LINE or DRIFT — the readings a single line can produce.
        self._last_localising = state.bits
        if state.kind is Kind.ON_LINE:
            return self._steer(state, "centred")
        return self._steer(state, f"{state.label}, offset {state.offset_cm:+.1f}cm")

    def _creep_step(self, reading: IRLineReading, dt: float) -> IRNavCommand:
        """Blind straight creep — ignores the sensor, only elapsed time matters.

        Moves the wheel axle (not just the forward-mounted sensor) over the
        junction centre before the turn starts, for `_creep_target_cm` (set per-junction by
        `_commit_junction` from `RouteJunction.creep_cm`) at `forward_speed_cm_per_s`. See
        `_follow_step` for why this must not react to sensor readings mid-creep.
        """
        self._creep_elapsed += dt
        duration = self._creep_target_cm / self.policy.forward_speed_cm_per_s
        if self._creep_elapsed >= duration:
            self.state = IRNavState.JUNCTION_TURN
            self._turn_elapsed = 0.0
            return self._turn_step(reading, 0.0)
        return IRNavCommand(
            self.policy.speed,
            self.policy.speed,
            f"junction confirmed; creeping {self._creep_target_cm:.1f}cm "
            f"to centre: {self._creep_elapsed:.2f}/{duration:.2f}s",
            IRNavState.JUNCTION_CREEP,
        )

    def _turn_step(self, reading: IRLineReading, dt: float) -> IRNavCommand:
        """Closed-loop spin: keep turning until the sensor reads `TURN_COMPLETE_READING`
        (0110), not a pure timed spin.

        2026-08-18's original design deliberately ignored the sensor mid-turn ("never exit
        early on line reacquired") because the junction crossbar itself reads black while the
        car pivots on top of it, so checking for *any visible channel* fired almost
        immediately (0.30s into a 2.24s nominal 90° turn, ~12°) — the crossbar, not the new
        line, tripped it. This does not reintroduce that bug: real-track tracing (2026-08-20)
        showed the turn ending in one specific, late-arriving reading (0110, ordinary centred
        FOLLOW) reached only once the car has swept far enough that the outer sensors have
        cleared the old crossbar/curve entirely — checking for that ONE reading, not "any
        channel visible", is what makes closing the loop here safe.

        Two guards: `spin_dead_time_s` as a minimum elapsed time before a 0110 read is trusted
        (the same "motor hasn't really started moving yet" floor the spin calibration itself
        uses — guards against a coincidental 0110 in the very first instant), and
        `turn_timeout_s` as a ceiling in case 0110 never comes back at all (misalignment, a
        genuine sensor fault) — without it a lost car here would spin forever.
        """
        self._turn_elapsed += dt
        timeout_s = self.policy.turn_timeout_s(self._turn_target_deg)
        if self._turn_elapsed >= self.policy.spin_dead_time_s and reading.physical == TURN_COMPLETE_READING:
            self.state = IRNavState.FOLLOW
            # The pivot's real angle is not otherwise verified, so a 0000 immediately after
            # this must not be resolved with the line position from before the turn: that
            # geometry belongs to the old heading. See the 2026-08-20 fix this line preserves.
            self._last_localising = None
            return IRNavCommand(
                self.policy.speed,
                self.policy.speed,
                "junction turn done: line reacquired (0110)",
                IRNavState.FOLLOW,
            )
        if self._turn_elapsed >= timeout_s:
            self.state = IRNavState.FOLLOW
            self._last_localising = None
            return IRNavCommand(
                self.policy.speed,
                self.policy.speed,
                f"junction turn done: {timeout_s:.2f}s timeout, 0110 never seen -- "
                "check wheel/axle alignment",
                IRNavState.FOLLOW,
            )

        speed = self.policy.speed
        if self._turn_direction > 0:
            left, right = speed, -speed
        else:
            left, right = -speed, speed
        return IRNavCommand(
            left,
            right,
            f"junction turn {'right' if self._turn_direction > 0 else 'left'}: "
            f"watching for 0110, {self._turn_elapsed:.2f}/{timeout_s:.2f}s timeout",
            IRNavState.JUNCTION_TURN,
        )

    # ------------------------------------------------------------ SEARCH
    def _enter_search(self) -> None:
        """Start (or restart) the line-recovery search from the current heading."""
        self.state = IRNavState.SEARCH
        self._search_phase = IRSearchPhase.SWEEP_LEFT
        self._search_elapsed = 0.0
        self._search_total = 0.0
        self._search_creep_steps = 0

    def _begin_search_phase(self, phase: IRSearchPhase) -> None:
        self._search_phase = phase
        self._search_elapsed = 0.0

    def _search_step(self, reading: IRLineReading, dt: float) -> IRNavCommand:
        """Recovery for a lost line: sweep ±search_sweep_deg, then creep.

        The sensor is checked every cycle, so the moment any channel sees
        black the search ends and normal follow resumes. Delegating back
        into `_follow_step` means a reacquired reading that is really the start of a
        junction's approach sequence is still handled as one.

        Sweep timing uses the same calibrated spin model as the junction
        turn; the right sweep rotates 2x the left-sweep angle so the bar
        probes both sides of the heading where the line was lost and ends
        up `search_sweep_deg` to the right of it.
        """
        if reading.visible:
            self.state = IRNavState.FOLLOW
            return self._follow_step(reading, 0.0)

        self._search_total += dt
        if self.policy.search_give_up_s > 0 and self._search_total >= self.policy.search_give_up_s:
            return IRNavCommand(
                0,
                0,
                f"search: give up after {self._search_total:.1f}s",
                IRNavState.SEARCH,
            )

        self._search_elapsed += dt
        speed = self.policy.speed
        creep_speed = round(speed * self.policy.search_creep_speed_ratio)

        if self._search_phase is IRSearchPhase.SWEEP_LEFT:
            duration = self.policy.sweep_duration(self.policy.search_sweep_deg)
            if self._search_elapsed >= duration:
                self._begin_search_phase(IRSearchPhase.SWEEP_RIGHT)
                return self._search_step(reading, 0.0)
            return IRNavCommand(
                -speed,
                speed,
                f"search: sweep left {self._search_elapsed:.2f}/{duration:.2f}s",
                IRNavState.SEARCH,
            )

        if self._search_phase is IRSearchPhase.SWEEP_RIGHT:
            # 2x the left sweep: from -deg back through centre to +deg.
            duration = self.policy.sweep_duration(2.0 * self.policy.search_sweep_deg)
            if self._search_elapsed >= duration:
                self._begin_search_phase(IRSearchPhase.CREEP)
                return self._search_step(reading, 0.0)
            return IRNavCommand(
                speed,
                -speed,
                f"search: sweep right {self._search_elapsed:.2f}/{duration:.2f}s",
                IRNavState.SEARCH,
            )

        # IRSearchPhase.CREEP — one short forward step, then look again.
        if self._search_elapsed >= self.policy.search_creep_step_s:
            self._search_creep_steps += 1
            if self._search_creep_steps >= self.policy.search_creep_steps_per_cycle:
                self._begin_search_phase(IRSearchPhase.SWEEP_LEFT)
            else:
                self._begin_search_phase(IRSearchPhase.CREEP)
            return self._search_step(reading, 0.0)
        return IRNavCommand(
            creep_speed,
            creep_speed,
            f"search: creep step {self._search_creep_steps + 1}/"
            f"{self.policy.search_creep_steps_per_cycle} "
            f"{self._search_elapsed:.2f}/{self.policy.search_creep_step_s:.2f}s",
            IRNavState.SEARCH,
        )
