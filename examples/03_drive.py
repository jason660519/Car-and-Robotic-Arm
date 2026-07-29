#!/usr/bin/env python3
"""最小行駛測試 —— 會讓車子真的動。

⚠️ 執行前務必把**車子架空**，四個輪子離地。
   確認方向正確、config.py 填好之後，才放到地上跑。

    uv run python examples/03_drive.py
"""

from __future__ import annotations

import sys
import time

from carbot import Car, NeZhaError
from carbot.config import SAFE_TEST_SPEED

MOVES = [
    ("前進", lambda c: c.forward(SAFE_TEST_SPEED)),
    ("後退", lambda c: c.backward(SAFE_TEST_SPEED)),
    ("左轉", lambda c: c.turn_left(SAFE_TEST_SPEED)),
    ("右轉", lambda c: c.turn_right(SAFE_TEST_SPEED)),
    ("原地左轉", lambda c: c.spin_left(SAFE_TEST_SPEED)),
    ("原地右轉", lambda c: c.spin_right(SAFE_TEST_SPEED)),
]
HOLD_S = 1.0


def main() -> int:
    if input("車子架空了嗎？四個輪子都離地？(yes/no) ").strip().lower() != "yes":
        print("先架空再來。")
        return 1

    try:
        car = Car()
    except NeZhaError as exc:
        print(f"連線失敗：{exc}")
        print("先跑 examples/01_i2c_probe.py 排查。")
        return 1

    with car:
        for label, move in MOVES:
            print(f"  {label} …", flush=True)
            move(car)
            time.sleep(HOLD_S)
            car.stop()
            time.sleep(0.5)

    print("\n每個動作的方向都對嗎？不對就回頭改 src/carbot/config.py。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
