"""State machine that turns a line reading into wheel commands.

Bottom layer (`carbot.line_follow.detect_line`) reports *where the line is*;
this module decides *what to do about it*: follow the line proportionally,
search when it disappears, and treat a persistent fork as a roundabout with a
time-confirmed lap before the car picks the exit branch.

The whole module is pure and unit-testable — no camera, no car, no I2C. It
emits :class:`NavCommand` values that the caller applies via `carbot.Car`
(``car.drive(command.left, command.right)``). Timing enters through ``dt``
(frames per second), so the same logic drives tests at any simulated rate.

Roundabout exit uses the agreed double confirmation: a fork (``junction``) is
needed **and** the elapsed time inside the roundabout must reach
``roundabout_loop_min_s``, which is anchored to the verified spin rate
(53.5 deg/s at speed 200, `examples/23_spin_rate_check.py`) — one full lap at
the calibrated speed takes ~6.7 s, so the default 6.5 s only counts a lap
that actually went around. Numbers stay tunable through :class:`NavPolicy`
and are expected to be adjusted against real runs.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from enum import Enum

from carbot.line_follow import LineReading


class NavState(Enum):
    """Where the car is in the navigation plan."""

    FOLLOW = "follow"          # steering on the line
    SEARCH = "search"          # line lost; spin in place to re-acquire it
    ROUNDABOUT = "roundabout"  # inside a fork; lap is time-confirmed before exit


@dataclass(frozen=True)
class NavPolicy:
    """Tunables for the state machine.

    ``speed`` is the base forward speed (Car range -1000..1000; 200 is the
    calibrated value for the spin rate used in roundabout timing).
    ``turn_gain`` maps |error_fraction| to the inside-wheel slowdown; the
    slower inside wheel is ``speed * ratio`` with ``ratio`` clamped between
    ``min_ratio`` and ``max_ratio``. ``junction_min_s`` is how long a fork must
    persist before it counts as a roundabout entry, and
    ``roundabout_loop_min_s`` is the minimum time inside the roundabout before
    an exit fork is believed — see the module docstring for its anchor.
    """

    speed: int = 200
    # Steering sensitivity. The first on-map run showed 0.45 was far too weak:
    # a 138 px offset produced only a 12-speed wheel difference (L200 R188),
    # the car drove almost straight and ran parallel to the line. 2.5 turns a
    # 0.14 error_fraction into a ~0.8 ratio (40-speed difference), with large
    # errors saturating at min_ratio.
    turn_gain: float = 2.5
    min_ratio: float = 0.15
    max_ratio: float = 1.0
    search_timeout_s: float = 4.0
    junction_min_s: float = 1.0
    roundabout_loop_min_s: float = 6.5
    # A fork only counts as a roundabout entry when the main line also widens
    # beyond this multiple of its recent baseline width. The verified 2026-08-15
    # on-map run showed environment shadows keep the main-line width steady
    # (90-150 px) while a real crossing inflates it (500+ px), so the factor
    # separates the two without needing to know the map.
    junction_width_factor: float = 1.5
    # Camera-to-chassis alignment. The camera is not centred on the car's
    # heading (it was repositioned), so "line in the frame centre" is not
    # "car aligned with the line". Calibrated on 2026-08-15 by parking the car
    # with its nose along the line: the line sat at 0.571 of the frame width,
    # not 0.5. Steering error is measured against this fraction instead of the
    # geometric centre.
    expected_center_fraction: float = 0.571

    def __post_init__(self) -> None:
        if not 0 <= self.speed <= 1000:
            raise ValueError("speed must be in [0, 1000]")
        if self.turn_gain <= 0:
            raise ValueError("turn_gain must be positive")
        if not 0.0 < self.min_ratio <= self.max_ratio <= 1.0:
            raise ValueError("min_ratio/max_ratio must satisfy 0 < min <= max <= 1")
        if self.search_timeout_s < 0:
            raise ValueError("search_timeout_s must be non-negative")
        if self.junction_min_s < 0:
            raise ValueError("junction_min_s must be non-negative")
        if self.roundabout_loop_min_s <= 0:
            raise ValueError("roundabout_loop_min_s must be positive")
        if self.junction_width_factor <= 1.0:
            raise ValueError("junction_width_factor must be > 1")
        if not 0.0 < self.expected_center_fraction < 1.0:
            raise ValueError("expected_center_fraction must be in (0, 1)")


@dataclass(frozen=True)
class NavCommand:
    """One step of wheel speeds plus why, for the log."""

    action: str
    left: int
    right: int
    reason: str
    state: NavState


class LineNav:
    """Tracks state across frames and emits wheel commands.

    Call :meth:`step` once per camera frame with the frame-to-frame ``dt`` in
    seconds. The instance keeps the previous error for continuity, the time
    spent in each state, and the fork/roundabout bookkeeping. Stateless
    steering logic lives in the module-level :func:`steer_command`.
    """

    # Fraction of the frame width: a candidate line further than this from the
    # locked target counts as "the line left the view", releasing the lock.
    _LOCK_RELEASE_GAP = 0.15

    def __init__(self, policy: NavPolicy | None = None) -> None:
        self.policy = policy or NavPolicy()
        self.state = NavState.FOLLOW
        self._state_time = 0.0
        self._search_direction = "left"
        self._junction_elapsed = 0.0
        self._roundabout_elapsed = 0.0
        self._roundabout_pending = False
        self._prev_error_fraction: float | None = None
        # Line continuity: the target line is the candidate closest to the last
        # frame's centroid, so the detector switching which dark structure it
        # counts as "main" does not yank the steering (the 2026-08-15 map run
        # jumped from err +0.91 to -0.34 in one frame and the car veered).
        self._last_centroid: float | None = None
        # Recent main-line widths while not in a fork; a junction only counts
        # as a roundabout entry when the line also widens past the baseline.
        self._baseline_widths: deque[float] = deque(maxlen=30)

    def step(self, reading: LineReading, dt: float) -> NavCommand:
        if dt < 0:
            raise ValueError("dt must be non-negative")
        self._state_time += dt

        if self.state is NavState.ROUNDABOUT:
            return self._roundabout_step(reading, dt)
        if self.state is NavState.SEARCH:
            return self._search_step(reading, dt)
        return self._follow_step(reading, dt)

    def _locked(self, reading: LineReading) -> LineReading:
        """Pick the candidate line closest to the previous frame's target.

        The detector reports the most persistent dark structure as the main
        line, which is correct when the map is clean but can flip to an
        unrelated shadow when the real line drifts out of view. Locking on the
        nearest candidate keeps the car steering at the line it was already
        following; when nothing was tracked yet the detector's main line wins.

        The lock is released when every candidate sits further than
        ``_LOCK_RELEASE_GAP`` from the locked target — the line left the view
        (a sharp turn, a missed junction) and steering at a ghost would run
        straight off the map, which the first on-map runs actually did. On
        release the detector's main line is used again.
        """
        if (
            not reading.visible
            or not reading.candidate_centroids
            or self._last_centroid is None
        ):
            return reading
        width = reading.roi[3]
        if not any(
            abs(c - self._last_centroid) <= self._LOCK_RELEASE_GAP * width
            for c in reading.candidate_centroids
        ):
            return reading  # release the lock; fall back to the detector's main line
        target = min(
            reading.candidate_centroids, key=lambda c: abs(c - self._last_centroid)
        )
        return replace(reading, centroid_x=target)

    def _recenter(self, reading: LineReading) -> LineReading:
        """Steer against the calibrated camera offset, not the frame centre."""
        if not reading.visible or reading.centroid_x is None:
            return reading
        width = reading.roi[3]
        error_px = reading.centroid_x - self.policy.expected_center_fraction * width
        return replace(
            reading,
            error_px=error_px,
            error_fraction=error_px / (width / 2),
        )

    # ------------------------------------------------------------- FOLLOW
    def _follow_step(self, reading: LineReading, dt: float) -> NavCommand:
        if not reading.visible:
            self._junction_elapsed = 0.0
            self._roundabout_pending = False
            if self._state_time >= self.policy.search_timeout_s:
                self._enter(NavState.SEARCH)
                return self._search_step(reading, dt)
            return self._drive("follow", 0, 0, "line lost; waiting to search")

        reading = self._locked(reading)
        reading = self._recenter(reading)

        if reading.junction and self._width_jumped(reading):
            self._junction_elapsed += dt
            if self._junction_elapsed >= self.policy.junction_min_s:
                # A persistent fork with a widened line is treated as a
                # roundabout entry. The car keeps following the main line
                # (continuous around the loop); only the exit decision changes.
                self._enter(NavState.ROUNDABOUT)
                self._roundabout_pending = True
                return self._roundabout_step(reading, dt)
        else:
            self._junction_elapsed = 0.0
            self._remember_baseline(reading)

        self._last_centroid = reading.centroid_x
        return steer_command(reading, self.policy, self._prev_error_fraction)

    def _remember_baseline(self, reading: LineReading) -> None:
        if reading.line_width_px > 0:
            self._baseline_widths.append(reading.line_width_px)

    def _width_jumped(self, reading: LineReading) -> bool:
        """True when the main line is markedly wider than its recent norm."""
        if not self._baseline_widths:
            return False
        baseline = sorted(self._baseline_widths)[len(self._baseline_widths) // 2]
        return reading.line_width_px > self.policy.junction_width_factor * baseline

    # ------------------------------------------------------------ SEARCH
    def _search_step(self, reading: LineReading, dt: float) -> NavCommand:
        if reading.visible:
            self._enter(NavState.FOLLOW)
            reading = self._recenter(self._locked(reading))
            self._last_centroid = reading.centroid_x
            return steer_command(reading, self.policy, self._prev_error_fraction)

        direction = self._search_direction
        self._search_direction = "right" if direction == "left" else "left"
        if direction == "left":
            return self._drive("search", -self.policy.speed, self.policy.speed,
                               "searching: spin left")
        return self._drive("search", self.policy.speed, -self.policy.speed,
                           "searching: spin right")

    # -------------------------------------------------------- ROUNDABOUT
    def _roundabout_step(self, reading: LineReading, dt: float) -> NavCommand:
        if not reading.visible:
            self._junction_elapsed = 0.0
            self._enter(NavState.SEARCH)
            return self._search_step(reading, dt)

        reading = self._locked(reading)
        reading = self._recenter(reading)
        self._last_centroid = reading.centroid_x
        self._roundabout_elapsed += dt
        loop_done = self._roundabout_elapsed >= self.policy.roundabout_loop_min_s

        if reading.junction and loop_done:
            # Second fork after a full lap: this is the exit. Pick the branch
            # away from the line we came in on, i.e. the main centroid we are
            # still following is fine — exiting means keeping the line.
            reason = (
                f"roundabout exit: lap {self._roundabout_elapsed:.1f}s "
                ">= min and fork seen"
            )
            self._enter(NavState.FOLLOW)
            return steer_command(reading, self.policy, self._prev_error_fraction, reason)

        reason = (
            f"roundabout: lap {self._roundabout_elapsed:.1f}s / "
            f"{self.policy.roundabout_loop_min_s:.1f}s"
            + (" (fork)" if reading.junction else "")
        )
        return steer_command(reading, self.policy, self._prev_error_fraction, reason)

    # ------------------------------------------------------------- utils
    def _enter(self, state: NavState) -> None:
        self.state = state
        self._state_time = 0.0

    def _drive(self, action: str, left: int, right: int, reason: str) -> NavCommand:
        return NavCommand(action=action, left=left, right=right,
                          reason=reason, state=self.state)


def steer_command(
    reading: LineReading,
    policy: NavPolicy | None = None,
    _prev_error: float | None = None,
    reason: str | None = None,
) -> NavCommand:
    """Proportional steering on the line reading.

    Positive ``error_fraction`` (line right of centre) slows the right wheel;
    negative slows the left. Returns a ``follow`` command with the computed
    speeds. ``_prev_error`` is accepted for API symmetry with :class:`LineNav`
    but the first version is purely proportional — no integral or derivative
    term yet, so the argument is unused.
    """
    policy = policy or NavPolicy()
    if not reading.visible:
        return NavCommand(action="follow", left=0, right=0,
                          reason=reason or "no line", state=NavState.FOLLOW)

    error = reading.error_fraction if reading.error_fraction is not None else 0.0
    ratio = 1.0 - policy.turn_gain * abs(error)
    ratio = max(policy.min_ratio, min(policy.max_ratio, ratio))
    base = policy.speed
    if error > 0:
        left, right = base, round(base * ratio)
    else:
        left, right = round(base * ratio), base

    detail = f"err={error:+.2f} ratio={ratio:.2f}"
    return NavCommand(action="follow", left=left, right=right,
                      reason=f"{reason or 'follow'}: {detail}", state=NavState.FOLLOW)
