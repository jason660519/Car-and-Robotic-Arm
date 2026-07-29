# 37 合 1 感測器套件原廠資料

**唯讀。**

## 來源

隨 37-in-1 感測器套件附贈的原廠光碟內容。模組實體照片在
[`assets/inventory/`](../../assets/inventory/)，可瀏覽的清單在
[`site/inventory/`](../../site/inventory/)。

## 內容

| 路徑 | 說明 |
|---|---|
| `arduino/` | 各模組的 Arduino 範例（`.pde` / `.ino`）與原理圖 PDF |
| `stm32/` | 各模組的 STM32 Keil 專案與接線說明 |

## 匯入時剔除了什麼

2026-07-30 整理時刪除了 **5,838 個 Keil 編譯產物**（`.o` `.crf` `.d` `.lst`
`.dep` `.map` `.axf` `.uvoptx` `.htm` build log 等），約 1GB。
這些全部可以用 Keil 從保留下來的 `.c` / `.h` / `.uvprojx` 重建。

保留：原始碼、專案檔、`.hex` 燒錄檔、原理圖 PDF、接線說明。
