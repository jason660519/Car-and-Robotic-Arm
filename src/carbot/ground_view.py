"""Bird's-eye (ground-plane) view of the track in front of the car.

The IMX500 sits low and looks forward, so a 2 cm floor line is a trapezoid in
the camera frame and is easy to confuse with box edges and chair legs. A
homography from four ground correspondences (or a ChArUco board lying on the
paper) warps each frame into a metric top-down patch. Line following then
steers on a stroke that is actually ~2 cm wide in that patch.

This module is pure: no camera, no motors, no I2C.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from carbot.line_follow import LinePolicy, LineReading, _grayscale, _row_segments, _snap_to_dark


def _cv2() -> Any:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV is required for the ground view. On the Pi use system python3; "
            "on a development machine run with `uv run --extra vision`."
        ) from exc
    return cv2


@dataclass(frozen=True)
class GroundView:
    """Image-to-bird's-eye homography for one camera pose above the paper.

    Bird's-eye pixels: x increases to the car's right, y increases toward the
    bottom of the image (near the wheels). World metres: x right, y forward
    on the ground, matching the four calibration correspondences.
    """

    homography: np.ndarray
    bev_width: int
    bev_height: int
    metres_per_pixel: float
    x_min_m: float
    x_max_m: float
    y_min_m: float
    y_max_m: float
    image_points_px: tuple[tuple[float, float], ...]
    world_points_m: tuple[tuple[float, float], ...]

    def __post_init__(self) -> None:
        if self.homography.shape != (3, 3):
            raise ValueError("homography must be 3x3")
        if self.bev_width < 32 or self.bev_height < 32:
            raise ValueError("bird's-eye size must be at least 32x32")
        if self.metres_per_pixel <= 0:
            raise ValueError("metres_per_pixel must be positive")
        if not self.x_min_m < self.x_max_m:
            raise ValueError("x_min_m must be < x_max_m")
        if not self.y_min_m < self.y_max_m:
            raise ValueError("y_min_m must be < y_max_m")

    @property
    def expected_line_width_px(self) -> float:
        return 0.02 / self.metres_per_pixel

    def world_to_bev(self, x_m: float, y_m: float) -> tuple[float, float]:
        u = (x_m - self.x_min_m) / self.metres_per_pixel
        v = (self.y_max_m - y_m) / self.metres_per_pixel
        return u, v

    def bev_to_world(self, u: float, v: float) -> tuple[float, float]:
        x_m = self.x_min_m + u * self.metres_per_pixel
        y_m = self.y_max_m - v * self.metres_per_pixel
        return x_m, y_m

    def warp(self, image: np.ndarray) -> np.ndarray:
        cv2 = _cv2()
        return cv2.warpPerspective(
            image, self.homography, (self.bev_width, self.bev_height)
        )

    def bev_to_image(self, u: float, v: float) -> tuple[float, float]:
        inv = np.linalg.inv(self.homography)
        point = inv @ np.array([u, v, 1.0], dtype=np.float64)
        if abs(point[2]) < 1e-9:
            raise ValueError("bird's-eye point is at infinity in the camera frame")
        return float(point[0] / point[2]), float(point[1] / point[2])

    def to_json(self) -> dict[str, Any]:
        return {
            "homography": self.homography.tolist(),
            "bev_width": self.bev_width,
            "bev_height": self.bev_height,
            "metres_per_pixel": self.metres_per_pixel,
            "x_min_m": self.x_min_m,
            "x_max_m": self.x_max_m,
            "y_min_m": self.y_min_m,
            "y_max_m": self.y_max_m,
            "image_points_px": [list(p) for p in self.image_points_px],
            "world_points_m": [list(p) for p in self.world_points_m],
        }


def calibrate_ground_view(
    image_points_px: np.ndarray,
    world_points_m: np.ndarray,
    *,
    x_min_m: float = -0.30,
    x_max_m: float = 0.30,
    y_min_m: float = 0.12,
    y_max_m: float = 0.72,
    metres_per_pixel: float = 0.002,
) -> GroundView:
    """Fit a ground homography from four or more image/world pairs.

    ``image_points_px`` are pixel coordinates in the camera frame.
    ``world_points_m`` are metres on the floor, x right, y forward.
    """
    cv2 = _cv2()
    image_points = np.asarray(image_points_px, dtype=np.float64).reshape(-1, 2)
    world_points = np.asarray(world_points_m, dtype=np.float64).reshape(-1, 2)
    if image_points.shape[0] < 4 or image_points.shape != world_points.shape:
        raise ValueError("need at least four matching image and world points")
    bev_width = max(round((x_max_m - x_min_m) / metres_per_pixel), 32)
    bev_height = max(round((y_max_m - y_min_m) / metres_per_pixel), 32)
    bev_points = np.array(
        [
            [
                (x - x_min_m) / metres_per_pixel,
                (y_max_m - y) / metres_per_pixel,
            ]
            for x, y in world_points
        ],
        dtype=np.float64,
    )
    homography, _ = cv2.findHomography(image_points, bev_points, method=0)
    if homography is None:
        raise ValueError("could not fit a ground homography from the given points")
    return GroundView(
        homography=np.asarray(homography, dtype=np.float64),
        bev_width=bev_width,
        bev_height=bev_height,
        metres_per_pixel=metres_per_pixel,
        x_min_m=x_min_m,
        x_max_m=x_max_m,
        y_min_m=y_min_m,
        y_max_m=y_max_m,
        image_points_px=tuple((float(x), float(y)) for x, y in image_points),
        world_points_m=tuple((float(x), float(y)) for x, y in world_points),
    )


def ground_view_from_charuco(
    image: np.ndarray,
    *,
    x_min_m: float = -0.30,
    x_max_m: float = 0.30,
    y_min_m: float = 0.12,
    y_max_m: float = 0.72,
    metres_per_pixel: float = 0.002,
) -> GroundView:
    """Build a ground view from a ChArUco board lying flat on the paper.

    The board plane is treated as the floor. Place the board in front of the
    car with its +Y side farther away (the same orientation used for camera
    calibration). Outer board corners become the four world correspondences.
    """
    from carbot.vision import (
        calibration_for_image,
        detect_charuco_board_pose,
        load_calibration,
        load_charuco_board_geometry,
    )

    cv2 = _cv2()
    calib_path = (
        Path(__file__).resolve().parents[2]
        / "assets/reference/camera-calibration/2026-08-14-imx500-4056x3040/calibration.json"
    )
    calibration = load_calibration(calib_path)
    geometry = load_charuco_board_geometry(calib_path)
    pose = detect_charuco_board_pose(image, calibration, geometry)
    if pose is None:
        raise ValueError("no ChArUco board on the floor in this frame")
    width_m = geometry.squares_x * geometry.square_pitch_x_m
    length_m = geometry.squares_y * geometry.square_pitch_y_m
    object_corners = np.array(
        [[0.0, 0.0, 0.0], [width_m, 0.0, 0.0], [width_m, length_m, 0.0], [0.0, length_m, 0.0]],
        dtype=np.float64,
    )
    adjusted = calibration_for_image(calibration, image)
    projected, _ = cv2.projectPoints(
        object_corners,
        pose.rotation_vector,
        pose.translation_m,
        adjusted.camera_matrix,
        adjusted.distortion_coefficients,
    )
    image_points = projected.reshape(-1, 2)
    # Board +Y is farther from the car; shift so the board sits in the BEV
    # ahead of the origin rather than straddling x=0 only.
    world_points = np.array(
        [[-width_m / 2, y_min_m + 0.02], [width_m / 2, y_min_m + 0.02],
         [width_m / 2, y_min_m + 0.02 + length_m], [-width_m / 2, y_min_m + 0.02 + length_m]],
        dtype=np.float64,
    )
    return calibrate_ground_view(
        image_points,
        world_points,
        x_min_m=x_min_m,
        x_max_m=x_max_m,
        y_min_m=y_min_m,
        y_max_m=y_max_m,
        metres_per_pixel=metres_per_pixel,
    )


def save_ground_view(path: str | Path, view: GroundView) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(view.to_json(), indent=2) + "\n", encoding="utf-8")


def load_optional_ground_view(path: str | Path | None = None) -> GroundView | None:
    """Load a ground view if the file exists; otherwise return None."""
    candidates: list[Path] = []
    if path is not None:
        candidates.append(Path(path))
    candidates.append(Path("/tmp/line-follow/ground-view.json"))
    candidates.append(
        Path(__file__).resolve().parents[2]
        / "assets/reference/ground-view/imx500-2028x1520.json"
    )
    for candidate in candidates:
        if candidate.is_file():
            return load_ground_view(candidate)
    return None


def load_ground_view(path: str | Path) -> GroundView:
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    try:
        return GroundView(
            homography=np.asarray(data["homography"], dtype=np.float64),
            bev_width=int(data["bev_width"]),
            bev_height=int(data["bev_height"]),
            metres_per_pixel=float(data["metres_per_pixel"]),
            x_min_m=float(data["x_min_m"]),
            x_max_m=float(data["x_max_m"]),
            y_min_m=float(data["y_min_m"]),
            y_max_m=float(data["y_max_m"]),
            image_points_px=tuple(
                (float(x), float(y)) for x, y in data["image_points_px"]
            ),
            world_points_m=tuple(
                (float(x), float(y)) for x, y in data["world_points_m"]
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid ground-view file: {source}") from exc


def detect_line_on_ground(
    image: np.ndarray,
    view: GroundView,
    policy: LinePolicy | None = None,
) -> LineReading:
    """Find the 2 cm path in the bird's-eye patch and report camera-frame error."""
    policy = policy or LinePolicy()
    gray = _grayscale(image)
    bev = view.warp(gray)
    height, width = bev.shape[:2]
    expected_w = view.expected_line_width_px
    min_width = 0.012 / view.metres_per_pixel
    max_width = 0.040 / view.metres_per_pixel
    y_lo = int(height * 0.25)
    y_hi = height
    min_pixels = max(int(min_width * 0.5), 4)
    gap = 0.04 * width
    expected_x = width / 2
    hits: list[tuple[float, float, float]] = []
    for y in range(y_lo, y_hi, 2):
        segs = _row_segments(bev[y], policy.dark_threshold, min_pixels, gap)
        for centroid, seg_w, _x0, _x1 in segs:
            if min_width <= seg_w <= max_width:
                hits.append((centroid, float(y), float(seg_w)))
    if len(hits) < 6:
        return LineReading(
            visible=False,
            error_px=None,
            error_fraction=None,
            centroid_x=None,
            centroid_y=None,
            line_width_px=0.0,
            dark_fraction=float((bev < policy.dark_threshold).mean()),
            tracked_rows=len(hits),
            roi=(0, image.shape[0], 0, image.shape[1]),
            axis="vertical",
        )
    near_2cm = [
        h for h in hits
        if abs(h[2] - expected_w) / expected_w <= 0.6
    ]
    pool = near_2cm or hits
    # Prefer the cluster nearest heading (BEV centre).
    xs = np.array([h[0] for h in pool])
    chosen_x = float(np.median(xs[np.abs(xs - expected_x).argsort()[: max(len(pool) // 3, 6)]]))
    members = [h for h in pool if abs(h[0] - chosen_x) <= 0.06 * width]
    if len(members) < 4:
        members = pool
    u = float(np.median([h[0] for h in members]))
    v = float(np.percentile([h[1] for h in members], 75))
    line_width = float(np.median([h[2] for h in members]))
    u, v = _snap_to_dark(bev, u, v, policy.dark_threshold)
    image_x, image_y = view.bev_to_image(u, v)
    error_px = image_x - image.shape[1] / 2
    # Steer in bird's-eye metres, not raw perspective pixels.
    error_fraction = (u - expected_x) / (width / 2)
    return LineReading(
        visible=True,
        error_px=error_px,
        error_fraction=float(np.clip(error_fraction, -1.0, 1.0)),
        centroid_x=image_x,
        centroid_y=image_y,
        line_width_px=line_width,
        dark_fraction=float((bev < policy.dark_threshold).mean()),
        tracked_rows=len(members),
        roi=(0, image.shape[0], 0, image.shape[1]),
        axis="vertical",
        candidate_centroids=tuple(dict.fromkeys(round(h[0], 1) for h in pool[:8])),
    )
