"""本台車的硬體對應表。

## 已從原廠文件確定的事

1. **驅動板背面的馬達接口幾何**（`vendor/yourfun-nezha/wiring/1. NeZha-STM32小车整车接线图.pdf`
   右半頁「NeZha驅動板反面」）：

   ```
   M3 ┌───────────┐ M4
      │           │
   M2 └───────────┘ M1
   ```

2. **舵機排針（`S1 S2 S3 S4`）那一側是車頭。**
   依據：該側兩個角落各有一顆白色 LED，就是指令集裡的 `HEADLED`（前燈）。
   另一側是 I2C 排針 `G SDA SCL 5V` 加上 `BT_LED`（固件指示）與 `PG_LED`（電源指示），
   那兩顆是狀態燈不是車燈。

## 已由實機確認的事

2026-07-30 以 `examples/02_motor_check.py` 確認：
M1 = 左後、M2 = 右後、M3 = 右前、M4 = 左前；M2 與 M3 的接線方向需要反轉。
"""

from __future__ import annotations

from typing import Literal

Wheel = Literal["front_left", "front_right", "rear_left", "rear_right"]

# 車輪 -> 驅動板 MOTOR 接口編號（1–4）
#
# 2026-07-30 實機驗證。
WHEEL_TO_MOTOR: dict[Wheel, int] = {
    "front_right": 3,
    "front_left": 4,
    "rear_right": 2,
    "rear_left": 1,
}

# 某幾顆馬達實際轉向與預期相反時列進來，不用改 nezha.py。
# 若「全部」都相反，改 nezha.py 的 FORWARD_IS_MOTOR_A 才是對的做法。
INVERTED_MOTORS: frozenset[int] = frozenset({2, 3})

# 本車使用的是兩線（紅黑）普通直流馬達，沒有霍爾編碼器。
# 驅動板支援編碼器，但 encoder() 在這台車上一律回 0。
# 換成 N20 編碼器馬達（6 線）後把這個改成 True，並接上 MOTOR 接口的 4 孔側。
HAS_ENCODERS = False

# 機械臂關節 -> 驅動板 SERVO 接口編號（1–4）
ARM_JOINT_TO_SERVO: dict[str, int] = {
    "base": 1,
    "shoulder": 2,
    "elbow": 3,
    "gripper": 4,
}

# 各關節的安全角度範圍，避免結構互撞。未實際量測前一律保守。
ARM_JOINT_LIMITS: dict[str, tuple[float, float]] = {
    "base": (0.0, 180.0),
    "shoulder": (20.0, 160.0),
    "elbow": (20.0, 160.0),
    "gripper": (30.0, 120.0),
}

# 第一次通電測試用的速度。車架空、確認方向正確之後再往上調。
SAFE_TEST_SPEED = 200
