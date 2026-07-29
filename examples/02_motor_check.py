#!/usr/bin/env python3
"""逐顆確認馬達接口與轉向 —— 會讓輪子轉起來。

⚠️ 執行前務必把**車子架空**，四個輪子離地。

    uv run python examples/02_motor_check.py

每顆馬達正轉 1 秒、停 1 秒、反轉 1 秒。你要記下兩件事：

1. **哪個輪子動了** —— 拿去更新 `src/carbot/config.py` 的 `WHEEL_TO_MOTOR`
2. **正轉時輪子往前還往後** —— 全部相反的話，把 `src/carbot/nezha.py` 的
   `FORWARD_IS_MOTOR_A` 翻過來；只有部分相反，就把那幾顆填進
   `config.py` 的 `INVERTED_MOTORS`

原廠手冊與程式碼註解對正反轉的說法互相矛盾，只能靠這一步確定。
"""

from __future__ import annotations

import sys
import time

from carbot.config import SAFE_TEST_SPEED
from carbot.nezha import NeZha, NeZhaError

HOLD_S = 1.0


def main() -> int:
    answer = input("車子架空了嗎？四個輪子都離地？(yes/no) ").strip().lower()
    if answer != "yes":
        print("先架空再來。")
        return 1

    try:
        board = NeZha()
    except NeZhaError as exc:
        print(f"連線失敗：{exc}")
        print("先跑 examples/01_i2c_probe.py 排查。")
        return 1

    with board:
        for n in (1, 2, 3, 4):
            print(f"\n=== M{n} ===")
            for label, speed in (("正轉", SAFE_TEST_SPEED), ("反轉", -SAFE_TEST_SPEED)):
                print(f"  {label} {abs(speed)} …", flush=True)
                board.motor(n, speed)
                time.sleep(HOLD_S)
                board.motor(n, 0)
                time.sleep(HOLD_S)
            print(f"  M{n} 剛剛動的是哪個輪子？往哪個方向？記下來。")

    print("\n完成。把結果填進 src/carbot/config.py。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
