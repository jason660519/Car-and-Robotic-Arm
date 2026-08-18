# Map1 IR Sensor Tracking — Quick Start

三個階段，~10 分鐘。你在機器人旁邊能切斷電源。

---

## 前置條件

```bash
# SSH 到樹莓派，進入專案目錄
cd /Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm
```

---

## ✅ Phase 1: IR Sensor Check (~2 min)

**不需要馬達，不需要移動車子。**

在發車區附近，手拿傳感器在黑線上測試：

```bash
scripts/map1-phase1-ir-check.sh
```

等同於（在 repo 根目錄執行）：

```bash
PYTHONPATH=src python3 examples/36_ir_tracing_check.py --pins 24,25,22,23 --invert 0,1,2,3
```

**預期：**
- 黑線上方：`1 1 1 1` ✓
- 白色紙上：`0 0 0 0` ✓

`--invert 0,1,2,3` 是 2026-08-18 電位器重調後驗證的設定，見
[docs/hardware/ir-tracing-sensor.md](../../docs/hardware/ir-tracing-sensor.md)。
極性在每次重調電位器後都可能翻轉，動過電位器就要重跑這個檢查。

Ctrl+C 停止。

---

## ✅ Phase 2: Motor Test (~3 min)

🔴 **先抬起所有 4 個輪子或用卡具固定底盤！**

```bash
PYTHONPATH=src python3 examples/37_map1_motor_test.py
```

會依序測試：
1. 前進 2 秒
2. 後退 2 秒
3. 左轉 2 秒
4. 右轉 2 秒
5. 左旋 1.5 秒
6. 右旋 1.5 秒

檢查輪子轉向是否符合預期，然後 Ctrl+C 停止。

---

## ✅ Phase 3: Full IR Tracking (~2 min)

🟢 **輪子放地上，車子在發車區起始位置。**

### 先試試看不開馬達（純檢測）

```bash
PYTHONPATH=src python3 examples/39_map1_ir_line_follow.py \
  --dry-run --duration 30
```

如果有錯誤會立刻看到，不會動馬達。

### 實際跑（操作者站在機器人旁邊）

```bash
PYTHONPATH=src python3 examples/39_map1_ir_line_follow.py \
  --speed 150 --turn-gain 2.0 --duration 120
```

**監控輸出：**
```
[  0.0s] #   1 OK   1111 err=+0.00 -> L150 R150
[  0.5s] #   2 OK   1110 err=+0.25 -> L130 R150
[  1.0s] #   3 OK   1111 err=-0.00 -> L150 R150
```

`OK` = 線被檢測到  
`LOST` = 線丟失（應該會自動恢復）  
`1111` / `1110` / `0111` 等 = 4 個 IR 通道的讀數

---

## 如果需要調參

| 問題 | 調整 |
|------|------|
| 蛇形振盪（過度轉向） | `--turn-gain 1.5` |
| 漂移脫線（轉向不足） | `--turn-gain 2.5` 或 `--speed 120` |
| 經常丟線 | 調整 IR 傳感器高度 (1-2cm above paper) |

重新運行，參數改在命令行：

```bash
PYTHONPATH=src python3 examples/39_map1_ir_line_follow.py \
  --speed 120 --turn-gain 2.5 --duration 120
```

---

## 成功條件

✅ Phase 1: 黑線讀 1，白色讀 0  
✅ Phase 2: 馬達方向都對  
✅ Phase 3: 車子跟著線走，完成 80% 以上的圓圈  

完成！

---

## 有問題？

- **IR 傳感器讀數異常** → 看 Phase 1 輸出，可能需要調高度或亮度
- **馬達不動** → 確認輪子沒有卡，檢查 GPIO 接線
- **車子一直漂移** → 降低 `--speed` 或增加 `--turn-gain`
- **線完全丟失** → Ctrl+C 停止，重新放在發車區，檢查黑線是否清晰

更詳細的故障排除見 [`map1-ir-tracking-plan.md`](map1-ir-tracking-plan.md)
