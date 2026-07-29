# Car and Robotic Arm

樹莓派驅動的四輪小車 + 三自由度機械臂。

底盤與機械臂由**有方機器人 NeZha（哪吒）總線驅動板**驅動，Raspberry Pi 5 透過
I2C（位址 `0x40`）下指令控制 4 顆馬達、4 個舵機與板載燈效，並讀取編碼器轉速。

## 硬體

| 項目 | 型號 |
|---|---|
| 主控 | Raspberry Pi 5 |
| 驅動板 | 有方機器人 NeZha 總線驅動板（I2C `0x40`） |
| 底盤 | 大聖多形態小車（ABS 材質），N20 馬達 ×4 |
| 機械臂 | 桌面級 3 自由度 |
| 電池 | HXS 18650 11.1V 1200mAh |

## 快速開始

```bash
uv sync
```

在樹莓派上確認驅動板有回應：

```bash
uv run python examples/01_i2c_probe.py
```

## 這個 repo 有什麼

| 路徑 | 內容 |
|---|---|
| [CONVENTIONS.md](CONVENTIONS.md) | **檔案擺放與命名規範 — 動手前先看這份** |
| [docs/hardware/](docs/hardware/) | NeZha I2C 協定、Raspberry Pi 5 腳位、整合筆記 |
| [docs/setup/](docs/setup/) | 環境建置步驟 |
| [src/carbot/](src/carbot/) | Python 驅動與設定 |
| [examples/](examples/) | 可直接跑的示範腳本 |
| [site/](site/) | Astro 網站原始碼（專案報告、零件庫存、組裝指南） |
| [assets/](assets/) | 零件照、組裝照、參考圖 |
| [vendor/](vendor/) | 原廠資料（唯讀） |

## 網頁

```bash
npm install && npm run dev
```

<http://localhost:4321/Car-and-Robotic-Arm/> —— 專案總覽、零件庫存、組裝指南，
中英雙語（英文在 `/en/`）。架構決策見
[ADR 0001](docs/adr/0001-static-site-architecture.md)。

## 安全注意事項

- 驅動板需 **12V** 供電，正負極接反會燒板
- 驅動板的 5V 可以餵 Pi（Pin 2/4），但**此時絕對不可同時接 Pi 的 USB-C 電源** ——
  原廠手冊明文禁止雙電源
- I2C 速率**不得超過 200kHz**。Pi 預設 100kHz，不要去調 `i2c_arm_baudrate`
- 第一次跑馬達請把車架空
