"""IR sensor line following — 4-channel direct steering without camera.

Each of the 4 IR channels reads a strip under the sensor. **Physical left-to-right
order on the sensor bar is Out4, Out3, Out1, Out2** — verified 2026-08-18 from the
potentiometer silkscreen (labelled SW4, SW3, SW1, SW2 left to right) and confirmed
live: a centered line lighting "the middle two" physical LEDs read as channels
(Out1=1, Out2=0, Out3=1, Out4=0) in GPIO/Out-number order. This is NOT the naive
Out1→Out2→Out3→Out4 left-to-right assumption; do not "simplify" this back without
re-verifying on hardware.

    physical:  Out4(L) Out3(L) | Out1(R) Out2(R)
               ├─ left half ──┤ ├─ right half ──┤

Steering logic:
  - All 4 see black (1,1,1,1) → straight ahead
  - Physical left sees more (Out4+Out3 high) → steer left
  - Physical right sees more (Out1+Out2 high) → steer right
  - None see black (0,0,0,0) → line lost; enter SEARCH (see below)
  - Only middle channels lit → on-center, slight correction

Line-recovery search (SEARCH state): the sensor bar spans ~10mm but the
two pairs are separated by a dead zone (~2.4cm) while the Task-1 route
line is only ~2cm wide, so after a turn the car can end up pointing
straight into the gap and read nothing at all. Sitting still can never
recover from that, so instead of stopping, the car probes: sweep
`search_sweep_deg` left, sweep back through centre to the same angle
right (watching for the line the whole time), then creep forward in
short steps until the line is seen again — or the search gives up after
`search_give_up_s`.

State machine: follow the line proportionally; a sustained all-4-black
junction commits to a scripted creep+turn; a lost line triggers the
sweep-and-creep recovery above.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from carbot.ir_tracing import IRTracingSensor


@dataclass(frozen=True)
class IRLineReading:
    """One cycle of 4-channel IR sensor data."""

    channels: tuple[int, int, int, int]  # (Out1, Out2, Out3, Out4) = 1 or 0
    visible: bool  # True if any channel sees the line
    error_fraction: float  # -1.0 (hard left) to +1.0 (hard right)
    summary: str


@dataclass(frozen=True)
class IRSteering:
    """Proportional steering command from IR reading."""

    left: int
    right: int
    reason: str


def detect_ir_line(sensor: IRTracingSensor, speed: int = 200) -> IRLineReading:
    """Read 4 IR channels and compute steering error.

    Returns:
      - visible: True if any channel detects the line
      - error_fraction: proportional steering demand
        * -1.0 = hard left (only left sees line)
        *  0.0 = centered (all 4 or middle 2 see line)
        * +1.0 = hard right (only right sees line)
      - channels: raw (Out1, Out2, Out3, Out4) readings
    """
    ch = sensor.read()  # (1=black, 0=white), in Out1..Out4 order
    # Physical bar order is Out4, Out3, Out1, Out2 (left to right) — see module
    # docstring. Left half = Out4+Out3 (indices 3,2); right half = Out1+Out2.
    left_count = ch[3] + ch[2]
    right_count = ch[0] + ch[1]
    visible = left_count > 0 or right_count > 0

    if not visible:
        return IRLineReading(
            channels=ch,
            visible=False,
            error_fraction=0.0,
            summary="no line",
        )

    if left_count == right_count:
        error = 0.0
        summary = f"centered {left_count}+{right_count}"
    else:
        error = (right_count - left_count) / 4.0
        side = "right" if error > 0 else "left"
        summary = f"{side} L{left_count} R{right_count}"

    return IRLineReading(
        channels=ch,
        visible=True,
        error_fraction=error,
        summary=summary,
    )


def ir_steer_command(reading: IRLineReading, speed: int = 200) -> IRSteering:
    """Convert IR line reading to proportional wheel speeds.

    Proportional steering: the more offset the line, the more the inside wheel slows.

    Args:
      reading: IR line detection result
      speed: base forward speed (0-1000)

    Returns:
      left, right wheel speeds
    """
    if not reading.visible:
        return IRSteering(0, 0, "line lost; stop")

    err = reading.error_fraction
    if abs(err) < 0.15:
        return IRSteering(speed, speed, f"centered err={err:+.2f}")

    turn_gain = 2.0
    ratio = max(0.2, 1.0 - turn_gain * abs(err))

    if err > 0:
        left, right = speed, int(speed * ratio)
    else:
        left, right = int(speed * ratio), speed

    return IRSteering(left, right, f"steer err={err:+.2f} ratio={ratio:.2f}")


class IRNavState(Enum):
    """Where the car is in the scripted-route plan."""

    FOLLOW = "follow"  # proportional steering on the line
    JUNCTION_CREEP = "junction_creep"  # committed to the junction; blind creep before pivoting
    JUNCTION_TURN = "junction_turn"  # spinning through a known, pre-planned turn
    SEARCH = "search"  # line lost; sweep ±search_sweep_deg, then creep forward step by step


class IRSearchPhase(Enum):
    """Sub-phases of the line-recovery search."""

    SWEEP_LEFT = "sweep_left"  # probing the left side of the heading where the line was lost
    SWEEP_RIGHT = "sweep_right"  # probing back through centre to the right side
    CREEP = "creep"  # one short forward step, then look again


@dataclass(frozen=True)
class IRNavPolicy:
    """Tunables for :class:`IRLineNav`.

    The Task-1 route is a fixed, known path (see Map1-Task1 route plan), not a
    maze to be explored — so a junction does not need to be *classified*
    left/right by sensor pattern (a symmetric T looks the same from either
    branch with only 4 channels spanning ~10mm). Instead the sensor's job is
    only to detect *that* a junction was reached (a wide dark crossbar lights
    every channel, vs. the narrow line during normal follow lighting only the
    middle two — verified 2026-08-18: normal follow reads physical
    [0,1,1,0], never [1,1,1,1]), and the turn direction/duration comes from
    the pre-known route.
    """

    # ------------------------------------------------------------------
    # TUNING GUIDE — symptom observed on the real car -> field to change.
    # Change ONE field at a time and re-test; several of these interact
    # (e.g. creep_before_turn_cm and junction_min_s both shift *when* the
    # turn starts, for different reasons) so isolate which one is wrong.
    #
    #   Symptom                                    -> Field to adjust
    #   ------------------------------------------------------------------
    #   Spins before reaching the junction centre  -> creep_before_turn_cm ^
    #     (axle is still short of the crossbar when the turn starts)
    #   Spins well past the junction centre         -> creep_before_turn_cm v
    #     (car has already driven onto the far branch before it turns)
    #   The creep distance looks right but the car  -> forward_speed_cm_per_s
    #     consistently travels short/long of it         (re-measure the on-paper
    #     forward speed and update the constant; do
    #     not silently bump creep_before_turn_cm)
    #   Never detects the junction at all,           -> junction_min_s v
    #   drives straight through onto blank paper        (the crossbar may
    #                                                      cross the sensor
    #                                                      faster than the
    #                                                      current dwell
    #                                                      requirement)
    #   Falsely "sees" a junction on the normal line -> junction_min_s ^
    #     (mid-follow all 4 channels blip black briefly, e.g. paper fold
    #     or sensor bounce, and it commits to a turn that shouldn't happen)
    #   Turn stops short of 90° (or the target angle) -> turn_deg ^, OR
    #                                                     spin_rate_deg_per_s v
    #   Turn overshoots past 90°                       -> turn_deg v, OR
    #                                                     spin_rate_deg_per_s ^
    #     (re-run examples/41_spin_angle_sweep.py if unsure which one moved —
    #     it re-measures spin_rate_deg_per_s/spin_dead_time_s directly; do not
    #     guess-scale them, this project already got burned assuming a
    #     camera-measured rate would transfer to this paper — see below)
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
    # All 4 channels must read black for AT LEAST this long (seconds)
    # before it's trusted as a real junction crossbar and not a momentary
    # coincidence (e.g. a paper fold or a single noisy sample). Too high
    # relative to how fast the car crosses the actual crossbar at `speed`
    # -> the crossbar passes under the sensor before this timer finishes,
    # and the car never registers the junction at all (drives straight
    # through). Too low -> false positives from brief noise on the normal
    # line trigger an unwanted turn.
    junction_min_s: float = 0.15
    # +1 = right turn, -1 = left turn. Task-1's first T-junction is a right turn.
    turn_direction: int = 1
    # Target rotation for the scripted turn. Independent of how long it
    # actually takes (see spin_rate_deg_per_s/spin_dead_time_s below) — this
    # is the "what", those are the "how fast".
    turn_deg: float = 90.0
    # Measured directly on the Task-1 map paper at speed=150 (verified
    # 2026-08-18, examples/41_spin_angle_sweep.py, 5-point sweep 2-10s,
    # linear fit angle = rate*(duration - dead_time)): rate 40.5 deg/s,
    # dead_time 0.2s. NOT extrapolated from the camera-based calibration
    # (examples/23_spin_rate_check.py, measured on a different, textured
    # surface elsewhere in the room) — friction differs by surface, so that
    # number does not transfer here. These two constants are only valid at
    # `speed=150` on this paper; re-run the sweep before trusting them at a
    # different speed or on a different print. nominal_turn_s() computes the
    # actual spin duration from these two plus turn_deg — if the real turn
    # over/undershoots, it's usually faster to re-run the sweep (gets both
    # numbers at once, correctly) than to hand-tune turn_deg as a fudge factor.
    spin_rate_deg_per_s: float = 40.5
    spin_dead_time_s: float = 0.2
    # Straight-line creep after a junction is confirmed, before pivoting,
    # so the wheel axle (the real pivot point — NOT the forward-mounted
    # sensor, which detects the crossbar first because it sits ahead of the
    # axle) is over the junction centre. Expressed as a DISTANCE, because
    # the offset it compensates for is physical: the sensor bar mounts
    # ~9.5cm ahead of the axle, so once the sensor is fully on the crossbar
    # (all 4 black), the axle is still ~9.5cm short of the crossbar centre.
    # The car is blind during this creep by design — only elapsed time
    # decides when the turn starts. `creep_duration_s()` converts the
    # distance to time using `forward_speed_cm_per_s`.
    #
    # Verified 2026-08-18 on the Map1 paper at speed=150 with the old
    # time-based creep (0.3s ≈ 3cm): the turn started with the axle short
    # of the crossbar, the car pivoted onto the ~2.4cm gap between the
    # sensor pairs, read nothing, and spent the rest of the run in
    # line-recovery search (22 searches in 60s) until the operator picked
    # it up. 9.5cm puts the axle on the crossbar so the turn exits onto
    # the line, not the gap.
    creep_before_turn_cm: float = 9.5
    # Forward speed used to convert `creep_before_turn_cm` into a drive
    # duration. Floor reference was 11.7 cm/s at speed=200 (see
    # docs/progress/2026-08-14-travel-speed-and-coverage.md); on the Map1
    # paper at speed=150 the operator picked 10 cm/s (≈0.95s for 9.5cm).
    # Re-measure on the paper and update this constant if the creep
    # consistently travels short/long of the target distance.
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

    def __post_init__(self) -> None:
        if not 0 <= self.speed <= 1000:
            raise ValueError("speed must be in [0, 1000]")
        if self.turn_gain <= 0:
            raise ValueError("turn_gain must be positive")
        if not 0.0 <= self.deadband < 1.0:
            raise ValueError("deadband must be in [0, 1)")
        if self.junction_min_s < 0:
            raise ValueError("junction_min_s must be non-negative")
        if self.turn_direction not in (1, -1):
            raise ValueError("turn_direction must be 1 (right) or -1 (left)")
        if self.turn_deg <= 0:
            raise ValueError("turn_deg must be positive")
        if self.creep_before_turn_cm < 0:
            raise ValueError("creep_before_turn_cm must be non-negative")
        if self.forward_speed_cm_per_s <= 0:
            raise ValueError("forward_speed_cm_per_s must be positive")
        if self.spin_rate_deg_per_s <= 0:
            raise ValueError("spin_rate_deg_per_s must be positive")
        if self.spin_dead_time_s < 0:
            raise ValueError("spin_dead_time_s must be non-negative")
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

    def nominal_turn_s(self) -> float:
        return self.spin_dead_time_s + self.turn_deg / self.spin_rate_deg_per_s

    def creep_duration_s(self) -> float:
        """Blind straight creep after a junction is confirmed, in seconds.

        Converts the sensor-to-axle offset (`creep_before_turn_cm`) to time
        with the measured on-paper forward speed. The car is blind during
        this creep — only elapsed time decides when the turn starts.
        """
        return self.creep_before_turn_cm / self.forward_speed_cm_per_s

    def sweep_duration(self, deg: float) -> float:
        """Time to spin ``deg`` degrees, using the same calibrated spin model
        as the junction turn (rate 40.5 deg/s, dead time 0.2s at speed 150)."""
        return self.spin_dead_time_s + deg / self.spin_rate_deg_per_s


@dataclass(frozen=True)
class IRNavCommand:
    """One step of wheel speeds plus why, for the log."""

    left: int
    right: int
    reason: str
    state: IRNavState


class IRLineNav:
    """Tracks state across cycles: follow the line, then a scripted turn at a junction.

    Call :meth:`step` once per IR read with the cycle-to-cycle ``dt`` in
    seconds. A junction is *detected* (all 4 channels black, sustained) but
    not *classified* — the turn direction is a policy setting, since the
    route is known in advance.
    """

    def __init__(self, policy: IRNavPolicy | None = None) -> None:
        self.policy = policy or IRNavPolicy()
        self.state = IRNavState.FOLLOW
        self._junction_elapsed = 0.0
        self._creep_elapsed = 0.0
        self._turn_elapsed = 0.0
        self._search_phase = IRSearchPhase.SWEEP_LEFT
        self._search_elapsed = 0.0  # time in the current search sub-phase
        self._search_total = 0.0  # total time spent searching
        self._search_creep_steps = 0  # creep steps done in the current search cycle

    def step(self, reading: IRLineReading, dt: float) -> IRNavCommand:
        if dt < 0:
            raise ValueError("dt must be non-negative")
        if self.state is IRNavState.JUNCTION_TURN:
            return self._turn_step(dt)
        if self.state is IRNavState.JUNCTION_CREEP:
            return self._creep_step(dt)
        if self.state is IRNavState.SEARCH:
            return self._search_step(reading, dt)
        return self._follow_step(reading, dt)

    def _follow_step(self, reading: IRLineReading, dt: float) -> IRNavCommand:
        all_four_black = sum(reading.channels) == 4
        if all_four_black:
            self._junction_elapsed += dt
            if self._junction_elapsed >= self.policy.junction_min_s:
                # Junction confirmed: commit. From here on (creep, then
                # turn) the car is blind to the sensor on purpose — verified
                # 2026-08-18 that a single noisy frame mid-crossbar (one
                # channel dropping out, e.g. 1111->1110) fed back into
                # normal proportional steering and yanked the car off the
                # junction before the creep even finished. Once committed,
                # only elapsed time decides what happens next, same as the
                # turn itself.
                self.state = IRNavState.JUNCTION_CREEP
                self._creep_elapsed = 0.0
                return self._creep_step(0.0)
            return IRNavCommand(
                self.policy.speed,
                self.policy.speed,
                f"possible junction: {self._junction_elapsed:.2f}/{self.policy.junction_min_s:.2f}s",
                IRNavState.FOLLOW,
            )
        self._junction_elapsed = 0.0

        if not reading.visible:
            # Line lost — e.g. the car turned onto the ~2.4cm dead zone
            # between the two sensor pairs. Do not just stop: run the
            # sweep-and-creep recovery (see module docstring).
            self._enter_search()
            return self._search_step(reading, 0.0)

        err = reading.error_fraction
        if abs(err) < self.policy.deadband:
            return IRNavCommand(
                self.policy.speed, self.policy.speed, f"centered err={err:+.2f}", IRNavState.FOLLOW
            )

        ratio = max(0.2, 1.0 - self.policy.turn_gain * abs(err))
        if err > 0:
            left, right = self.policy.speed, round(self.policy.speed * ratio)
        else:
            left, right = round(self.policy.speed * ratio), self.policy.speed
        return IRNavCommand(left, right, f"steer err={err:+.2f} ratio={ratio:.2f}", IRNavState.FOLLOW)

    def _creep_step(self, dt: float) -> IRNavCommand:
        """Blind straight creep — ignores the sensor, only elapsed time matters.

        Moves the wheel axle (not just the forward-mounted sensor) over the
        junction centre before the turn starts — the sensor detects the
        crossbar ~9.5cm before the axle reaches it, so the creep duration is
        `creep_before_turn_cm / forward_speed_cm_per_s`. See `_follow_step`
        for why this must not react to sensor readings mid-creep.
        """
        self._creep_elapsed += dt
        if self._creep_elapsed >= self.policy.creep_duration_s():
            self.state = IRNavState.JUNCTION_TURN
            self._turn_elapsed = 0.0
            return self._turn_step(0.0)
        return IRNavCommand(
            self.policy.speed,
            self.policy.speed,
            f"junction confirmed; creeping {self.policy.creep_before_turn_cm:.1f}cm "
            f"to centre: {self._creep_elapsed:.2f}/{self.policy.creep_duration_s():.2f}s",
            IRNavState.JUNCTION_CREEP,
        )

    def _turn_step(self, dt: float) -> IRNavCommand:
        """Pure timed spin — never exit early on "line reacquired".

        The junction crossbar itself reads black while the car pivots on top
        of it, so a handful of degrees into the turn a channel goes black
        again well before the car has actually turned to face the new
        heading; an early "any channel visible" exit fires almost
        immediately (verified 2026-08-18: 0.30s of a 2.24s nominal 90° turn,
        ~12°) and the car re-enters FOLLOW still pointed the old way. Turn
        for the full nominal time, same as the camera-based
        `LineNav._right_turn_step`.
        """
        self._turn_elapsed += dt
        if self._turn_elapsed >= self.policy.nominal_turn_s():
            self.state = IRNavState.FOLLOW
            self._junction_elapsed = 0.0
            return IRNavCommand(
                self.policy.speed, self.policy.speed, "junction turn done: nominal time reached", IRNavState.FOLLOW
            )

        speed = self.policy.speed
        if self.policy.turn_direction > 0:
            left, right = speed, -speed
        else:
            left, right = -speed, speed
        return IRNavCommand(
            left,
            right,
            f"junction turn: {self._turn_elapsed:.2f}/{self.policy.nominal_turn_s():.2f}s",
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
        into `_follow_step` means a reacquired reading that is really a
        junction crossbar (all 4 black) is still handled as one.

        Sweep timing uses the same calibrated spin model as the junction
        turn; the right sweep rotates 2x the left-sweep angle so the bar
        probes both sides of the heading where the line was lost and ends
        up `search_sweep_deg` to the right of it.
        """
        if reading.visible:
            self.state = IRNavState.FOLLOW
            self._junction_elapsed = 0.0
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
