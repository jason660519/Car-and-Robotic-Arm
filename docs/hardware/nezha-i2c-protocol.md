# NeZha 驅動板 I2C 協定

有方機器人 NeZha（哪吒）總線驅動板的完整 I2C 指令集。

**來源**：`vendor/yourfun-nezha/sdk/` 的原廠 STM32／Arduino／C51 驅動庫原始碼，
與 `vendor/yourfun-nezha/manual/` 的官方使用手冊（V1.0.0, 2023-11-27）。
原廠沒有出獨立的協定文件，本文是從驅動原始碼反推整理的。

Python 實作見 [`src/carbot/nezha.py`](../../src/carbot/nezha.py)。

## 位址

| 項目 | 值 |
|---|---|
| 7-bit 位址（Linux / `i2cdetect` 顯示的） | **`0x40`** |
| 原廠 `NEZHA_ADDR` | `0x80`（8-bit 寫入位址，`0x80 >> 1 == 0x40`） |
| 讀取位址 | `0x81`（`NEZHA_ADDR \| 0x01`） |

> ⚠️ `0x40` 也是 **PCA9685 的原廠預設位址**。本專案的 Waveshare Pan-Tilt HAT 與
> PCA9685 Servo Driver HAT 都用這個位址，**同時上線會撞位址**，必須改 HAT 的 A0–A5 跳線。

## 傳輸格式

所有指令都寫進**命令暫存器 `0x00`**。需要帶參數的指令，在寫完命令暫存器之後
**再送一個獨立的資料 frame**，frame 的第一個 byte 是指令碼本身。

```
無參數指令：  START  0x80  0x00  <cmd>  STOP
帶參數指令：  START  0x80  0x00  <cmd>  STOP
              START  0x80  <cmd>  <data...>  STOP
讀取指令：    START  0x80  <cmd>  RESTART  0x81  <hi>  <lo>  STOP
```

分兩次送是原廠實作的行為，不要合併。對應到 Linux SMBus：

| 動作 | smbus2 呼叫 |
|---|---|
| 無參數指令 | `write_byte_data(0x40, 0x00, cmd)` |
| 帶參數指令 | 先同上，再 `write_i2c_block_data(0x40, cmd, data)` |
| 讀取 | `read_i2c_block_data(0x40, cmd, 2)` |

## 指令表

### 系統

| 指令 | 碼 | 參數 |
|---|---|---|
| Reset | `0xFF` | 無。送完必須 **sleep 100ms** |
| 馬達初始化 | `0x01` | 無 |

### 馬達 M1–M4

| 接口 | 設定速度 |
|---|---|
| M1 | `0x05` |
| M2 | `0x09` |
| M3 | `0x0D` |
| M4 | `0x11` |

參數 4 bytes：`[motor_a_hi, motor_a_lo, motor_b_hi, motor_b_lo]`

- 兩個值各自範圍 **0–1000**，占空比 = 值 / 1000
- **`motor_a` 與 `motor_b` 不可同時有值**，手冊列為無效組合
- 控制訊號頻率 100Hz，韌體寫死不可改

### 編碼器

| 接口 | 初始化 | 讀取 |
|---|---|---|
| M1 | `0x15` | `0x16` |
| M2 | `0x18` | `0x19` |
| M3 | `0x1B` | `0x1C` |
| M4 | `0x1E` | `0x1F` |

讀回 2 bytes，big-endian **有號 int16**，正負代表轉向。
採樣週期 20ms，韌體寫死不可改。用之前要先初始化。

### 舵機 S1–S4

| 接口 | 初始化 | 設定 PWM |
|---|---|---|
| S1 | `0x21` | `0x22` |
| S2 | `0x24` | `0x25` |
| S3 | `0x27` | `0x28` |
| S4 | `0x2A` | `0x2B` |

參數 2 bytes：`[pwm_hi, pwm_lo]`，PWM 範圍 **50–250**，線性對應 0°–180°
（180° 模擬舵機）。每個接口用之前都要單獨初始化。

舵機接線（由外往內）：`GND` / `5V` / `Sx 訊號`。舵機線是棕=GND、紅=VCC、黃=PWM。

### 燈

| 燈 | 開 | 關 | 翻轉 |
|---|---|---|---|
| 前燈 | `0x2D` | `0x2E` | `0x2F` |
| 左尾燈 | `0x30` | `0x31` | `0x32` |
| 右尾燈 | `0x33` | `0x34` | `0x35` |
| 氛圍燈 | `0x36` | `0x37` | `0x38` |

## 樹莓派上的四個地雷

### 1. I2C 速率上限 200kHz

原廠 `NeZha_I2C.c` 明文寫著：

> NeZha(哪吒)驅動板 I2C 通信速率不得高於 200KHz……過高的通信速率可能會導致主控系統與驅動板通信失敗

Pi 預設 100kHz，**不要**去 `/boot/firmware/config.txt` 設 `dtparam=i2c_arm_baudrate=400000`。

### 2. 上電延時不可省

原廠在兩處標了「不可去掉」：I2C 初始化後 **500ms**、reset 後 **100ms**。

### 3. 原廠實作不檢查 ACK

`NeZha_I2C_SendByte()` 的註解直接寫「額外的一個時鐘，**不處理應答信號**」，
而且讀取時連最後一個 byte 都回 ACK（正規 I2C 主機應該 NACK）。

Pi 的**硬體** I2C controller 是會檢查 ACK 的。`i2cdetect` 掃得到 `0x40`
代表位址層有正常 ACK，資料層通常也沒事。萬一出現：

```
OSError: [Errno 121] Remote I/O error
```

原因就在這裡。退路是用軟體 I2C：在 `/boot/firmware/config.txt` 加

```
dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=23,i2c_gpio_scl=24
```

### 4. 禁止雙電源

手冊警告第 2 條：驅動板的 5V 餵給主控時，**切勿再使用其他電源給主控供電**。
用 NeZha 的 5V 接 Pi 的 Pin 2/4 時，就不能同時插 Pi 的 USB-C。

## 正反轉的矛盾 ⚠️

手冊與原廠程式碼註解對 `motor_a` / `motor_b` 的說法**互相矛盾**：

| 來源 | 說法 |
|---|---|
| 使用手冊 P.13 | 「`motor_a` 控制電機**正轉**，`motor_b` 控制電機反轉」 |
| `NeZha.c` 函式註解 | 「`motor_a`：電機**反轉**……`motor_b`：電機正轉」 |

送出的 byte 順序兩邊一致，差別只在解讀，所以**只能實測**。
跑 `examples/02_motor_check.py`，結果不對就把 `src/carbot/nezha.py` 的
`FORWARD_IS_MOTOR_A` 翻過來。

（手冊定義的正轉是右手法則：右手握住電機、拇指指向轉軸，四指方向為正轉。）

## 硬體接口速查

- **12V 電池接口** —— 必須 12V，接反會燒板。電源指示燈熄滅要立刻斷電
- **I2C 接口**（由右往左）：`5V` / `SCL` / `SDA` / `GND`
- **MOTOR 接口 ×4** —— 每個分成 **2 孔（馬達電源）** 與 **4 孔（編碼器）** 兩部分。
  ⚠️ 馬達的 2 孔接頭插進 4 孔接口會燒板
- **舵機接口 ×4** —— 右側標 `NC` 的是空接口，不能當舵機用
- **5V 電源接口 ×3** —— 給其他外設用
- **固件指示燈** —— 長亮表示韌體正常；熄滅代表韌體損壞，板子功能全失效
