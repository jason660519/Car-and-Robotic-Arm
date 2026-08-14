"""Downward-looking line detection for black-line tracking on the track map.

The camera is mounted pointing down at the floor, so the frame shows the
track map directly under the car plus a fixed band of chassis/shadow at the
bottom edge. A verified still (2026-08-15, 4056x3040, IMX500 AI Camera):

- track paper background peaks around gray 208
- the black line is ~2.3 % of the pixels and sits ~230 px wide
- any threshold in 90..120 separates line from paper (``dark_threshold``
  defaults to 100)
- the chassis/shadow band starts near y=2081 (68 % of the frame height) and
  the map edge shadows occupy the top ~8 %; the ROI excludes both by default

The line is not assumed to be straight. Each scan row's dark-pixel centroid is
computed and the row centroids are combined with a median, which is robust to
branches, junctions, and the roundabout the car must trace. When too few rows
see a line the reading reports ``visible=False`` and ``error_px=None`` so the
controller can switch to a "search for the line" behaviour instead of steering
on garbage.

OpenCV is a Pi/`--extra vision` dependency, so it is imported lazily. This
module is pure: no camera, no motors, no I2C.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class LinePolicy:
    """Thresholds for treating dark pixels as the tracking line.

    Defaults come from the verified 2026-08-15 downward still described in the
    module docstring. The ROI is expressed in fractions of the frame so the same
    policy works at any capture resolution; ``roi_top`` and ``roi_bottom`` cut
    the map-edge shadows and the chassis band, which would otherwise read as
    huge dark regions and swamp the line centroid.

    ``dark_threshold`` is the gray value below which a pixel counts as "line".
    It is deliberately not aggressive: paper peaks at ~208, the line is well
    below 90 in the verified frame, so 100 leaves headroom for exposure changes
    without pulling in map shadows or dirt.
    """

    dark_threshold: int = 100
    roi_top: float = 0.10
    roi_bottom: float = 0.68
    min_row_dark_fraction: float = 0.002
    min_tracked_rows: int = 6
    min_line_fraction: float = 0.001
    # Junction (crossing) detection. A branch is a second dark line that
    # persists across at least ``min_branch_rows_fraction`` of the ROI height
    # while the main line is also present, with its centroid separated from the
    # main line by more than ``branch_gap_fraction`` of the frame width. The
    # verified 2026-08-15 map frame carries scattered dark print/shadows that
    # each last under ~1 % of the ROI (10-12 rows of 1763), while a real
    # crossing line spans ~13 % of it, so the fraction doubles as the noise
    # floor; a wide line alone is not a fork.
    branch_gap_fraction: float = 0.04
    min_branch_rows_fraction: float = 0.05

    def __post_init__(self) -> None:
        if not 0 <= self.dark_threshold <= 255:
            raise ValueError("dark_threshold must be in [0, 255]")
        if not 0.0 <= self.roi_top < self.roi_bottom <= 1.0:
            raise ValueError("roi must satisfy 0 <= roi_top < roi_bottom <= 1")
        if not 0.0 <= self.min_row_dark_fraction <= 1.0:
            raise ValueError("min_row_dark_fraction must be in [0, 1]")
        if self.min_tracked_rows < 1:
            raise ValueError("min_tracked_rows must be positive")
        if not 0.0 <= self.min_line_fraction <= 1.0:
            raise ValueError("min_line_fraction must be in [0, 1]")
        if not 0.0 <= self.branch_gap_fraction <= 1.0:
            raise ValueError("branch_gap_fraction must be in [0, 1]")
        if not 0.0 <= self.min_branch_rows_fraction <= 1.0:
            raise ValueError("min_branch_rows_fraction must be in [0, 1]")


@dataclass(frozen=True)
class LineReading:
    """What one frame says about the line, in the controller's terms.

    ``error_px`` is the line centroid minus the frame centre in pixels:
    positive means the line is to the right of the car's heading, negative to
    the left. ``error_fraction`` normalises it to [-1, 1]. Both are ``None``
    when the line is not visible. ``centroid_x`` stays meaningful even when the
    reading is not visible, so a search behaviour can steer toward the last
    seen line.

    ``branch_count``/``branch_centroids``/``junction`` describe crossing
    geometry. At a T-junction or crossroads the line widens and the per-row
    dark pixels split into two stable clusters; ``junction`` is True when two
    or more clusters persist across enough rows. The controller uses that flag
    to stop steering on a blended centroid and instead choose a branch by
    rule — see `carbot.line_nav`.
    """

    visible: bool
    error_px: float | None
    error_fraction: float | None
    centroid_x: float | None
    line_width_px: float
    dark_fraction: float
    tracked_rows: int
    roi: tuple[int, int, int, int]
    branch_count: int = 0
    branch_centroids: tuple[float, ...] = ()
    junction: bool = False
    candidate_centroids: tuple[float, ...] = ()

    @property
    def summary(self) -> str:
        if not self.visible:
            return "no line"
        state = (
            f"line err={self.error_px:+.0f}px ({self.error_fraction:+.2f}) "
            f"x={self.centroid_x:.0f} width={self.line_width_px:.0f}px "
            f"rows={self.tracked_rows}"
        )
        if self.junction:
            return f"JUNCTION branches={self.branch_count} {state}"
        return state


def _cv2() -> Any:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV is required for line detection. On the Pi use the system "
            "python3; on a development machine run with `uv run --extra vision`."
        ) from exc
    return cv2


def _grayscale(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image
    if image.ndim == 3 and image.shape[2] in (3, 4):
        cv2 = _cv2()
        code = cv2.COLOR_BGR2GRAY if image.shape[2] == 3 else cv2.COLOR_BGRA2GRAY
        return cv2.cvtColor(image, code)
    raise ValueError(f"unsupported image shape {image.shape}")


def _track_segments(
    dark: np.ndarray, min_row_pixels: int, gap: float
) -> tuple[list[float], list[int], list[float], list[int], int]:
    """Follow dark segments row by row into continuous lines.

    Each scan row's dark pixels are split into segments. Every segment is
    attached to the line from the previous rows whose running centroid is
    closest, provided the distance is within ``gap``; otherwise it starts a new
    line. Returns ``(segment_centroids, segment_widths, line_centroids,
    line_rows, rows_with_segments)`` where each ``line_*`` list is one entry
    per tracked line (mean centroid, member count) and ``rows_with_segments``
    is the number of scan rows that saw at least one segment.

    This row-to-row tracking is what keeps a curved main line together: its
    centroid drifts a few pixels per row, well inside ``gap``, whereas a global
    clustering of all segment centroids splits it whenever the drift exceeds
    the gap. Scattered map print and shadows die after a few rows.
    """
    segment_centroids: list[float] = []
    segment_widths: list[int] = []
    lines: list[list[float]] = []
    rows_with_segments = 0

    for row in dark:
        indices = np.flatnonzero(row)
        if indices.size < min_row_pixels:
            continue
        rows_with_segments += 1
        breaks = np.flatnonzero(np.diff(indices) > gap)
        for segment in np.split(indices, breaks + 1):
            if segment.size < min_row_pixels:
                continue
            centroid = float(segment.mean())
            segment_centroids.append(centroid)
            segment_widths.append(int(segment.size))
            best, best_dist = None, gap
            for line in lines:
                distance = abs(line[-1] - centroid)
                if distance <= best_dist:
                    best, best_dist = line, distance
            if best is None:
                lines.append([centroid])
            else:
                best.append(centroid)

    line_centroids = [float(np.mean(line)) for line in lines]
    line_rows = [len(line) for line in lines]
    return segment_centroids, segment_widths, line_centroids, line_rows, rows_with_segments


def detect_line(image: np.ndarray, policy: LinePolicy | None = None) -> LineReading:
    """Locate the dark tracking line in one downward-looking frame.

    Pipeline: grayscale -> ROI crop -> median blur -> threshold dark pixels ->
    per-row segments -> row-to-row tracking into lines -> main line centroid.
    When a second line persists alongside the main one the reading reports
    ``junction`` so the controller can choose a branch instead of steering at
    a blended centroid. Returns :class:`LineReading`; see its docstring.
    """
    policy = policy or LinePolicy()
    gray = _grayscale(image)
    height, width = gray.shape[:2]

    y_top = int(height * policy.roi_top)
    y_bottom = int(height * policy.roi_bottom)
    if y_bottom <= y_top:
        raise ValueError("ROI collapses to zero height; check roi_top/roi_bottom")
    roi = gray[y_top:y_bottom, :]

    blur = _cv2().medianBlur(roi, 5)
    dark = blur < policy.dark_threshold

    dark_fraction = float(dark.mean())
    roi_area = dark.size
    min_line_pixels = policy.min_line_fraction * roi_area
    min_row_pixels = policy.min_row_dark_fraction * width
    branch_gap = policy.branch_gap_fraction * width

    segment_centroids, segment_widths, line_centroids, line_rows, rows_with_segments = (
        _track_segments(dark, min_row_pixels, branch_gap)
    )
    branch_min_rows = policy.min_branch_rows_fraction * (y_bottom - y_top)
    if line_centroids:
        order = sorted(range(len(line_centroids)), key=lambda i: line_rows[i], reverse=True)
        main_centroid = line_centroids[order[0]]
        main_rows = line_rows[order[0]]
        branches = tuple(
            line_centroids[i]
            for i in order[1:]
            if line_rows[i] >= branch_min_rows
        )
    else:
        main_centroid, main_rows, branches = None, 0, ()

    dark_pixels = sum(segment_widths)
    candidates = tuple(
        line_centroids[i] for i in sorted(
            range(len(line_centroids)), key=lambda i: line_rows[i], reverse=True
        )
    )

    visible = (
        main_centroid is not None
        and main_rows >= policy.min_tracked_rows
        and dark_pixels >= min_line_pixels
    )

    if not visible:
        centroid = float(np.mean(segment_centroids)) if segment_centroids else None
        return LineReading(
            visible=False,
            error_px=None,
            error_fraction=None,
            centroid_x=centroid,
            line_width_px=float(np.mean(segment_widths)) if segment_widths else 0.0,
            dark_fraction=dark_fraction,
            tracked_rows=rows_with_segments,
            roi=(y_top, y_bottom, 0, width),
            candidate_centroids=candidates,
        )

    junction = len(branches) >= 1
    if junction:
        main_width = _line_width(segment_centroids, segment_widths, main_centroid, branch_gap)
        error_px = main_centroid - width / 2
        return LineReading(
            visible=True,
            error_px=error_px,
            error_fraction=error_px / (width / 2),
            centroid_x=main_centroid,
            line_width_px=main_width,
            dark_fraction=dark_fraction,
            tracked_rows=rows_with_segments,
            roi=(y_top, y_bottom, 0, width),
            branch_count=1 + len(branches),
            branch_centroids=(main_centroid,) + branches,
            junction=True,
            candidate_centroids=candidates,
        )

    error_px = main_centroid - width / 2
    return LineReading(
        visible=True,
        error_px=error_px,
        error_fraction=error_px / (width / 2),
        centroid_x=main_centroid,
        line_width_px=float(np.median(segment_widths)),
        dark_fraction=dark_fraction,
        tracked_rows=rows_with_segments,
        roi=(y_top, y_bottom, 0, width),
        branch_count=1,
        branch_centroids=(main_centroid,),
        candidate_centroids=candidates,
    )


def _line_width(
    segment_centroids: list[float], segment_widths: list[int], centroid: float, gap: float
) -> float:
    """Median width of segments belonging to the line at ``centroid``."""
    widths = [
        w for w, c in zip(segment_widths, segment_centroids) if abs(c - centroid) <= gap
    ]
    return float(np.median(widths)) if widths else 0.0


def detect_line_file(path: str, policy: LinePolicy | None = None) -> LineReading:
    """Run :func:`detect_line` on an image on disk. Raises ``ValueError`` when
    the file cannot be read."""
    cv2 = _cv2()
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"could not read image: {path}")
    return detect_line(image, policy)
