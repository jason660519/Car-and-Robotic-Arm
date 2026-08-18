#!/usr/bin/env python3
"""互動式檢查機械臂的三顆舵機。

實體配置：S2、S3、S4。每次只動一顆，並只在 90° 中位附近移動 ±10°。

**會驅動舵機。操作者必須站在機器人旁邊，隨時能切斷主電源。**

流程與安全閘門在 :mod:`carbot.servo`，本檔只負責接上真實的 NeZha 板。

Usage:
    PYTHONPATH=src python3 examples/04_servo_check.py
"""

from __future__ import annotations

import sys

from carbot.nezha import NeZha
from carbot.servo import run_session


def main() -> int:
    return run_session(lambda: NeZha(init_motors=False))


if __name__ == "__main__":
    sys.exit(main())
