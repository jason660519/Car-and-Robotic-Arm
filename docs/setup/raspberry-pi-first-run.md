# 樹莓派首次上路

從零到車子會動。每一步都有可驗證的結果，**不要跳步**。

前置：Raspberry Pi 5 已裝好 Raspberry Pi OS 並能連上網。

---

## 0. 通電前先確認接線 ⚠️

| 檢查項 | 正確做法 |
|---|---|
| 驅動板電源 | **12V** 接 12V 電池接口。正負極接反會燒板 |
| Pi 的 5V | 從驅動板 I2C 接口的 `5V` 接到 Pi 的 **Pin 2 或 Pin 4** |
| **不可同時供電** | 用驅動板餵 Pi 時，**絕對不要**再插 Pi 的 USB-C 電源 |
| SDA | 驅動板 `SDA` → Pi **Pin 3** |
| SCL | 驅動板 `SCL` → Pi **Pin 5** |
| GND | 驅動板 `G` → Pi 任一 GND，**必須共地** |
| 馬達接頭 | 2 線馬達插 **2 孔**接口。插進 4 孔編碼器接口會燒板 |

通電後看驅動板上的兩顆指示燈：**電源燈與固件燈都要長亮**。
電源燈熄滅代表電路短路，**立刻斷電**。

## 1. 開啟 I2C

```bash
sudo raspi-config
```

`Interface Options` → `I2C` → `Yes`，然後重開機。

裝工具並確認驅動板有回應：

```bash
sudo apt update && sudo apt install -y i2c-tools
```

```bash
sudo i2cdetect -y 1
```

**預期看到 `40`。** 看不到就回頭檢查第 0 步的接線與電源。

> 不要去 `/boot/firmware/config.txt` 設 `dtparam=i2c_arm_baudrate=400000`。
> 驅動板規格上限是 200kHz，Pi 預設的 100kHz 剛好。

把自己加進 `i2c` 群組，之後跑程式就不用 `sudo`：

```bash
sudo usermod -aG i2c $USER && echo "重新登入後生效"
```

## 2. 把程式放上 Pi

```bash
cd ~ && git clone https://github.com/jason660519/Car-and-Robotic-Arm.git && cd Car-and-Robotic-Arm
```

## 3. 裝 uv 與相依套件

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
source ~/.bashrc && uv sync
```

## 4. 確認通訊 —— 不會讓任何東西動

```bash
uv run python examples/01_i2c_probe.py
```

**預期**：`✓ reset 指令送出成功，驅動板有回應`，然後前燈閃一下。

前燈有閃 = 指令通道確認可用。沒閃但沒報錯，代表指令送出去了但板子沒反應，
回頭檢查固件指示燈。

## 5. 確認馬達對應 —— ⚠️ 車子要架空

**把車架起來，四個輪子離地。**

```bash
uv run python examples/02_motor_check.py
```

每顆馬達會正轉 1 秒、停、反轉 1 秒。拿紙筆記兩件事：

1. **M1／M2／M3／M4 分別是哪個輪子**（左前／右前／左後／右後）
2. **「正轉」時輪子是往前還是往後**

> 為什麼一定要做這步：原廠接線圖沒標「反面」是鏡像還是透視視角，
> 而手冊 P.13 與原廠程式碼註解對正反轉的說法**互相矛盾**。
> 只能實測。詳見 [nezha-i2c-protocol.md](../hardware/nezha-i2c-protocol.md)。

## 6. 把結果填進設定

編輯 [`src/carbot/config.py`](../../src/carbot/config.py)：

```python
WHEEL_TO_MOTOR = {
    "front_left": 4,   # ← 改成第 5 步實測的結果
    "front_right": 3,
    "rear_left": 1,
    "rear_right": 2,
}
```

轉向的處理：

| 狀況 | 怎麼改 |
|---|---|
| **全部**四顆都反 | 改 `src/carbot/nezha.py` 的 `FORWARD_IS_MOTOR_A = False` |
| 只有某幾顆反 | 把那幾顆的編號填進 `config.INVERTED_MOTORS`，例如 `frozenset({1, 3})` |

## 7. 行駛測試 —— 還是架空

```bash
uv run python examples/03_drive.py
```

依序跑前進、後退、左轉、右轉、原地左轉、原地右轉。

**每個動作的方向都要對。** 有一個不對就回第 6 步改設定再跑一次。

## 8. 落地

全部方向都正確之後才放到地上。速度從 `SAFE_TEST_SPEED`（200）開始，
確認能穩定直線行駛再往上調。

```python
from carbot import Car

with Car() as car:
    car.move_for(1.0, 300, 300)   # 前進 1 秒後自動停
    car.move_for(0.6, -250, 250)  # 原地左轉
```

`Car` 是 context manager，離開 `with` 或程式出錯都會自動停車。

---

## 排錯

### `OSError: [Errno 121] Remote I/O error`

驅動板沒有正確回 ACK。原廠的 I2C 實作不檢查應答信號，Pi 的硬體 I2C 會檢查。

1. 先確認 `i2cdetect -y 1` 還看得到 `40`
2. 確認沒有把 I2C 速率調高過
3. 都正常還是失敗的話，改用軟體 I2C —— 在 `/boot/firmware/config.txt` 加：

   ```
   dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=23,i2c_gpio_scl=24
   ```

   接線改到 GPIO 23／24，程式改成 `NeZha(bus=3)`。

### `i2cdetect` 看不到 `40`

- 驅動板電源開了嗎？電源燈與固件燈亮著嗎？
- SDA／SCL 有沒有接反？（Pin 3 = SDA、Pin 5 = SCL）
- GND 有共地嗎？只接訊號線不接地是最常見的失敗原因
- 有插 PCA9685 的 HAT 嗎？它預設也是 `0x40`，會撞位址

### 編碼器一直回 0

正常。本車用的是兩線普通直流馬達，沒有編碼器。
`config.HAS_ENCODERS = False` 就是在講這件事。
換成 N20 編碼器馬達（6 線）後改成 `True`，並把編碼器線接到 MOTOR 接口的 4 孔側。

### 車子跑一跑突然停住 / Pi 重開

供電不足。量一下：

```bash
vcgencmd pmic_read_adc EXT5V_V && vcgencmd get_throttled
```

`get_throttled` 不是 `0x0` 就是有掉壓。馬達啟動瞬間的電流會把 5V 拉下去 ——
把測試速度降低，或改用獨立電源供 Pi（但**不能同時**接驅動板的 5V）。
