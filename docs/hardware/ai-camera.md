# Raspberry Pi AI Camera (IMX500) Model Guide

> Structure of this document:
> - **Part 1** — English guide (English only).
> - **Part 2** — Bilingual walkthrough (English + Traditional Chinese side by side, for bilingual learners).

Hardware: Raspberry Pi AI Camera with Sony IMX500 intelligent vision sensor (on-sensor NPU).

Sources:
- Model Zoo: <https://github.com/raspberrypi/imx500-models>
- Picamera2 demos: <https://github.com/raspberrypi/picamera2/tree/main/examples/imx500>

---

# Part 1 — English Guide

## 1.1 Quick Start

```bash
# Install the pre-trained models (already done on this Pi; run only if missing)
sudo apt install imx500-models

# Get the official demo scripts
git clone https://github.com/raspberrypi/picamera2.git
cd picamera2/examples/imx500

# Run a demo, e.g. object detection
python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_yolo11n_pp.rpk
```

All model files (`*.rpk`) live in `/usr/share/imx500-models/`.

## 1.2 Feature Overview

| Task | What it does | Models |
|---|---|---|
| Image Classification | Classify the whole image into one of 1000 ImageNet classes | 15 |
| Object Detection | Locate and classify multiple objects in a scene (COCO, 80 classes) | 6 |
| Semantic Segmentation | Classify every pixel of the image (PASCAL VOC, 20 classes) | 1 |
| Pose Estimation | Detect human body keypoints / skeleton (COCO KeyPoints) | 1 |

## 1.3 Image Classification

Task: categorize input into predefined classes with a confidence score.
Dataset: ImageNet (1000 classes). Demo script: `imx500_classification_demo.py`

| Model | Top-1 Acc. | Input | Command |
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

## 1.4 Object Detection

Task: identify and locate multiple objects with bounding boxes.
Dataset: COCO (80 classes). Demo script: `imx500_object_detection_demo.py`

| Model | mAP | Input | Command |
|---|---|---|---|
| YOLO11n (pp*) | 0.374 | 640×640 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_yolo11n_pp.rpk --bbox-normalization --bbox-order xy` |
| YOLOv8n (pp*) | 0.279 | 640×640 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_yolov8n_pp.rpk --bbox-normalization --bbox-order xy` |
| EfficientDet Lite-0 (pp*) | 0.252 | 320×320 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_efficientdet_lite0_pp.rpk` |
| NanoDet Plus | 0.332 | 416×416 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_nanodet_plus_416x416.rpk` |
| NanoDet Plus (pp*) | 0.320 | 416×416 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_nanodet_plus_416x416_pp.rpk` |
| SSD MobileNetV2 FPN Lite (pp*) | 0.218 | 320×320 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk` |

\* **pp** = post-processing is baked into the network and runs on the IMX500 itself, offloading the CPU.

## 1.5 Semantic Segmentation

Task: assign a category to every pixel of the image.
Dataset: PASCAL VOC (20 classes). Demo script: `imx500_segmentation_demo.py`

| Model | mIOU | Input | Command |
|---|---|---|---|
| DeepLabv3Plus | 0.721 | 320×320 | `python imx500_segmentation_demo.py --model /usr/share/imx500-models/imx500_network_deeplabv3plus.rpk` |

## 1.6 Pose Estimation

Task: detect human body keypoints (head, shoulders, elbows, knees…).
Dataset: COCO KeyPoints. Demo script: `imx500_pose_estimation_higherhrnet_demo.py`

| Model | mAP | Input | Command |
|---|---|---|---|
| HigherHRNet | 0.188 | 288×384 | `python imx500_pose_estimation_higherhrnet_demo.py --model /usr/share/imx500-models/imx500_network_higherhrnet_coco.rpk` |

## 1.7 Notes

1. **`pp` suffix**: post-processing is integrated into the network and executed on the IMX500 edge AI processor; the CPU is almost fully offloaded. Non-`pp` models do the post-processing on the Pi CPU.
2. **`imx500_network_inputtensoronly.rpk`**: debugging model that passes the input tensor through without inference.
3. **`rpk_update_network_intrinsics`**: official tool to update network intrinsics inside an `.rpk` (rarely needed).
4. **Licenses**: models use different open-source licenses (Apache-2.0 / MIT / BSD-3 / AGPL-3.0 / Apple Sample Code). See the official `imx500-models/LICENSES/` directory. Note AGPL-3.0 (YOLO family) before commercial use.
5. **rpicam-apps alternative** (same model files, no Picamera2 demo needed):
   `rpicam-hello -t 0 --model /usr/share/imx500-models/imx500_network_posenet.rpk --post-process-file /usr/share/rpi-camera-assets/imx500_posenet.json`
   (rpicam-apps v1.x installs post-process JSON under `/usr/share/rpi-camera-assets/`; confirm with `dpkg -L rpicam-apps | grep imx500`.)
6. **Typical uses**: pedestrian/vehicle detection (YOLO11n), gesture or object classification (EfficientNet family), obstacle segmentation (DeepLabv3Plus), action recognition (HigherHRNet) — all can be wired into this project's car / robotic arm.

---

# Part 2 — Bilingual Walkthrough / 中英對照講解

> Each section pairs an English explanation with the Traditional Chinese translation, so bilingual
> readers can compare. Model names and commands stay in English.
> 每一節都是「英文講解 + 繁體中文翻譯」並列，方便雙語讀者對照學習。模型名稱與指令維持英文原文。

## 2.1 Quick Start / 快速開始

**English** — Install the pre-trained models, clone the official demo scripts, and run a demo.
**中文** — 安裝官方預訓練模型，下載官方示範程式，然後執行示範。

```bash
# 1. Install the models / 安裝模型（本機已裝，缺檔才執行）
sudo apt install imx500-models

# 2. Get the demo scripts / 下載官方示範程式
git clone https://github.com/raspberrypi/picamera2.git
cd picamera2/examples/imx500

# 3. Run a demo, e.g. object detection / 執行示範（例：物體偵測）
python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_yolo11n_pp.rpk
```

**English** — All model files (`*.rpk`) live in `/usr/share/imx500-models/`.
**中文** — 所有模型檔（`.rpk`）都放在 `/usr/share/imx500-models/`。

## 2.2 Feature Overview / 功能總覽

| Task 功能 | What it does 做什麼 | Models 模型數 |
|---|---|---|
| Image Classification 影像分類 | Classify the whole image into 1000 ImageNet classes 判斷整張影像屬於哪一類（ImageNet 1000 類） | 15 |
| Object Detection 物體偵測 | Locate and classify multiple objects（COCO 80 classes）同時標出多個物體的位置與類別（COCO 80 類） | 6 |
| Semantic Segmentation 語意分割 | Classify every pixel（PASCAL VOC 20 classes）為每個像素分類（PASCAL VOC 20 類） | 1 |
| Pose Estimation 姿態估計 | Detect human body keypoints 偵測人體骨架關鍵點（COCO KeyPoints） | 1 |

## 2.3 Image Classification / 影像分類

**English** — Categorize the input image into a predefined class with a confidence score.
Suitable for scene recognition, material judgment, and simple classification.
**中文** — 判斷畫面內容，並附信心分數（confidence）。適合場景辨識、材質判斷、簡單分類。

**English** — Dataset: ImageNet（1000 classes）. Demo: `imx500_classification_demo.py`
**中文** — 訓練資料集：ImageNet（1000 類）。示範程式：`imx500_classification_demo.py`

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

## 2.4 Object Detection / 物體偵測

**English** — Identify and locate multiple objects in a scene with bounding boxes.
Suitable for people, vehicles, animals, etc.
**中文** — 同時標出畫面中多個物體的位置（bounding box）與類別，適合人、車、動物等偵測。

**English** — Dataset: COCO（80 classes）. Demo: `imx500_object_detection_demo.py`
**中文** — 訓練資料集：COCO（80 類）。示範程式：`imx500_object_detection_demo.py`

| Model 模型 | mAP 精度 | Input 輸入解析度 | Command 執行指令 |
|---|---|---|---|
| YOLO11n (pp*) | 0.374 | 640×640 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_yolo11n_pp.rpk --bbox-normalization --bbox-order xy` |
| YOLOv8n (pp*) | 0.279 | 640×640 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_yolov8n_pp.rpk --bbox-normalization --bbox-order xy` |
| EfficientDet Lite-0 (pp*) | 0.252 | 320×320 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_efficientdet_lite0_pp.rpk` |
| NanoDet Plus | 0.332 | 416×416 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_nanodet_plus_416x416.rpk` |
| NanoDet Plus (pp*) | 0.320 | 416×416 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_nanodet_plus_416x416_pp.rpk` |
| SSD MobileNetV2 FPN Lite (pp*) | 0.218 | 320×320 | `python imx500_object_detection_demo.py --model /usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk` |

\* **pp** — post-processing 後處理已包進網路，直接在 IMX500 上執行，CPU 幾乎完全解放。

## 2.5 Semantic Segmentation / 語意分割

**English** — Assign a category to every pixel of the image, giving a much finer result than
bounding boxes. Useful for autonomous driving and obstacle avoidance pre-processing.
**中文** — 對畫面**每個像素**分類（哪些是天空、路面、人、車…），比偵測框更精細，適合自駕、避障前處理。

**English** — Dataset: PASCAL VOC（20 classes）. Demo: `imx500_segmentation_demo.py`
**中文** — 訓練資料集：PASCAL VOC（20 類）。示範程式：`imx500_segmentation_demo.py`

| Model 模型 | mIOU 精度 | Input 輸入解析度 | Command 執行指令 |
|---|---|---|---|
| DeepLabv3Plus | 0.721 | 320×320 | `python imx500_segmentation_demo.py --model /usr/share/imx500-models/imx500_network_deeplabv3plus.rpk` |

## 2.6 Pose Estimation / 姿態估計

**English** — Detect human body keypoints (head, shoulders, elbows, knees…).
Can feed skeleton animation, gesture recognition, or fall detection.
**中文** — 偵測人體關節關鍵點（頭、肩、肘、膝…），可接骨架動畫、動作辨識、跌倒偵測等。

**English** — Dataset: COCO KeyPoints. Demo: `imx500_pose_estimation_higherhrnet_demo.py`
**中文** — 訓練資料集：COCO KeyPoints。示範程式：`imx500_pose_estimation_higherhrnet_demo.py`

| Model 模型 | mAP 精度 | Input 輸入解析度 | Command 執行指令 |
|---|---|---|---|
| HigherHRNet | 0.188 | 288×384 | `python imx500_pose_estimation_higherhrnet_demo.py --model /usr/share/imx500-models/imx500_network_higherhrnet_coco.rpk` |

## 2.7 Notes / 附註

1. **`pp` 後綴**
   **English** — Post-processing is integrated into the network and runs on the IMX500 edge AI processor; the CPU is almost fully offloaded. Non-`pp` models do post-processing on the Pi CPU.
   **中文** — 該模型已把後處理整合進網路，直接在 IMX500 上執行，CPU 幾乎完全解放；無 `pp` 的版本後處理由樹莓派 CPU 做。

2. **`imx500_network_inputtensoronly.rpk`**
   **English** — Debugging model that passes the input tensor through without inference.
   **中文** — 不做推理、直接把輸入張量回傳的測試用模型，通常只給開發者除錯。

3. **`rpk_update_network_intrinsics`**
   **English** — Official tool to update network intrinsics inside an `.rpk` (rarely needed).
   **中文** — 官方工具，用於更新 `.rpk` 內的網路 intrinsics（一般不常用）。

4. **Licenses 授權**
   **English** — Models use different open-source licenses (Apache-2.0 / MIT / BSD-3 / AGPL-3.0 / Apple Sample Code); see `imx500-models/LICENSES/`. Note AGPL-3.0 (YOLO family) before commercial use.
   **中文** — 模型各自採用不同開源授權（Apache-2.0 / MIT / BSD-3 / AGPL-3.0 / Apple Sample Code），以官方 `imx500-models/LICENSES/` 目錄為準；YOLO 系列為 AGPL-3.0，商用前需注意。

5. **rpicam-apps alternative / 命令列替代方式**
   **English** — Same model files, no Picamera2 demo needed:
   **中文** — 不走 Picamera2 demo 也行，模型檔相同：
   ```bash
   rpicam-hello -t 0 --model /usr/share/imx500-models/imx500_network_posenet.rpk --post-process-file /usr/share/rpi-camera-assets/imx500_posenet.json
   ```
   **English** — rpicam-apps v1.x installs post-process JSON under `/usr/share/rpi-camera-assets/`; confirm with `dpkg -L rpicam-apps | grep imx500`.
   **中文** — 新版 rpicam-apps v1.x 的 post-process JSON 在 `/usr/share/rpi-camera-assets/`，可先 `dpkg -L rpicam-apps | grep imx500` 確認路徑。

6. **Typical uses / 常見用途**
   **English** — Pedestrian/vehicle detection (YOLO11n), gesture or object classification (EfficientNet family), obstacle segmentation (DeepLabv3Plus), action recognition (HigherHRNet) — all can be wired into this project's car / robotic arm.
   **中文** — 行人／車輛偵測（YOLO11n）、手勢或物體分類（EfficientNet 系列）、地圖分割避障（DeepLabv3Plus）、動作辨識（HigherHRNet）——這些都能直接接到本專案的小車／機械臂上。
