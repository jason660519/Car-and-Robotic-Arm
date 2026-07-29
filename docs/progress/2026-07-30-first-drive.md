# 2026-07-30 小車首次實機上路

## 結果

Raspberry Pi 5 已能透過 I2C 控制 NeZha 驅動板。四顆馬達的實際接口與方向均已確認，
差速控制的六種架空動作全部正確，落地後也完成低速短距離前進測試。

## 通訊確認

在 Raspberry Pi 上執行：

```bash
uv run python examples/01_i2c_probe.py
```

確認結果：

- I2C bus 1 的 `0x40` 有回應
- reset 指令成功
- 本車使用兩線直流馬達，因此依設定跳過編碼器
- 前燈控制正常

## 馬達實測

車身架空後執行：

```bash
uv run python examples/02_motor_check.py
```

實測結果：

| 接口 | 輪位 | 正轉方向 |
|---|---|---|
| M1 | 左後 | 往前 |
| M2 | 右後 | 往後 |
| M3 | 右前 | 往後 |
| M4 | 左前 | 往前 |

輪位對應與原本推論一致；M2、M3 的接線方向相反，因此設定為：

```python
WHEEL_TO_MOTOR = {
    "front_right": 3,
    "front_left": 4,
    "rear_right": 2,
    "rear_left": 1,
}

INVERTED_MOTORS = frozenset({2, 3})
```

四顆馬達並非全部反向，所以不修改 `nezha.py` 的 `FORWARD_IS_MOTOR_A`。

## 行駛確認

保持車身架空並執行：

```bash
uv run python examples/03_drive.py
```

以下六種動作方向全部正確：

- 前進
- 後退
- 左轉
- 右轉
- 原地左轉
- 原地右轉

落地後以速度 200 前進 0.5 秒，方向正確且程式結束後自動停止：

```bash
uv run python -c \
'from carbot import Car; car = Car(); car.move_for(0.5, 200, 200); car.close()'
```

## 程式驗證

實機設定寫回 `src/carbot/config.py`，測試改以套用接線反轉後的邏輯速度驗證差速控制。

```text
pytest: 44 passed
ruff: All checks passed
```

## 下一步

- 在空曠地面逐步調整安全速度與直線行駛表現
- 測量左右側馬達差異，必要時加入校正係數
- 接上機械臂前先逐一確認舵機接口、零位與安全角度
