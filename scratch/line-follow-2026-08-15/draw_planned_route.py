"""Draw the planned line-follow route on the bird's-eye photo, on the 2 cm stroke."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
PHOTO = ROOT / "map-bev-inventory-rotated.jpg"
FONT = "/System/Library/Fonts/STHeiti Light.ttc"

LINE_CM = 2.0
STEM_WIDTH_PX = 27.0
PX_PER_CM = STEM_WIDTH_PX / LINE_CM
CM_PER_PX = 1.0 / PX_PER_CM
TICK_CM = 20.0

# Circle from Hough + ring samples on this BEV.
CC = np.array([307.0, 581.0])
CR = 258.0


def load_gray():
    bgr = cv2.imread(str(PHOTO))
    if bgr is None:
        raise FileNotFoundError(PHOTO)
    gray = cv2.GaussianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    return bgr, gray


def snap_center(gray: np.ndarray, x: float, y: float, win: int = 28) -> tuple[int, int]:
    """Move to the darkest 2 cm-scale blob in a window (medial-ish)."""
    h, w = gray.shape
    xi, yi = int(round(x)), int(round(y))
    x0, x1 = max(0, xi - win), min(w, xi + win + 1)
    y0, y1 = max(0, yi - win), min(h, yi + win + 1)
    roi = gray[y0:y1, x0:x1]
    dark = roi < 90
    if dark.sum() < 8:
        return xi, yi
    dist = cv2.distanceTransform(dark.astype(np.uint8) * 255, cv2.DIST_L2, 5)
    dist[~dark] = 0
    # Prefer ~half of 2 cm (13.5 px), not paper-edge slabs.
    target = STEM_WIDTH_PX / 2.0
    score = dist - 0.35 * np.abs(dist - target)
    score[~dark] = -1e9
    yy, xx = np.unravel_index(int(np.argmax(score)), score.shape)
    return int(x0 + xx), int(y0 + yy)


def snap_ring(gray: np.ndarray, deg: float) -> tuple[int, int]:
    rad = np.deg2rad(deg)
    direction = np.array([np.cos(rad), np.sin(rad)])
    best = None
    best_val = 255
    for t in np.linspace(CR - 45, CR + 45, 91):
        p = CC + direction * t
        x, y = int(round(p[0])), int(round(p[1]))
        if 0 <= x < gray.shape[1] and 0 <= y < gray.shape[0]:
            v = int(gray[y, x])
            if v < best_val:
                best_val = v
                best = (x, y)
    return best if best is not None else tuple(np.round(CC + direction * CR).astype(int))


def densify(points: list[tuple[int, int]], step: float = 6.0) -> np.ndarray:
    out = [np.array(points[0], dtype=float)]
    for a, b in zip(points, points[1:]):
        a = np.array(a, dtype=float)
        b = np.array(b, dtype=float)
        n = max(int(np.linalg.norm(b - a) / step), 1)
        for i in range(1, n + 1):
            out.append(a + (b - a) * (i / n))
    return np.array(out)


def cumulative_cm(path: np.ndarray) -> np.ndarray:
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    return np.concatenate([[0.0], np.cumsum(seg * CM_PER_PX)])


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT, size=size, index=0)


def build_path(gray: np.ndarray) -> tuple[np.ndarray, dict]:
    # Waypoints sit on measured 2 cm strokes (row/col scans), then snapped.
    stem = [(868, 700), (868, 660), (867, 591)]
    # T-bar right (horizontal 2 cm) then right vertical of outer loop (~x=1150).
    outer = [
        (867, 583),
        (950, 578),
        (1000, 573),
        (1100, 560),
        (1151, 545),
        (1151, 500),
        (1153, 400),
        (1148, 300),
        (1137, 200),
        (1137, 155),
        (1100, 155),
        (1000, 138),
        (800, 132),
        (600, 129),
        (400, 121),
        (320, 140),
        (307, 200),
        (307, 280),
    ]
    # Visual CCW: 12 o'clock (270°) → 9 (180°) → 6 (90°) → 3 (0°).
    ring_degs = list(range(270, -1, -8))
    ring = [snap_ring(gray, d) for d in ring_degs]
    ret = [(550, 581), (700, 585), (867, 583), (868, 660), (868, 720)]

    raw = stem + outer + ring + ret
    snapped = [snap_center(gray, *p) for p in raw]
    # Keep ring points from radial snap; they already sit on the ink.
    n_before_ring = len(stem) + len(outer)
    snapped[n_before_ring : n_before_ring + len(ring)] = ring
    path = densify(snapped, step=5.0)

    keys = {
        "start": snap_center(gray, 868, 700),
        "t": snap_center(gray, 867, 591),
        "right_mid": snap_center(gray, 1151, 400),
        "enter_rb": snap_ring(gray, 270),
        "e1": snap_ring(gray, 180),
        "e2": snap_ring(gray, 90),
        "e3": snap_ring(gray, 0),
        "back": snap_center(gray, 868, 720),
    }
    # Segment cuts by nearest path index.
    def near(pt):
        d = np.linalg.norm(path - np.array(pt, dtype=float), axis=1)
        return int(np.argmin(d))

    cuts = {
        "stem": (near(keys["start"]), near(keys["t"])),
        "outer": (near(keys["t"]), near(keys["enter_rb"])),
        "roundabout": (near(keys["enter_rb"]), near(keys["e3"])),
        "return": (near(keys["e3"]), near(keys["back"])),
    }
    return path, keys, cuts  # path, landmarks, segment index cuts


def draw(bgr: np.ndarray, gray: np.ndarray) -> Image.Image:
    path, keys, cuts = build_path(gray)
    cum = cumulative_cm(path)
    total = float(cum[-1])

    def length(name: str) -> float:
        a, b = cuts[name]
        return float(abs(cum[b] - cum[a]))

    lengths = {k: length(k) for k in cuts}

    vis = cv2.addWeighted(bgr, 0.62, np.full_like(bgr, 255), 0.38, 0)

    def poly(pts, color, thick):
        arr = np.array(pts, dtype=np.int32).reshape(-1, 1, 2)
        cv2.polylines(vis, [arr], False, color, thick, cv2.LINE_AA)

    GREEN, ORANGE, BLUE, PURPLE = (46, 160, 50), (0, 140, 255), (210, 90, 20), (150, 50, 160)
    i_t, i_enter, i_e3 = cuts["stem"][1], cuts["outer"][1], cuts["roundabout"][1]
    poly(path[: i_t + 1], GREEN, 8)
    poly(path[i_t : i_enter + 1], ORANGE, 8)
    poly(path[i_enter : i_e3 + 1], BLUE, 8)
    poly(path[i_e3:], PURPLE, 8)

    # T right arrow on the actual line.
    t = np.array(keys["t"])
    cv2.arrowedLine(
        vis,
        tuple(t.astype(int)),
        tuple((t + np.array([70, 0])).astype(int)),
        (0, 0, 210),
        7,
        cv2.LINE_AA,
        tipLength=0.35,
    )

    # 20 cm ticks + labels
    next_tick = TICK_CM
    rgb = cv2.cvtColor(vis, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    draw_im = ImageDraw.Draw(pil)
    f_tick = font(22)
    f_small = font(18)
    f_title = font(28)
    f_body = font(20)

    for i, cm in enumerate(cum):
        if cm + 0.4 < next_tick:
            continue
        if i + 1 >= len(path):
            break
        p = path[i]
        tangent = path[min(i + 3, len(path) - 1)] - path[max(i - 3, 0)]
        nrm = np.array([-tangent[1], tangent[0]])
        nlen = np.linalg.norm(nrm)
        if nlen < 1:
            continue
        nrm = nrm / nlen * 14
        a = p - nrm
        b = p + nrm
        draw_im.line([tuple(a), tuple(b)], fill=(20, 20, 20), width=3)
        label_at = p + nrm * 2.4
        text = f"{int(round(next_tick))}cm"
        draw_im.text((label_at[0] + 4, label_at[1] - 10), text, font=f_tick, fill=(20, 20, 20))
        next_tick += TICK_CM
    s = keys["start"]
    draw_im.text((s[0] + 18, s[1] - 8), "0cm", font=f_tick, fill=(20, 20, 20))

    def badge(xy, n, fill):
        x, y = int(xy[0]), int(xy[1])
        draw_im.ellipse((x - 18, y - 18, x + 18, y + 18), fill=(255, 255, 255), outline=fill, width=3)
        draw_im.text((x - 7, y - 12), str(n), font=f_title, fill=fill)

    badge((keys["start"][0] - 48, keys["start"][1]), 1, (46, 140, 40))
    badge((keys["t"][0] + 8, keys["t"][1] - 40), 3, (210, 110, 0))
    badge(keys["right_mid"], 4, (210, 110, 0))
    badge(keys["enter_rb"], 5, (20, 90, 200))
    badge((keys["t"][0] + 36, keys["t"][1] + 48), 6, (140, 40, 150))

    for pt, lab in [(keys["e1"], "E1"), (keys["e2"], "E2"), (keys["e3"], "E3")]:
        x, y = int(pt[0]), int(pt[1])
        draw_im.ellipse((x - 16, y - 16, x + 16, y + 16), fill=(255, 255, 255), outline=(20, 90, 200), width=2)
        draw_im.text((x - 14, y - 10), lab, font=f_small, fill=(20, 90, 200))

    # Scale bar (10 cm of 2 cm-line pixels).
    bar_px = PX_PER_CM * 10
    bx, by = 40, bgr.shape[0] - 36
    draw_im.line([(bx, by), (bx + bar_px, by)], fill=(20, 20, 20), width=6)
    draw_im.line([(bx, by - 8), (bx, by + 8)], fill=(20, 20, 20), width=3)
    draw_im.line([(bx + bar_px, by - 8), (bx + bar_px, by + 8)], fill=(20, 20, 20), width=3)
    draw_im.text((bx, by - 28), "10 cm  （线宽 2 cm = 27 px）", font=f_small, fill=(20, 20, 20))

    # Side panel
    panel_w = 430
    canvas = Image.new("RGB", (pil.width + panel_w, pil.height), (248, 248, 248))
    canvas.paste(pil, (0, 0))
    p = ImageDraw.Draw(canvas)
    x0 = pil.width + 22
    y = 28

    def lines(text, f=f_body, fill=(30, 30, 30), gap=28):
        nonlocal y
        p.text((x0, y), text, font=f, fill=fill)
        y += gap

    lines("规划路线（未发车）", f_title, (0, 70, 170), 40)
    lines(f"全长约 {total:.0f} cm", f_title, (20, 20, 20), 36)
    lines("尺度：2 cm 黑线 ≈ 27 px", f_small, (80, 80, 80), 24)
    lines("折痕/斜拍会让局部差几 cm", f_small, (80, 80, 80), 32)
    y += 8
    lines("1  发车区开口", f_body, (46, 140, 40))
    lines(f"2  直行竖线        {lengths['stem']:.0f} cm", f_body, (46, 140, 40))
    lines("     不在 1→2 右转", f_small, (80, 80, 80), 24)
    lines("     镜头前倾会先看到 T", f_small, (80, 80, 80), 24)
    lines(f"3  车身到 T 再右转", f_body, (210, 110, 0))
    lines(f"4  外圈（诗）      {lengths['outer']:.0f} cm", f_body, (210, 110, 0))
    lines(f"5  环岛逆时针      {lengths['roundabout']:.0f} cm", f_body, (20, 90, 200))
    lines("     E1 左  E2 下  E3 右", f_small, (80, 80, 80), 24)
    lines("     走第 3 出口 E3", f_body, (20, 90, 200))
    lines(f"6  回 T 再下发车  {lengths['return']:.0f} cm", f_body, (140, 40, 150))
    y += 16
    lines("第一 T 不要左转。", f_body, (180, 30, 30))
    lines("左转会先进入圆环。", f_small, (80, 80, 80), 26)
    y += 12
    lines("沿路短杠 = 每 20 cm", f_small, (80, 80, 80), 24)
    lines("数字贴在 2 cm 中线旁。", f_small, (80, 80, 80), 24)
    y += 16
    lines("看对再说发车。", f_body, (20, 20, 20))

    np.save(ROOT / "planned-path.npy", path)
    (ROOT / "planned-route-lengths.txt").write_text(
        "\n".join(
            [
                f"px_per_cm={PX_PER_CM:.3f}",
                f"total_cm={total:.1f}",
                *(f"{k}_cm={v:.1f}" for k, v in lengths.items()),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return canvas


def main() -> None:
    bgr, gray = load_gray()
    img = draw(bgr, gray)
    dest = ROOT / "planned-route-inventory.jpg"
    img.save(dest, quality=92)
    print(f"wrote {dest}")
    print((ROOT / "planned-route-lengths.txt").read_text())


if __name__ == "__main__":
    main()
