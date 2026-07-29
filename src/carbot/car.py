"""Differential-drive control for the four-wheel chassis.

This layer wraps the per-motor `NeZha` API into left/right drive commands and applies the wheel
mapping and inversion rules from `config.py`.

    from carbot import Car

    with Car() as car:
        car.forward(300)
        time.sleep(1)
        car.stop()

The current `config.WHEEL_TO_MOTOR` mapping and inversion settings were verified on real hardware.
If motor wiring changes, lift the car and rerun `examples/02_motor_check.py`.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Self

from carbot import config
from carbot.nezha import MAX_SPEED, NeZha

if TYPE_CHECKING:
    from smbus2 import SMBus

LEFT_WHEELS = ("front_left", "rear_left")
RIGHT_WHEELS = ("front_right", "rear_right")


class Car:
    """Four-wheel differential-drive chassis controller.

    Speeds always use the range -1000 to 1000. Positive values mean forward, negative values mean
    reverse, and the absolute value represents PWM duty cycle in thousandths.
    """

    def __init__(self, board: NeZha | int | SMBus | None = None) -> None:
        self._board = (
            board if isinstance(board, NeZha) else NeZha(board if board is not None else 1)
        )
        self._owns_board = not isinstance(board, NeZha)
        self._left = [config.WHEEL_TO_MOTOR[w] for w in LEFT_WHEELS]
        self._right = [config.WHEEL_TO_MOTOR[w] for w in RIGHT_WHEELS]

    @property
    def board(self) -> NeZha:
        """Expose the low-level board object for direct servo or LED control."""
        return self._board

    # ---------------------------------------------------------------- Core
    def drive(self, left: int, right: int) -> None:
        """Set left and right side speeds. All movement funnels through this method."""
        for speed, motors in ((left, self._left), (right, self._right)):
            speed = max(-MAX_SPEED, min(MAX_SPEED, speed))
            for n in motors:
                self._board.motor(n, -speed if n in config.INVERTED_MOTORS else speed)

    def stop(self) -> None:
        self.drive(0, 0)

    # ------------------------------------------------------------- Movements
    def forward(self, speed: int = config.SAFE_TEST_SPEED) -> None:
        self.drive(abs(speed), abs(speed))

    def backward(self, speed: int = config.SAFE_TEST_SPEED) -> None:
        self.drive(-abs(speed), -abs(speed))

    def turn_left(self, speed: int = config.SAFE_TEST_SPEED, *, ratio: float = 0.3) -> None:
        """Drive forward while turning left. `ratio` scales the inside wheel speed."""
        self.drive(round(abs(speed) * ratio), abs(speed))

    def turn_right(self, speed: int = config.SAFE_TEST_SPEED, *, ratio: float = 0.3) -> None:
        self.drive(abs(speed), round(abs(speed) * ratio))

    def spin_left(self, speed: int = config.SAFE_TEST_SPEED) -> None:
        """Rotate left in place."""
        self.drive(-abs(speed), abs(speed))

    def spin_right(self, speed: int = config.SAFE_TEST_SPEED) -> None:
        self.drive(abs(speed), -abs(speed))

    def move_for(self, seconds: float, left: int, right: int) -> None:
        """Drive for a fixed duration, then stop even if an error occurs."""
        try:
            self.drive(left, right)
            time.sleep(seconds)
        finally:
            self.stop()

    # --------------------------------------------------------------- Cleanup
    def close(self) -> None:
        try:
            self.stop()
        finally:
            if self._owns_board:
                self._board.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
