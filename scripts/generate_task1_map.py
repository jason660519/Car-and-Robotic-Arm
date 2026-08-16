#!/usr/bin/env python3
"""Generate the printable Task-1 map: 8 A4 map pages + 1 instruction page.

The map is drawn vector-style at exact millimetre scale and split into a
4x2 grid of A4 pages (each 210x297 mm) that tile into a 840x594 mm sheet
carrying a 840x588 mm map (the original 1000x700 mm Task-1 map scaled by
0.84). The 20 mm black route line and the 20 mm AprilTags are NOT scaled —
they keep their physical size so line-follow and tag pose estimation keep
working; only the route geometry and tag positions are scaled.

Units are millimetres throughout. Coordinate frame: map frame, SW origin,
x east, y north (matches src/carbot/landmarks.py conventions).

Page 1..8 = map tiles; page 9 = print/assemble + AprilTag usage guide.

Run:
    uv run --with reportlab python3 scripts/generate_task1_map.py \
        --output scratch/landmarks/task1-map.pdf \
        --tag-map-out scratch/landmarks/task1-tag-map.json
"""

from __future__ import annotations

import argparse
import io
import json
import math
from itertools import pairwise
from pathlib import Path

import cv2
from reportlab.lib.colors import black, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

MM_PER_PT = 25.4 / 72.0
A4_W_MM, A4_H_MM = 210.0, 297.0

# ---------------------------------------------------------------------------
# Map geometry (mm, SW origin: x east, y north). Original 1000x700 mm * 0.84.
# ---------------------------------------------------------------------------
SCALE = 0.84
MAP_W_MM = 840.0
MAP_H_MM = 588.0
LINE_W_MM = 20.0  # 2 cm black line, kept at physical size
TAG_SIZE_MM = 20.0  # AprilTag side, kept at physical size
MIN_TAG_CLEAR_MM = 20.0  # tag edge to black-line edge

ROUNDABOUT = (245.3, 241.9, 151.2)  # cx, cy, R (mm)

# Route centerlines as polylines (mm). Roundabout is drawn separately.
ROUTE = [
    [(589.7, 163.8), (589.7, 247.8)],  # stem up
    [(589.7, 247.8), (724.1, 247.8)],  # Phase 2 east
    [(724.1, 247.8), (737.5, 253.7), (747.6, 257.9), (751.8, 260.4)],  # ARC 1 SE
    [(751.8, 260.4), (772.8, 283.9), (783.7, 310.8)],  # east slant
    [(783.7, 310.8), (783.7, 411.6)],  # Line A up
    [(783.7, 411.6), (783.7, 446.9), (783.7, 478.8), (774.5, 502.3), (760.2, 525)],  # ARC 2 NE
    [(760.2, 525), (268.8, 525)],  # Phase 6 top
    [(268.8, 525), (261.2, 510.7), (251.2, 493.9), (243.6, 470.4)],  # ARC 3 NW
    [(243.6, 470.4), (243.6, 407.4), (245.3, 393.1)],  # entry down
    [(396.5, 241.9), (396.5, 247.8)],  # exit -> return
    [(396.5, 247.8), (589.7, 247.8)],  # Phase 10 return
]

# Designed tag positions (id, x_mm, y_mm), verified clear of the route and
# page seams by scripts/../ (see --tag-map-out and the assert below).
TAGS = [
    (0, 45, 565),
    (1, 135, 435),
    (2, 400, 485),
    (3, 655, 485),
    (4, 800, 545),
    (5, 818, 335),
    (6, 815, 205),
    (7, 790, 60),
    (8, 50, 60),
    (9, 80, 130),
    (10, 120, 540),
    (11, 660, 200),
    (12, 660, 130),
    (13, 500, 200),
    (14, 760, 215),
    (15, 450, 180),
]

START_MM = (589.7, 163.8)  # stem bottom = start zone
SCALE_BAR = (300.0, 20.0, 100.0)  # x, y, length (mm)
NORTH_MM = (150.0, 555.0)  # north arrow position

SEAM_X = [210.0, 420.0, 630.0]  # vertical page seams
SEAM_Y = 294.0  # horizontal page seam


def pt(mm: float) -> float:
    return mm / MM_PER_PT


def make_tag_png(tag_id: int, size_px: int = 400) -> bytes:
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
    marker = cv2.aruco.generateImageMarker(dictionary, tag_id, size_px)
    ok, encoded = cv2.imencode(".png", marker)
    if not ok:
        raise RuntimeError(f"could not encode tag {tag_id}")
    return encoded.tobytes()


# ---------------------------------------------------------------------------
# Geometry helpers (mm)
# ---------------------------------------------------------------------------
def dist_point_seg(px: float, py: float, a, b) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def min_route_dist(px: float, py: float) -> float:
    d = min(dist_point_seg(px, py, a, b) for seg in ROUTE for a, b in pairwise(seg))
    cx, cy, r = ROUNDABOUT
    d = min(d, abs(math.hypot(px - cx, py - cy) - r))
    return d


def roundabout_points(n: int = 360):
    """270-degree arc from 12 o'clock counter-clockwise to 3 o'clock."""
    cx, cy, r = ROUNDABOUT
    pts = []
    for i in range(n + 1):
        theta = math.radians(90.0 + 270.0 * i / n)  # 90 -> 360 deg
        pts.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))
    return pts


def validate_tags(tags):
    problems = []
    for tid, x, y in tags:
        rd = min_route_dist(x, y)
        if rd < LINE_W_MM / 2.0 + MIN_TAG_CLEAR_MM:
            problems.append(f"tag {tid}: route clearance {rd:.1f} mm < 30")
        if min(abs(x - s) for s in SEAM_X) < 15.0:
            problems.append(f"tag {tid}: too close to vertical seam")
        if abs(y - SEAM_Y) < 15.0:
            problems.append(f"tag {tid}: too close to horizontal seam")
        if (
            x < TAG_SIZE_MM
            or x > MAP_W_MM - TAG_SIZE_MM
            or y < TAG_SIZE_MM
            or y > MAP_H_MM - TAG_SIZE_MM
        ):
            problems.append(f"tag {tid}: outside map ({x:.0f},{y:.0f})")
    return problems


# ---------------------------------------------------------------------------
# Drawing (all in mm, SW origin)
# ---------------------------------------------------------------------------
def draw_map(c: canvas.Canvas, tag_pngs: dict[int, bytes], detail: bool = True) -> None:
    # Route black line (20 mm wide, round joins).
    c.setStrokeColor(black)
    c.setLineWidth(pt(LINE_W_MM))
    c.setLineCap(1)
    c.setLineJoin(1)
    for seg in ROUTE:
        p = c.beginPath()
        p.moveTo(pt(seg[0][0]), pt(seg[0][1]))
        for x, y in seg[1:]:
            p.lineTo(pt(x), pt(y))
        c.drawPath(p, stroke=1, fill=0)
    # Roundabout arc.
    ring = roundabout_points()
    p = c.beginPath()
    p.moveTo(pt(ring[0][0]), pt(ring[0][1]))
    for x, y in ring[1:]:
        p.lineTo(pt(x), pt(y))
    c.drawPath(p, stroke=1, fill=0)

    # Direction arrows (white triangles on the line).
    c.setFillColor(white)
    arrows = [
        ((589.7, 205.0), (589.7, 225.0)),  # stem up
        ((655.0, 247.8), (675.0, 247.8)),  # Phase 2 east
        ((783.7, 360.0), (783.7, 380.0)),  # Line A up
        ((500.0, 525.0), (480.0, 525.0)),  # Phase 6 west
        ((243.6, 440.0), (243.6, 420.0)),  # entry down
        ((500.0, 247.8), (480.0, 247.8)),  # return west
    ]
    for (x1, y1), (x2, y2) in arrows:
        draw_arrow(c, (x1, y1), (x2, y2))

    # Start zone marker.
    sx, sy = START_MM
    c.setStrokeColor(black)
    c.setLineWidth(pt(1.2))
    c.setFillColor(white)
    c.rect(pt(sx - 30), pt(sy - 34), pt(60), pt(30), stroke=1, fill=1)
    if detail:
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(pt(sx), pt(sy - 22), "START")
        c.setFont("STSong-Light", 8)
        c.drawCentredString(pt(sx), pt(sy - 32), "发车区 / 归零点")

    # AprilTags + labels.
    for tag_id, tx, ty in TAGS:
        png = tag_pngs[tag_id]
        c.drawImage(
            ImageReader(io.BytesIO(png)),
            pt(tx - TAG_SIZE_MM / 2),
            pt(ty - TAG_SIZE_MM / 2),
            width=pt(TAG_SIZE_MM),
            height=pt(TAG_SIZE_MM),
        )
        # thin border so the white quiet zone is visible against the paper
        c.setStrokeColor(black)
        c.setLineWidth(pt(0.3))
        c.rect(
            pt(tx - TAG_SIZE_MM / 2),
            pt(ty - TAG_SIZE_MM / 2),
            pt(TAG_SIZE_MM),
            pt(TAG_SIZE_MM),
            stroke=1,
            fill=0,
        )
        # ID label + north tick
        if detail:
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(black)
            c.drawCentredString(pt(tx), pt(ty + TAG_SIZE_MM / 2 + 3.5), f"ID {tag_id}")
            c.drawCentredString(pt(tx), pt(ty + TAG_SIZE_MM / 2 + 7.5), "N \u2191")

    # North arrow.
    nx, ny = NORTH_MM
    c.setFillColor(black)
    if detail:
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(pt(nx), pt(ny + 16), "N")
    p = c.beginPath()
    p.moveTo(pt(nx), pt(ny + 12))
    p.lineTo(pt(nx - 6), pt(ny))
    p.lineTo(pt(nx + 6), pt(ny))
    p.close()
    c.drawPath(p, stroke=0, fill=1)

    # Scale bar (100 mm, ticked every 10 mm).
    bx, by, blen = SCALE_BAR
    c.setStrokeColor(black)
    c.setLineWidth(pt(1.2))
    c.line(pt(bx), pt(by), pt(bx + blen), pt(by))
    for i in range(11):
        x = bx + i * blen / 10.0
        h = 4.0 if i % 5 == 0 else 2.0
        c.line(pt(x), pt(by), pt(x), pt(by - h))
    if detail:
        c.setFont("Helvetica", 7)
        c.drawString(pt(bx - 4), pt(by - 8), "0")
        c.drawString(pt(bx + blen / 2 - 3), pt(by - 8), "50")
        c.drawString(pt(bx + blen - 6), pt(by - 8), "100 mm")
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(
            pt(bx + blen / 2),
            pt(by + 4),
            "scale bar \u2014 print at 100% and verify with a ruler",
        )

    # Map border.
    c.setStrokeColor(black)
    c.setLineWidth(pt(0.5))
    c.rect(pt(0), pt(0), pt(MAP_W_MM), pt(MAP_H_MM), stroke=1, fill=0)


def draw_arrow(c: canvas.Canvas, a, b) -> None:
    x1, y1 = a
    x2, y2 = b
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 8.0
    tip = (x2, y2)
    left = (tip[0] - size * math.cos(ang - 0.5), tip[1] - size * math.sin(ang - 0.5))
    right = (tip[0] - size * math.cos(ang + 0.5), tip[1] - size * math.sin(ang + 0.5))
    p = c.beginPath()
    p.moveTo(pt(tip[0]), pt(tip[1]))
    p.lineTo(pt(left[0]), pt(left[1]))
    p.lineTo(pt(right[0]), pt(right[1]))
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def draw_page_marks(
    c: canvas.Canvas, tile_no: int, total: int = 8, pdf_page: int | None = None
) -> None:
    """Corner crosses + tile number, in page coordinates (mm from page bottom-left)."""
    c.setStrokeColor(black)
    c.setLineWidth(pt(0.4))
    for cx, cy in [(10, 10), (A4_W_MM - 10, 10), (10, A4_H_MM - 10), (A4_W_MM - 10, A4_H_MM - 10)]:
        c.line(pt(cx - 3), pt(cy), pt(cx + 3), pt(cy))
        c.line(pt(cx), pt(cy - 3), pt(cx), pt(cy + 3))
    label = f"tile {tile_no}/{total}"
    if pdf_page is not None:
        label += f"  (PDF page {pdf_page})"
    c.setFont("Helvetica", 7)
    c.drawCentredString(pt(A4_W_MM / 2), pt(8), label)


def draw_overview(c: canvas.Canvas, tag_pngs: dict[int, bytes]) -> None:
    """Page 1: whole-map thumbnail with the 8-page grid and tile numbers."""
    s = 0.25
    map_w_mm = MAP_W_MM * s  # 210
    map_h_mm = MAP_H_MM * s  # 147
    ox = (A4_W_MM - map_w_mm) / 2.0
    oy = A4_H_MM - map_h_mm - 26.0

    # Title.
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(pt(A4_W_MM / 2), pt(A4_H_MM - 14), "Task-1 Map \u2014 Overview")
    c.setFont("STSong-Light", 10)
    c.drawCentredString(
        pt(A4_W_MM / 2),
        pt(A4_H_MM - 23),
        "\u603b\u89c8\u7f29\u56fe\uff08\u5bf9\u7167\u62fc\u63a5\uff09",
    )

    # Thumbnail (route + tags + border, no text labels).
    c.saveState()
    c.translate(pt(ox), pt(oy))
    c.scale(s, s)
    draw_map(c, tag_pngs, detail=False)
    c.restoreState()

    # 8-page grid (dashed) + tile numbers.
    c.setDash(2, 2)
    c.setLineWidth(pt(0.4))
    c.setStrokeColor(black)
    for i in range(1, 4):
        x = ox + i * 210.0 * s
        c.line(pt(x), pt(oy), pt(x), pt(oy + map_h_mm))
    c.line(pt(ox), pt(oy + map_h_mm / 2), pt(ox + map_w_mm), pt(oy + map_h_mm / 2))
    c.setDash()

    c.setFont("Helvetica-Bold", 9)
    for col in range(4):
        for row in range(2):
            tile = row * 4 + col + 1  # row 0 = top (tiles 1-4), row 1 = bottom (5-8)
            cx = ox + (col + 0.5) * 210.0 * s
            cy = oy + ((2 - row) * 294.0 - 147.0) * s
            c.drawCentredString(pt(cx), pt(cy), f"{tile}")

    # Bottom notes.
    y = oy - 10.0
    c.setFont("Helvetica-Bold", 10)
    c.drawString(pt(20), pt(y), "Assemble order")
    y -= 13
    c.setFont("Helvetica", 8.5)
    for ln in (
        "Top row (north): tiles 1 \u2013 4, left to right.",
        "Bottom row (south): tiles 5 \u2013 8, left to right.",
        "Align the corner crosses on adjacent tiles and tape on the back.",
    ):
        c.drawString(pt(22), pt(y), ln)
        y -= 12
    c.setFont("STSong-Light", 8.5)
    c.drawString(
        pt(22),
        pt(y),
        "\u4e0a\u6392\uff08\u5317\uff09\u4e3a\u7b2c1\u20134\u5f20\uff0c\u4e0b\u6392\uff08\u5357\uff09\u4e3a\u7b2c5\u20138\u5f20\uff1b\u5bf9\u9f50\u56db\u89d2\u5341\u5b57\u6807\u8bb0\u62fc\u63a5\u3002",
    )


# ---------------------------------------------------------------------------
# Instruction page (page 9)
# ---------------------------------------------------------------------------
def draw_guide(c: canvas.Canvas) -> None:
    c.setFillColor(black)
    y = A4_H_MM - 20
    c.setFont("Helvetica-Bold", 16)
    c.drawString(pt(20), pt(y), "Task-1 Map \u2014 Print & Assemble Guide")
    y -= 14
    c.setFont("STSong-Light", 11)
    c.drawString(
        pt(20),
        pt(y),
        "\u4efb\u52a1\u4e00\u5730\u56fe\uff1a\u6253\u5370\u4e0e\u62fc\u63a5\u8bf4\u660e",
    )
    y -= 22

    def para(title, lines):
        nonlocal y
        c.setFont("Helvetica-Bold", 11)
        c.drawString(pt(20), pt(y), title)
        y -= 15
        c.setFont("Helvetica", 9.5)
        for ln in lines:
            c.drawString(pt(24), pt(y), ln)
            y -= 12.5
        y -= 6

    para(
        "1. Print the 8 map tiles (PDF pages 3\u201310)",
        [
            "Print PDF pages 3\u201310 on A4 at 100% / Actual Size. Do NOT use \u201cfit to page\u201d.",
            "Verify the 100 mm scale bar with a ruler before assembling.",
            "\u6253\u5370 PDF \u7b2c3\u201310\u9875\uff0c\u9009\u201c\u5b9e\u9645\u5927\u5c0f 100%\u201d\uff0c\u4e0d\u8981\u201c\u7f29\u653e\u5230\u9875\u9762\u201d\uff1b\u5148\u7528\u5c3a\u91cf\u6bd4\u4f8b\u5c3a\u3002",
        ],
    )
    para(
        "2. Assemble (4 columns x 2 rows) \u2014 see the overview on PDF page 1",
        [
            "Top row (north) = tiles 1\u20134 left to right; bottom row (south) = tiles 5\u20138 left to right.",
            "Align the corner crosses on adjacent tiles; tape on the back.",
            "4\u5217 x 2\u884c\uff1a\u4e0a\u6392\uff08\u5317\uff09\u4e3a tile 1\u20134\uff0c\u4e0b\u6392\uff08\u5357\uff09\u4e3a tile 5\u20138\uff1b\u5bf9\u9f50\u56db\u89d2\u5341\u5b57\u6807\u8bb0\u3002",
        ],
    )
    para(
        "3. Orientation",
        [
            "The N arrow points map-north (up). Tags are printed with ID upright facing north.",
            "\u671d\u5317\u7bad\u5934\u6307\u5411\u5730\u56fe\u5317\uff08\u4e0a\u65b9\uff09\u3002",
        ],
    )
    para(
        "4. AprilTag landmarks (the printed squares)",
        [
            "16 AprilTags (family 36h11, 20 mm) are printed onto the map as absolute-position landmarks.",
            "Each is labelled \u201cID n\u201d with an \u201cN \u2191\u201d marker (yaw = 0 = facing map-north).",
            "Web search: \u201cAprilTag\u201d, \u201cAprilTag 36h11\u201d, \u201cAprilTag pose estimation\u201d, \u201cOpenCV aruco AprilTag\u201d.",
            "AprilTag\uff08\u5bb6\u65cf 36h11\uff0c20 mm\uff09\u662f\u673a\u5668\u89c6\u89c9\u5b9a\u4f4d\u5730\u6807\uff1b\u4e0a\u7f51\u641c\u201cAprilTag\u201d\u5373\u53ef\u627e\u5230\u4f7f\u7528\u8bf4\u660e\u3002",
        ],
    )
    para(
        "5. Scale",
        [
            "Map 840 x 588 mm = original 1000 x 700 mm Task-1 map scaled 0.84.",
            "Route black line 20 mm; AprilTags 20 mm (physical sizes unchanged).",
        ],
    )


# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("scratch/landmarks/task1-map.pdf"))
    parser.add_argument(
        "--tag-map-out", type=Path, default=Path("scratch/landmarks/task1-tag-map.json")
    )
    args = parser.parse_args()

    problems = validate_tags(TAGS)
    if problems:
        for p in problems:
            print("ERROR:", p)
        return 1

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

    tag_pngs = {tid: make_tag_png(tid) for tid, _, _ in TAGS}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(args.output), pagesize=A4)
    pdf.setTitle("Task-1 map (overview + guide + 8 tiles)")

    # Page 1: overview thumbnail (with the 8-page grid); page 2: guide.
    draw_overview(pdf, tag_pngs)
    pdf.showPage()
    draw_guide(pdf)
    pdf.showPage()

    # Pages 3..10: map tiles, 4 columns x 2 rows. Tiles 1-4 = top row
    # (map north, y 294..588), tiles 5-8 = bottom row (y 0..294).
    for page in range(8):
        col = page % 4
        row = 1 - page // 4  # 1 = top row (map top), 0 = bottom row
        # clip to the page, then translate so big-map (col*210, row*294)
        # lands at the page origin.
        pdf.saveState()
        clip = pdf.beginPath()
        clip.rect(0, 0, pt(A4_W_MM), pt(A4_H_MM))
        pdf.clipPath(clip, stroke=0, fill=0)
        pdf.translate(-pt(col * 210.0), -pt(row * 294.0))
        draw_map(pdf, tag_pngs)
        pdf.restoreState()
        draw_page_marks(pdf, page + 1, 8, pdf_page=page + 3)
        pdf.showPage()

    pdf.save()
    print(f"wrote {args.output} (overview + guide + 8 tiles, {len(TAGS)} tags)")

    # Tag map JSON (metres, SW origin, x east / y north).
    tag_map = {
        "name": "task1-map-scaled-0.84",
        "description": (
            "AprilTags printed directly on the 840x588 mm map (original "
            "1000x700 mm scaled 0.84). Map frame: SW origin, x east, y north, "
            "metres; NE corner = (0.84, 0.588). Tag size 20 mm. yaw_deg 0 = "
            "ID upright facing map-north (N arrow up)."
        ),
        "tags": [
            {
                "id": tid,
                "x_m": round(x / 1000.0, 4),
                "y_m": round(y / 1000.0, 4),
                "z_m": 0.0,
                "yaw_deg": 0,
                "size_m": 0.02,
            }
            for tid, x, y in TAGS
        ],
    }
    args.tag_map_out.parent.mkdir(parents=True, exist_ok=True)
    args.tag_map_out.write_text(json.dumps(tag_map, indent=2) + "\n", encoding="utf-8")
    print(f"wrote tag-map {args.tag_map_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
