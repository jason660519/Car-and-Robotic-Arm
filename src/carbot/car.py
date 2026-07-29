"""四輪差速車的行駛控制。

把 `NeZha` 的單顆馬達介面包成「左右兩側」的差速控制，並套用
`config.py` 的車輪對應與反轉設定。

    from carbot import Car

    with Car() as car:
        car.forward(300)
        time.sleep(1)
        car.stop()

⚠️ `config.WHEEL_TO_MOTOR` 尚未在實機驗證過。第一次跑務必把車架空，
先用 `examples/02_motor_check.py` 確認每顆馬達對應哪個輪子。
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
    """四輪差速底盤。

    `speed` 一律是 −1000 到 1000，正值前進、負值後退，
    絕對值是 PWM 占空比的千分比。
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
        """底層驅動板，需要直接下指令（舵機、燈）時用。"""
        return self._board

    # ------------------------------------------------------------------ 核心
    def drive(self, left: int, right: int) -> None:
        """分別設定左右兩側的速度。所有移動最後都走這裡。"""
        for speed, motors in ((left, self._left), (right, self._right)):
            speed = max(-MAX_SPEED, min(MAX_SPEED, speed))
            for n in motors:
                self._board.motor(n, -speed if n in config.INVERTED_MOTORS else speed)

    def stop(self) -> None:
        self.drive(0, 0)

    # ------------------------------------------------------------------ 動作
    def forward(self, speed: int = config.SAFE_TEST_SPEED) -> None:
        self.drive(abs(speed), abs(speed))

    def backward(self, speed: int = config.SAFE_TEST_SPEED) -> None:
        self.drive(-abs(speed), -abs(speed))

    def turn_left(self, speed: int = config.SAFE_TEST_SPEED, *, ratio: float = 0.3) -> None:
        """邊前進邊左轉。`ratio` 是內側輪相對外側輪的速度比。"""
        self.drive(round(abs(speed) * ratio), abs(speed))

    def turn_right(self, speed: int = config.SAFE_TEST_SPEED, *, ratio: float = 0.3) -> None:
        self.drive(abs(speed), round(abs(speed) * ratio))

    def spin_left(self, speed: int = config.SAFE_TEST_SPEED) -> None:
        """原地左轉（左右反向）。"""
        self.drive(-abs(speed), abs(speed))

    def spin_right(self, speed: int = config.SAFE_TEST_SPEED) -> None:
        self.drive(abs(speed), -abs(speed))

    def move_for(self, seconds: float, left: int, right: int) -> None:
        """跑指定秒數後自動停下。中途出錯也保證停車。"""
        try:
            self.drive(left, right)
            time.sleep(seconds)
        finally:
            self.stop()

    # ------------------------------------------------------------------ 收尾
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
