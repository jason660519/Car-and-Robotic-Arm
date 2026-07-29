# Raspberry Pi 官方文件

**唯讀。**

| 檔案 | 說明 |
|---|---|
| `RP-008248-DS-1-bcm2711-peripherals.pdf` | BCM2711 周邊裝置手冊 |

> ⚠️ BCM2711 是 **Raspberry Pi 4** 的 SoC。本專案用的是 **Pi 5（BCM2712）**，
> GPIO 控制器架構不同（Pi 5 的 GPIO 走 RP1 南橋）。這份文件對照 I2C／SPI
> 暫存器語意時仍有參考價值，但**腳位與時脈設定不要直接照抄**。
> Pi 5 的腳位對照見 [`docs/hardware/raspberry-pi-5-pinout.md`](../../docs/hardware/raspberry-pi-5-pinout.md)。

官方文件：<https://www.raspberrypi.com/documentation/computers/raspberry-pi.html>
