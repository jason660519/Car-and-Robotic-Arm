#!/usr/bin/env python3
"""連線測試 —— 不會讓任何馬達或舵機動作。

在樹莓派上執行：

    uv run python examples/01_i2c_probe.py

確認 I2C bus 通、驅動板在 0x40 有回應、reset 指令送得出去，
以及編碼器讀得到值。這是通電後的第一個該跑的東西。
"""

from __future__ import annotations

import sys

from carbot.nezha import DEFAULT_ADDRESS, DEFAULT_BUS, NeZha, NeZhaError


def main() -> int:
    print(f"開啟 I2C bus {DEFAULT_BUS}，位址 0x{DEFAULT_ADDRESS:02X} …")

    try:
        board = NeZha(init_motors=False)
    except NeZhaError as exc:
        print(f"\n✗ 連線失敗：{exc}")
        print("\n排查順序：")
        print("  1. sudo i2cdetect -y 1  —— 0x40 有沒有出現？")
        print("  2. SDA 接 Pin 3、SCL 接 Pin 5、GND 有沒有共地？")
        print("  3. 驅動板 12V 電源開了嗎？固件指示燈亮著嗎？")
        print("  4. Pan-Tilt HAT（PCA9685）也是 0x40，同時上線會撞位址")
        return 1

    print("✓ reset 指令送出成功，驅動板有回應")

    with board:
        print("\n讀取編碼器（沒接編碼器馬達的接口會回 0）：")
        for n in (1, 2, 3, 4):
            board.init_encoder(n)
            try:
                print(f"  M{n}: {board.encoder(n):>6}")
            except NeZhaError as exc:
                print(f"  M{n}: 讀取失敗 —— {exc}")

        print("\n閃一下前燈確認指令通道正常 …")
        board.led("head", True)
        board.led("head", False)

    print("\n✓ 全部通過。下一步：examples/02_motor_check.py（請先把車架空）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
