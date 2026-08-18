"""Guarded servo check for the arm's three servos (S2, S3, S4).

The sequence and its safety gate used to live inside
``examples/04_servo_check.py``. That put unit-testable behaviour — the
exact-``yes`` clearance gate, the one-channel-at-a-time ordering, and the
guarantee that the board is closed with ``stop_motors=False`` on every exit
path — in a file that cannot be imported, because ``04_servo_check`` is not a
valid Python identifier. ``tests/test_servo_check.py`` had to load it through
``importlib`` to reach it. The logic lives here instead so the tests can
import it like any other module; the example is now argparse-free wiring.

Movement is deliberately small: each servo is stepped around its 90° centre
by ±10° only, one channel at a time, with an operator confirmation before
every single move. Servos hold torque after the run, so the operator is told
to cut main power once results are recorded.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from carbot.nezha import NeZhaError

#: Arm servo channels in the order they are exercised.
SERVO_CHANNELS = (2, 3, 4)

#: Angles each channel is stepped through: centre, -10°, +10°, back to centre.
TEST_ANGLES = (90, 80, 100, 90)

#: The only accepted answer to the clearance question. Anything else — "y",
#: "YES ", an empty line — refuses to move, because a mistyped or reflexive
#: confirmation must not energise an arm that someone still has a hand in.
CLEARANCE_ANSWER = "yes"

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_INTERRUPTED = 130


class ServoBoard(Protocol):
    """The board surface :func:`run_check` needs."""

    def init_servo(self, channel: int) -> None: ...

    def servo(self, channel: int, angle: float) -> None: ...


class ManagedServoBoard(ServoBoard, Protocol):
    """A :class:`ServoBoard` the session is also responsible for closing."""

    def close(self, *, stop_motors: bool) -> None: ...


def clearance_confirmed(answer: str) -> bool:
    """True only for an exact ``yes``. See :data:`CLEARANCE_ANSWER`."""
    return answer == CLEARANCE_ANSWER


def run_check(
    board: ServoBoard,
    prompt: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
) -> None:
    """Step S2, S3, S4 through :data:`TEST_ANGLES`, one channel at a time.

    Every individual move waits on ``prompt`` first, so the operator can stop
    between any two commands rather than only between channels.
    """
    for channel in SERVO_CHANNELS:
        output(f"\n=== S{channel} ===")
        board.init_servo(channel)

        for angle in TEST_ANGLES:
            prompt(
                f"確認手已移開、關節沒有卡住，按 Enter 讓 S{channel} 移到 {angle}°；"
                "有異常請直接關閉主電源。"
            )
            board.servo(channel, angle)

        output(f"S{channel} 完成：請記下它控制哪個關節、移動方向，以及有無異音。")


def run_session(
    open_board: Callable[[], ManagedServoBoard],
    prompt: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
) -> int:
    """Gate on operator clearance, run the check, and always close the board.

    ``open_board`` is a factory rather than a board so that nothing touches
    I2C until the clearance answer is an exact ``yes`` — a refused run must
    not have constructed a board at all.

    The board is closed with ``stop_motors=False`` on every exit path: this
    check never started the motors, and stopping them here would issue motor
    commands the operator did not ask for.

    Returns :data:`EXIT_OK`, :data:`EXIT_REFUSED`, or :data:`EXIT_INTERRUPTED`.
    """
    output("本測試依序檢查 S2、S3、S4，每次只做 90° 附近的小幅移動。")
    output("若卡住、抖動、持續嗡嗡叫或接近極限，立刻關閉機器人主電源。")

    if not clearance_confirmed(prompt("手臂周圍已淨空，而且主電源開關伸手可及嗎？(yes/no) ")):
        output("未收到完整的 yes；不送出任何舵機指令。")
        return EXIT_REFUSED

    board: ManagedServoBoard | None = None
    try:
        board = open_board()
        run_check(board, prompt=prompt, output=output)
    except KeyboardInterrupt:
        output("\n測試已中止。舵機可能仍保持扭力；請關閉機器人主電源。")
        return EXIT_INTERRUPTED
    except NeZhaError as exc:
        output(f"\n通訊失敗：{exc}")
        output("請關閉機器人主電源，再檢查接線與 I2C 連線。")
        return EXIT_REFUSED
    finally:
        if board is not None:
            board.close(stop_motors=False)

    output("\n三個接口測試完成。舵機仍可能保持扭力；記錄結果後請關閉主電源。")
    return EXIT_OK
