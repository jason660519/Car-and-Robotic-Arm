"""本台車的硬體對應表。

**這裡的對應關係尚未在實機上驗證。** 第一次跑之前請把車架空，
用 `examples/02_motor_check.py` 逐顆確認，再把下面的常數改成實際值。

依據來源：`vendor/yourfun-nezha/wiring/` 的整車接線圖。接線圖畫的是驅動板**背面**，
所以圖上的左右跟從車頭看過去是相反的 —— 這正是必須實測的原因。
"""

from __future__ import annotations

from typing import Literal

Wheel = Literal["front_left", "front_right", "rear_left", "rear_right"]

# 車輪 -> 驅動板 MOTOR 接口編號（1–4）
#
# 接線圖背面標示：M3 左上、M4 右上、M2 左下、M1 右下。
# 下面是「背面的上方 = 車頭、左右鏡像」的推論結果，**未驗證**。
WHEEL_TO_MOTOR: dict[Wheel, int] = {
    "front_left": 3,
    "front_right": 4,
    "rear_left": 2,
    "rear_right": 1,
}

# 某一側的馬達實際轉向與預期相反時，把它列進來即可，不用改 nezha.py
INVERTED_MOTORS: frozenset[int] = frozenset()

# 機械臂關節 -> 驅動板 SERVO 接口編號（1–4）
ARM_JOINT_TO_SERVO: dict[str, int] = {
    "base": 1,
    "shoulder": 2,
    "elbow": 3,
    "gripper": 4,
}

# 各關節的安全角度範圍，避免結構互撞。未量測前一律保守。
ARM_JOINT_LIMITS: dict[str, tuple[float, float]] = {
    "base": (0.0, 180.0),
    "shoulder": (20.0, 160.0),
    "elbow": (20.0, 160.0),
    "gripper": (30.0, 120.0),
}

# 第一次通電測試用的速度。車架空之後再往上調。
SAFE_TEST_SPEED = 200
