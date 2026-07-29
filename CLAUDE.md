# Car and Robotic Arm — AI agent 工作規則

## 動手前必讀

**[CONVENTIONS.md](CONVENTIONS.md) 是檔案擺放與命名的單一真實來源。**
新增或搬動任何檔案前先讀它。與現況衝突時，是現況要改。

## 專案性質

實體機器人專案，程式跑在 Raspberry Pi 5 上，透過 I2C 控制 NeZha 驅動板。
**改動會讓真實硬體動起來**，錯誤的指令可能燒板子或讓車子撞牆。

## 硬規則

1. **`vendor/` 唯讀。** 要改原廠程式碼，複製到 `src/` 或 `scripts/` 再改，
   原始檔留著當對照組。
2. **馬達相關的改動不要憑推測。** I2C 協定以
   [docs/hardware/nezha-i2c-protocol.md](docs/hardware/nezha-i2c-protocol.md) 為準，
   該文件的來源是 `vendor/yourfun-nezha/sdk/` 的原廠驅動原始碼。
3. **不要幫使用者跑會讓馬達轉的程式。** 產生程式碼、說明怎麼跑即可，
   實際通電由使用者決定時機。
4. **不要主動 commit / push。**
5. 硬體實測步驟以 [docs/setup/raspberry-pi-first-run.md](docs/setup/raspberry-pi-first-run.md)
   為準，不要自己另發明一套順序。
6. 照片編號不重用、不重排（CONVENTIONS.md §3.3）。

## 已知地雷

| 項目 | 說明 |
|---|---|
| I2C 位址 `0x40` | 與 PCA9685 預設位址相同。若 Pan-Tilt HAT 同時上線會撞位址 |
| I2C 速率 | 不得超過 200kHz。Pi 預設 100kHz，別動 |
| 雙電源 | NeZha 餵 5V 給 Pi 時，不可同時接 Pi 的 USB-C |
| 正反轉方向 | 原廠手冊與程式碼註解對 `motor_a` / `motor_b` 的說法相反，以實測為準 |
| 上電延時 | init 後 500ms、reset 後 100ms，原廠標註不可省 |

## 工具

- Python：**uv**（不用 pip / poetry）
- 前端：見 [docs/adr/](docs/adr/)
