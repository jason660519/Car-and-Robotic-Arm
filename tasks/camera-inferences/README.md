# Camera Inferences

這個資料夾純粹方便你(Jason)在 Mac 上找東西 —— 真正會在 Pi 上執行的程式碼一定要放在
`examples/`(見專案根目錄的 `CONVENTIONS.md` 與
`docs/setup/mac-to-raspberry-pi-access.md`),否則不會同步到 Pi、也跑不起來。

> **注意**:本資料夾**有**被 git 追蹤(原本這裡寫「不受 git 追蹤」是錯的)。因此下方
> 「看過即可、不需要進 repo」的東西實際上都會進版控,牴觸 CONVENTIONS §7 —— 那類檔案
> 應該放在被 ignore 的 `scratch/`。目前已追蹤的圖檔留在原地待決定,見
> `docs/progress/2026-08-19-tasks-directory-conventions.md`。

## 腳本本體

[`examples/35_cam_object_id_check.py`](../../examples/35_cam_object_id_check.py)

在 Pi 上跑:

```bash
PYTHONPATH=src python3 examples/35_cam_object_id_check.py
```

量測 IMX500 on-sensor 物件偵測(SSD MobileNetV2 FPN-Lite,這台 Pi 上沒裝 YOLO)辨識一次的時間
(camera cold start / 每幀延遲)與信心分數,取代原本誤把 `05_ai_camera_check.py --inference`
的 120 秒 soak-test 時間當成單次判斷耗時的認知。

## 這裡放什麼

- 拍照結果、跑分紀錄之類「看過即可、不需要進 repo」的東西
- `2026-08-17-front-object-detection-check.jpg` — 2026-08-17 用 `carpi` 拍的測試照(可樂罐、香蕉、橘子),
  用來驗證要不要裝物件辨識軟體
