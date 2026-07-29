"""互動式檢查機械臂的三顆舵機。

實體配置：S2、S3、S4。每次只動一顆，並只在 90° 中位附近移動 ±10°。
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Protocol

from carbot.nezha import NeZha, NeZhaError

SERVO_CHANNELS = (2, 3, 4)
TEST_ANGLES = (90, 80, 100, 90)


class ServoBoard(Protocol):
    def init_servo(self, channel: int) -> None: ...

    def servo(self, channel: int, angle: float) -> None: ...


def run_check(
    board: ServoBoard,
    prompt: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
) -> None:
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


def main() -> int:
    print("本測試依序檢查 S2、S3、S4，每次只做 90° 附近的小幅移動。")
    print("若卡住、抖動、持續嗡嗡叫或接近極限，立刻關閉機器人主電源。")
    answer = input("手臂周圍已淨空，而且主電源開關伸手可及嗎？(yes/no) ")
    if answer != "yes":
        print("未收到完整的 yes；不送出任何舵機指令。")
        return 1

    board: NeZha | None = None
    try:
        board = NeZha(init_motors=False)
        run_check(board)
    except KeyboardInterrupt:
        print("\n測試已中止。舵機可能仍保持扭力；請關閉機器人主電源。")
        return 130
    except NeZhaError as exc:
        print(f"\n通訊失敗：{exc}")
        print("請關閉機器人主電源，再檢查接線與 I2C 連線。")
        return 1
    finally:
        if board is not None:
            board.close(stop_motors=False)

    print("\n三個接口測試完成。舵機仍可能保持扭力；記錄結果後請關閉主電源。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
