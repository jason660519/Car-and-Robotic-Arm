#!/usr/bin/env python3
"""IMX500 object-detection check for visual obstacle avoidance (no motors).

Loads an on-sensor object detector (SSD mobilenetv2, COCO 80 classes) and
prints every detection plus an "OBSTACLE AHEAD" flag when a large object sits
in the central lower part of the frame — the car's path. This is the visual
layer that will later be fused with the sonar (e.g. a chair/table the sonar
cannot see).

Run on the Pi while the operator places/removes obstacles in front of the car:

    PYTHONPATH=src python3 examples/20_visual_detection_check.py --frames 30

Models available on this Pi:
    /usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk
    /usr/share/imx500-models/imx500_network_nanodet_plus_416x416_pp.rpk
"""

from __future__ import annotations

import argparse
import sys
import time

import numpy as np
from picamera2 import Picamera2
from picamera2.devices import IMX500
from picamera2.devices.imx500 import NetworkIntrinsics, postprocess_nanodet_detection

DEFAULT_MODEL = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"

# COCO classes most relevant to indoor obstacles; used only if the model
# carries no labels of its own.
COCO_LABELS = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
    "toothbrush",
]


def parse_detections(metadata, imx500, intrinsics, threshold, iou, max_detections, picam2):
    """Return a list of (category, conf, box_x, box_y, box_w, box_h) in pixels."""
    np_outputs = imx500.get_outputs(metadata, add_batch=True)
    if np_outputs is None:
        return []
    input_w, input_h = imx500.get_input_size()

    if intrinsics.postprocess == "nanodet":
        boxes, scores, classes = postprocess_nanodet_detection(
            outputs=np_outputs[0], conf=threshold, iou_thres=iou, max_out_dets=max_detections
        )[0]
        from picamera2.devices.imx500.postprocess import scale_boxes
        boxes = scale_boxes(boxes, 1, 1, input_h, input_w, False, False)
    else:
        boxes, scores, classes = np_outputs[0][0], np_outputs[1][0], np_outputs[2][0]
        if intrinsics.bbox_normalization:
            boxes = boxes / input_h
        if intrinsics.bbox_order == "xy":
            boxes = boxes[:, [1, 0, 3, 2]]

    results = []
    for box, score, category in zip(boxes, scores, classes):
        if score <= threshold:
            continue
        # box is [y0, x0, y1, x1] (normalized); convert returns pixel (x, y, w, h)
        coords = np.asarray(box, dtype=np.float64)
        x, y, w, h = imx500.convert_inference_coords(coords, metadata, picam2)
        results.append((int(category), float(score), int(x), int(y), int(w), int(h)))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="IMX500 visual obstacle detection check")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--frames", type=int, default=30, help="frames to analyse")
    parser.add_argument("--interval", type=float, default=1.0, help="seconds between reads")
    parser.add_argument("--threshold", type=float, default=0.30, help="detection confidence threshold")
    parser.add_argument("--iou", type=float, default=0.65)
    parser.add_argument("--max-detections", type=int, default=10)
    parser.add_argument("--center-x", type=float, default=0.35,
                        help="obstacle if the box centre x is within this fraction of frame centre")
    parser.add_argument("--min-height-frac", type=float, default=0.45,
                        help="obstacle if the box bottom is below this fraction of frame height")
    parser.add_argument("--min-area-frac", type=float, default=0.06,
                        help="obstacle only if the box covers at least this fraction of the frame")
    args = parser.parse_args()

    imx500 = IMX500(args.model)
    intrinsics = imx500.network_intrinsics
    if not intrinsics:
        intrinsics = NetworkIntrinsics()
        intrinsics.task = "object detection"
    if intrinsics.task != "object detection":
        print(f"Model is not an object-detection network (task={intrinsics.task})", file=sys.stderr)
        return 1
    labels = intrinsics.labels or COCO_LABELS
    intrinsics.update_with_defaults()

    picam2 = Picamera2(imx500.camera_num)
    config = picam2.create_preview_configuration(
        controls={"FrameRate": intrinsics.inference_rate}, buffer_count=12
    )
    imx500.show_network_fw_progress_bar()
    picam2.start(config)
    main_size = picam2.camera_configuration()["main"]["size"]
    fw, fh = main_size
    time.sleep(1.0)

    print(f"Visual detection check: {args.frames} reads, model={args.model.split('/')[-1]}")
    print("=" * 60)
    try:
        for i in range(args.frames):
            metadata = picam2.capture_metadata()
            dets = parse_detections(metadata, imx500, intrinsics,
                                    args.threshold, args.iou, args.max_detections, picam2)
            obstacle = False
            for cat, conf, x, y, w, h in dets:
                name = labels[cat] if cat < len(labels) else str(cat)
                cx = x + w / 2
                bottom = y + h
                area = (w * h) / (fw * fh)
                central = abs(cx - fw / 2) < args.center_x * fw
                low = bottom > args.min_height_frac * fh
                if central and low and area > args.min_area_frac:
                    obstacle = True
                print(f"  {name:14s} conf={conf:.2f} box=({x},{y},{w},{h}) "
                      f"centre_x={cx:.0f} bottom={bottom:.0f} area={area:.3f}")
            print(f"[{i + 1}] -> {'OBSTACLE AHEAD' if obstacle else 'clear'}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        picam2.stop()
        picam2.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
