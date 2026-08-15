"""Bird's-eye ground-view calibration and 2 cm line lock."""

from __future__ import annotations

import numpy as np
import pytest

from carbot.ground_view import (
    calibrate_ground_view,
    detect_line_on_ground,
    load_ground_view,
    save_ground_view,
)
from carbot.line_follow import detect_line

pytest.importorskip("cv2", reason="ground view needs OpenCV")

PAPER = 208
LINE = 40


def _view():
    image_pts = np.array([[0, 0], [299, 0], [299, 399], [0, 399]], dtype=float)
    world_pts = np.array(
        [[-0.30, 0.92], [0.30, 0.92], [0.30, 0.12], [-0.30, 0.12]],
        dtype=float,
    )
    return calibrate_ground_view(
        image_pts,
        world_pts,
        x_min_m=-0.30,
        x_max_m=0.30,
        y_min_m=0.12,
        y_max_m=0.92,
        metres_per_pixel=0.002,
    )


def _topdown_with_line(x: int = 150, width: int = 10) -> np.ndarray:
    image = np.full((400, 300), PAPER, dtype=np.uint8)
    image[:, x - width // 2 : x + width // 2] = LINE
    return image


def test_centred_2cm_line_in_birds_eye_has_near_zero_error():
    view = _view()
    reading = detect_line_on_ground(_topdown_with_line(), view)
    assert reading.visible
    assert reading.axis == "vertical"
    assert reading.error_fraction is not None
    assert abs(reading.error_fraction) < 0.08


def test_line_to_the_right_in_birds_eye_reports_positive_error():
    view = _view()
    reading = detect_line_on_ground(_topdown_with_line(x=210), view)
    assert reading.visible
    assert reading.error_fraction is not None
    assert reading.error_fraction > 0.15


def test_blank_paper_in_birds_eye_is_not_a_line():
    view = _view()
    image = np.full((400, 300), PAPER, dtype=np.uint8)
    reading = detect_line_on_ground(image, view)
    assert not reading.visible


def test_detect_line_uses_ground_view_when_provided():
    view = _view()
    reading = detect_line(_topdown_with_line(), ground_view=view)
    assert reading.visible
    assert reading.error_fraction is not None
    assert abs(reading.error_fraction) < 0.08


def test_ground_view_round_trips_through_json(tmp_path):
    view = _view()
    path = tmp_path / "ground-view.json"
    save_ground_view(path, view)
    loaded = load_ground_view(path)
    assert loaded.bev_width == view.bev_width
    np.testing.assert_allclose(loaded.homography, view.homography, rtol=1e-9)


def test_calibrate_rejects_fewer_than_four_points():
    with pytest.raises(ValueError):
        calibrate_ground_view([[0, 0], [1, 0], [1, 1]], [[0, 0], [1, 0], [1, 1]])
