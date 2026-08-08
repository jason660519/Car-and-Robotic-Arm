# Raspberry Pi AI Camera (IMX500) — Model Guide / 使用說明

> This guide lists every official pre-trained neural network model that ships with the
> `imx500-models` package and explains what the AI Camera can do with it.
> 本文件列出官方 `imx500-models` 套件內建的全部預訓練模型，說明這顆 AI Camera 可以做哪些 AI 功能。

Hardware: Raspberry Pi AI Camera with Sony IMX500 intelligent vision sensor (on-sensor NPU).
硬體：Raspberry Pi AI Camera，搭載 Sony IMX500 智慧影像感測器（內建 NPU，AI 推理直接在相機上執行，
不佔用樹莓派 CPU）。

Sources / 資料來源：
- Model Zoo: <https://github.com/raspberrypi/imx500-models>
- Picamera2 demos: <https://github.com/raspberrypi/picamera2/tree/main/examples/imx500>

---

## Quick Start / 快速開始

```bash
# 1. Install the models (already done on this Pi, run only if missing)
# 1. 安裝模型（本機已裝，缺檔才執行）
sudo apt install imx500-models

# 2. Get the Picamera2 demo scripts / 下載官方程式
git clone https://github.com/raspberrypi/picamera2.git
cd picamera2/examples/imx500

# 3. Run a demo, e.g. object detection / 執行示範（例：物體偵測）
python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_yolo11n_pp.rpk
```

All model files live in `/usr/share/imx500-models/` (`*.rpk`).
所有模型檔位於 `/usr/share/imx500-models/`（副檔名 `.rpk`）。

---

## Feature Overview / 功能總覽

| Task 功能 | What it does 做什麼 | # Models 模型數 |
|---|---|---|
| Image Classification 影像分類 | 判斷整張影像屬於哪一類（ImageNet 1000 類） | 15 |
| Object Detection 物體偵測 | 同時標出畫面中多個物體的位置與類別（COCO 80 類） | 6 |
| Semantic Segmentation 語意分割 | 為畫面每個像素分類（PASCAL VOC 20 類） | 1 |
| Pose Estimation 姿態估計 | 偵測人體骨架關鍵點（COCO KeyPoints） | 1 |

---

## 1. Image Classification / 影像分類

Task: 判斷畫面內容，附信心分數（confidence）。Input: 單張影像。適用：場景辨識、材質判斷、簡單分類。
Dataset: ImageNet（1000 類）。Demo script: `imx500_classification_demo.py`

| Model 模型 | Top-1 Acc. 精度 | Input 輸入解析度 | Command 執行指令 |
|---|---|---|---|
| EfficientNet-B0 | 72.1% | 224×224 | `python imx500_classification_demo.py --model /usr/share/imx500-models/imx500_network_efficientnet_bo.rpk` |
| EfficientNet Lite-0 | 75.3% | 224×224 | `python imx500_classification_demo.py --model /usr/share/imx500-models/imx500_network_efficientnet_lite0.rpk` |
| EfficientNetV2-B0 | 76.7% | 224×224 | `python imx500_classification_demo.py --model /usr/share/imx500-models/imx500_network_efficientnetv2_b0.rpk` |
| EfficientNetV2-B1 | 77.0% | 240×240 | `python imx500_classification_demo.py --model /usr/share/imx500-models/imx500_network_efficientnetv2_b1.rpk` |
| EfficientNetV2-B2 | 77.7% | 260×260 | `python imx500_classification_demo.py --model /usr/share/imx500-models/imx500_network_efficientnetv2_b2.rpk` |
| MnasNet1.0 | 73.2% | 224×224 | `python imx500_classification_demo.py --model /usr/share/imx500-models/imx500_network_mnasnet1.0.rpk` |
| MobileNetV2 | 71.6% | 224×224 | `python imx500_classification_demo.py --model /usr/share/imx500-models/imx500_network_mobilenet_v2.rpk` |
| MobileViT-XS | 72.3% | 256×256 | `python imx500_classification_demo.py --model /usr/share/imx500-models/imx500_network_mobilevit_xs.rpk` |
| MobileViT-XXS | 67.4% | 256×256 | `python imx500_classification_demo.py --model /usr/share/imx500-models/imx500_network_mobilevit_xxs.rpk` |
| RegNetX-002 | 68.4% | 224×224 | `python imx500_classification_demo.py --model /usr/share/imx500-models/imx500_network_regnetx_002.rpk` |
| RegNetY-002 | 69.4% | 224×224 | `python imx500_classification_demo.py --model /usr/share/imx500-models/imx500_network_regnety_002.rpk` |
| RegNetY-004 | 73.8% | 224×224 | `python imx500_classification_demo.py --model /usr/share/imx500-models/imx500_network_regnety_004.rpk` |
| ResNet-18 | 68.6% | 224×224 | `python imx500_classification_demo.py --model /usr/share/imx500-models/imx500_network_resnet18.rpk` |
| ShuffleNetV2-x1.5 | 72.2% | 224×224 | `python imx500_classification_demo.py --model /usr/share/imx500-models/imx500_network_shufflenet_v2_x1_5.rpk` |
| SqueezeNet-V1.0 | 57.6% | 224×224 | `python imx500_classification_demo.py --model /usr/share/imx500-models/imx500_network_squeezenet1.0.rpk` |

---

## 2. Object Detection / 物體偵測

Task: 同時標出畫面中多個物體的位置（bounding box）與類別，適合人、車、動物等偵測。
Dataset: COCO（80 類）。Demo script: `imx500_object_detection_demo.py`

| Model 模型 | mAP 精度 | Input 輸入解析度 | Command 執行指令 |
|---|---|---|---|
| YOLO11n (pp*) | 0.374 | 640×640 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_yolo11n_pp.rpk --bbox-normalization --bbox-order xy` |
| YOLOv8n (pp*) | 0.279 | 640×640 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_yolov8n_pp.rpk --bbox-normalization --bbox-order xy` |
| EfficientDet Lite-0 (pp*) | 0.252 | 320×320 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_efficientdet_lite0_pp.rpk` |
| NanoDet Plus | 0.332 | 416×416 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_nanodet_plus_416x416.rpk` |
| NanoDet Plus (pp*) | 0.320 | 416×416 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_nanodet_plus_416x416_pp.rpk` |
| SSD MobileNetV2 FPN Lite (pp*) | 0.218 | 320×320 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk` |

\* **pp** = post-processing（非極大值抑制等後處理）已包進網路，直接在 IMX500 上執行，CPU 負擔更小。

---

## 3. Semantic Segmentation / 語意分割

Task: 對畫面**每個像素**分類（哪些是天空、路面、人、車…），比偵測框更精細，適合自駕、避障前處理。
Dataset: PASCAL VOC（20 類）。Demo script: `imx500_segmentation_demo.py`

| Model 模型 | mIOU 精度 | Input 輸入解析度 | Command 執行指令 |
|---|---|---|---|
| DeepLabv3Plus | 0.721 | 320×320 | `python imx500_segmentation_demo.py --model /usr/share/imx500-models/imx500_network_deeplabv3plus.rpk` |

---

## 4. Pose Estimation / 姿態估計

Task: 偵測人體關節關鍵點（頭、肩、肘、膝…），可接骨架動畫、動作辨識、跌倒偵測等。
Dataset: COCO KeyPoints。Demo script: `imx500_pose_estimation_higherhrnet_demo.py`

| Model 模型 | mAP 精度 | Input 輸入解析度 | Command 執行指令 |
|---|---|---|---|
| HigherHRNet | 0.188 | 288×384 | `python imx500_pose_estimation_higherhrnet_demo.py --model /usr/share/imx500-models/imx500_network_higherhrnet_coco.rpk` |

---

## Notes / 附註

1. **`pp` 後綴**：該模型已把後處理整合進網路（在 IMX500 上執行），CPU 幾乎完全解放；無 `pp` 的版本後處理由樹莓派 CPU 做。
2. **`imx500_network_inputtensoronly.rpk`**：不做推理、直接把輸入張量回傳的測試用模型，通常只給開發者除錯。
3. **`rpk_update_network_intrinsics`**：官方工具，用於更新 `.rpk` 內的網路 intrinsics（一般不常用）。
4. **授權**：模型各自採用不同開源授權（Apache-2.0 / MIT / BSD-3 / AGPL-3.0 / Apple Sample Code），以官方
   `imx500-models/LICENSES/` 目錄為準；AGPL-3.0（YOLO 系列）商用前需注意。
5. **rpicam-apps 也能跑**（不走 Picamera2 demo 也行，模型檔相同）：
   `rpicam-hello -t 0 --model /usr/share/imx500-models/imx500_network_posenet.rpk --post-process-file /usr/share/rpi-camera-assets/imx500_posenet.json`
   （新版 rpicam-apps v1.x 的 post-process JSON 在 `/usr/share/rpi-camera-assets/`，可先 `dpkg -L rpicam-apps | grep imx500` 確認路徑）
6. **常見用途**：行人／車輛偵測（YOLO11n）、手勢或物體分類（EfficientNet 系列）、地圖分割避障（DeepLabv3Plus）、
   動作辨識（HigherHRNet）——這些都能直接接到本專案的小車／機械臂上。
