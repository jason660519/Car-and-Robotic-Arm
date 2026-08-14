"""Tests for downward black-line detection, using synthetic images.

Each fixture isolates one property: a centred vertical line reports a near-zero
error, a shifted line reports a proportional error, a blank floor reports "no
line", and a bottom band of chassis/shadow must not leak into the reading
because the ROI excludes it. The real 2026-08-15 capture is not committed, so
every case here is synthetic; the module docstring records what the real frame
measured (line ~230 px wide, threshold 90-120 all valid, chassis band below
68 % of the frame).
"""

from __future__ import annotations

import numpy as np
import pytest

from carbot.line_follow import LinePolicy, detect_line

pytest.importorskip("cv2", reason="line detection needs OpenCV")

HEIGHT, WIDTH = 480, 640
PAPER = 208  # verified background gray of the track map


def blank(paper: int = PAPER) -> np.ndarray:
    return np.full((HEIGHT, WIDTH), paper, dtype=np.uint8)


def vertical_line(x: int, width: int = 20) -> np.ndarray:
    """White paper with a black vertical strip centred on ``x``."""
    image = blank()
    image[:, x - width // 2 : x + width // 2] = 40  # verified line gray << 100
    return image


def chassis_band(image: np.ndarray, y_start: int = int(HEIGHT * 0.72)) -> np.ndarray:
    """Simulate the dark chassis/shadow strip at the bottom of the frame."""
    image = image.copy()
    image[y_start:, :] = 50
    return image


# --------------------------------------------------------------------- basics


def test_centred_line_reports_near_zero_error():
    reading = detect_line(vertical_line(WIDTH // 2))
    assert reading.visible
    assert reading.error_px is not None
    assert abs(reading.error_px) < 5
    assert abs(reading.error_fraction or 0) < 0.02
    assert reading.centroid_x == pytest.approx(WIDTH / 2, abs=5)


def test_line_to_the_left_reports_negative_error():
    reading = detect_line(vertical_line(WIDTH // 4))
    assert reading.visible
    assert reading.error_px is not None
    assert reading.error_px < 0
    assert reading.centroid_x == pytest.approx(WIDTH / 4, abs=10)


def test_line_to_the_right_reports_positive_error():
    reading = detect_line(vertical_line(3 * WIDTH // 4))
    assert reading.visible
    assert reading.error_px is not None
    assert reading.error_px > 0
    assert reading.error_fraction == pytest.approx(
        reading.error_px / (WIDTH / 2), abs=1e-9
    )


def test_error_fraction_is_normalised_to_unit_range():
    reading = detect_line(vertical_line(WIDTH // 4))
    assert -1.0 <= reading.error_fraction <= 1.0


def test_blank_floor_reports_no_line():
    reading = detect_line(blank())
    assert not reading.visible
    assert reading.error_px is None
    assert reading.error_fraction is None


def test_line_width_is_reported():
    reading = detect_line(vertical_line(WIDTH // 2, width=30))
    assert reading.line_width_px == pytest.approx(30, abs=5)


# ------------------------------------------------------- ROI / real-frame cases


def test_chassis_band_does_not_leak_into_the_reading():
    """The dark band at the bottom is outside roi_bottom=0.68 by default."""
    image = chassis_band(vertical_line(WIDTH // 2))
    reading = detect_line(image)
    assert reading.visible
    assert reading.centroid_x == pytest.approx(WIDTH / 2, abs=5)


def test_chassis_band_alone_reports_no_line():
    """A frame with only the chassis band (car off the map) must not steer."""
    reading = detect_line(chassis_band(blank()))
    assert not reading.visible


def test_line_only_inside_top_roi_shadow_is_ignored():
    """Map-edge shadows at the top are cut by roi_top; a line below still works."""
    image = blank()
    image[: int(HEIGHT * 0.05), :] = 40  # top shadow
    image[int(HEIGHT * 0.4) : int(HEIGHT * 0.6), WIDTH // 2 - 10 : WIDTH // 2 + 10] = 40
    reading = detect_line(image)
    assert reading.visible
    assert reading.centroid_x == pytest.approx(WIDTH / 2, abs=5)


def test_threshold_headroom_matches_verified_frame():
    """The verified still separated at every threshold 90-120; policy must too."""
    for threshold in (90, 100, 110, 120):
        reading = detect_line(vertical_line(WIDTH // 2), LinePolicy(dark_threshold=threshold))
        assert reading.visible, f"threshold {threshold} lost the line"


def test_sparse_noise_does_not_read_as_a_line():
    """Scattered dark specks are under min_row_dark_fraction per row."""
    image = blank()
    rng = np.random.default_rng(3)
    xs, ys = rng.integers(0, WIDTH, 40), rng.integers(0, HEIGHT, 40)
    for x, y in zip(xs, ys):
        image[y : y + 2, x : x + 2] = 40
    reading = detect_line(image)
    assert not reading.visible


# ----------------------------------------------------------------- validation


def test_policy_rejects_invalid_thresholds():
    with pytest.raises(ValueError):
        LinePolicy(dark_threshold=256)
    with pytest.raises(ValueError):
        LinePolicy(roi_top=0.9, roi_bottom=0.1)
    with pytest.raises(ValueError):
        LinePolicy(min_tracked_rows=0)


def test_detect_line_rejects_non_image_input():
    with pytest.raises(ValueError):
        detect_line(np.zeros((10, 10, 5), dtype=np.uint8))  # 5 channels


# ----------------------------------------------------------- junction / forks


def y_fork(branch_rows: int = 40) -> np.ndarray:
    """Main vertical line plus a diagonal branch joining it partway down.

    The bottom of the frame shows only the main line; the top shows the main
    line and the branch side by side — the geometry the downward camera sees
    when the car approaches a roundabout entry.
    """
    image = blank()
    main_x = WIDTH // 2
    # main line, full ROI
    image[int(HEIGHT * 0.10) : int(HEIGHT * 0.68), main_x - 10 : main_x + 10] = 40
    # diagonal branch from the main line at y_branch up to the top-right
    y_branch = int(HEIGHT * 0.40)
    for step in range(branch_rows):
        yy = y_branch - step
        xx = main_x + step * 3
        image[yy, xx - 8 : xx + 8] = 40
    return image


def test_plain_line_is_not_a_junction():
    reading = detect_line(vertical_line(WIDTH // 2))
    assert reading.junction is False
    assert reading.branch_count == 1


def test_wide_line_is_not_a_junction():
    """A 100 px strip is wide but single-branched; width alone must not fork."""
    reading = detect_line(vertical_line(WIDTH // 2, width=100))
    assert reading.junction is False
    assert reading.branch_count == 1


def test_fork_reports_two_branches():
    reading = detect_line(y_fork())
    assert reading.visible
    assert reading.junction
    assert reading.branch_count == 2
    assert len(reading.branch_centroids) == 2
    # main branch is the persistent vertical line at the frame centre
    assert reading.branch_centroids[0] == pytest.approx(WIDTH // 2, abs=20)


def test_too_short_a_branch_is_not_a_junction():
    """A flicker that appears on only a couple of rows is noise, not a fork."""
    reading = detect_line(y_fork(branch_rows=2))
    assert reading.junction is False


def test_junction_summary_labels_it():
    reading = detect_line(y_fork())
    assert reading.summary.startswith("JUNCTION branches=2")
