#!/usr/bin/env python3
"""Draw the CORRECTED Task-1 route on a clean 100x70 (1000x700 px) orthophoto (v2).

v2 fixes the T-junction / stem / return-line geometry using the project's own
planned-route data (scratch/line-follow-2026-08-15/planned-route-lengths.txt,
planned-path.npy) and the operator-confirmed phase lengths:
  Phase 2 = 16.0 cm, Phase 10 = 23.0 cm, stem = 10.0 cm.

Anchors (10 px = 1 cm):
  - Roundabout centre (292,412), R=180 px (D=36.0 cm), entry at 12 o'clock,
    3/4 CCW arc (270 deg) ending at 3 o'clock (472,412).
  - Return line: (472,405) -> T (702,405)  = 23.0 cm.
  - Stem: (702,505) -> (702,405)          = 10.0 cm (start zone at bottom).
  - Phase 2: (702,405) -> (862,405)       = 16.0 cm.
  - ARC1 SE -> Line A (x=933) up -> NE -> top line -> NW -> entrance -> ring.
All segments connect end-to-end (continuous path).
"""
import cv2
import numpy as np

SRC = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/media__1786840258952.jpg'
OUT = '/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/assets/reference/task1/2026-08-16-task1-100x70-route-map-corrected.png'

img = cv2.imread(SRC)
rot = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

pts_src = np.array([
    [60, 90], [890, 100], [895, 690], [70, 680],
], dtype='float32')
out_w, out_h = 1000, 700
pts_dst = np.array([[0, 0], [out_w - 1, 0], [out_w - 1, out_h - 1], [0, out_h - 1]], dtype='float32')
M = cv2.getPerspectiveTransform(pts_src, pts_dst)
base = cv2.warpPerspective(rot, M, (out_w, out_h))
overlay = base.copy()

RED = (0, 0, 255)
DKBLUE = (0, 80, 160)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

def pline(pts, color=RED, thickness=6):
    pts = np.array(pts, dtype=np.int32).reshape(-1, 1, 2)
    cv2.polylines(overlay, [pts], False, color, thickness, cv2.LINE_AA)

def arrow(p1, p2, color=RED, thickness=6, tip=0.12):
    cv2.arrowedLine(overlay, p1, p2, color, thickness, cv2.LINE_AA, tipLength=tip)

# ---------------------------------------------------------------------------
# CORRECTED ROUTE v2 — continuous, follows the real track (10 px = 1 cm)
# ---------------------------------------------------------------------------
# Phase 1: stem UP from 發車區 (702,505) to T junction (702,405) = 10.0 cm
arrow((702, 505), (702, 405), tip=0.10)
# Phase 2: T -> east 16.0 cm (702,405) -> (862,405)
arrow((702, 405), (862, 405), tip=0.08)
# ARC 1 (SE corner): small curve to Line A bottom
pline([(862, 405), (878, 398), (890, 393), (895, 390)])
# Phase 4: north along Line A (x drifts 895 -> 933, then vertical at 933)
pline([(895, 390), (920, 362), (933, 330), (933, 210)])
arrow((933, 300), (933, 235), tip=0.10)
# ARC 2 (NE corner): Line A top -> top line
pline([(933, 210), (933, 168), (933, 130), (922, 102), (905, 75)])
# Phase 6: top line west (58.5 cm)
arrow((905, 75), (320, 75), tip=0.06)
# ARC 3 (NW corner): top line left end -> entrance line
pline([(320, 75), (311, 92), (299, 112), (290, 140)])
# Phase 8: entrance line down to roundabout top (7.5 cm)
arrow((290, 140), (290, 215), tip=0.12)
arrow((290, 215), (292, 232), tip=0.10)
# Phase 9: roundabout 3/4 CCW arc: 12 o'clock -> 9 -> 6 -> 3 o'clock (270 deg)
cv2.ellipse(overlay, (292, 412), (180, 180), 0, 0, 270, RED, 6, cv2.LINE_AA)
# Phase 10: return from ring 3 o'clock (472,405) -> T (702,405) = 23.0 cm
arrow((472, 405), (702, 405), tip=0.08)
# Phase 11: stem DOWN back to 發車區
arrow((702, 405), (702, 505), tip=0.10)

# ---------------------------------------------------------------------------
# Scale bar (0-20 cm) top-left
# ---------------------------------------------------------------------------
sx, sy = 40, 40
sl = 200  # 200 px = 20 cm
cv2.rectangle(overlay, (sx - 12, sy - 30), (sx + sl + 12, sy + 30), WHITE, -1)
cv2.rectangle(overlay, (sx - 12, sy - 30), (sx + sl + 12, sy + 30), BLACK, 2)
cv2.line(overlay, (sx, sy), (sx + sl, sy), BLACK, 5)
cv2.line(overlay, (sx, sy - 10), (sx, sy + 10), BLACK, 4)
cv2.line(overlay, (sx + sl, sy - 10), (sx + sl, sy + 10), BLACK, 4)
cv2.line(overlay, (sx + 100, sy - 6), (sx + 100, sy + 6), BLACK, 3)
cv2.putText(overlay, 'SCALE 0-20 cm (10 px = 1 cm)', (sx - 8, sy - 36),
            cv2.FONT_HERSHEY_SIMPLEX, 0.42, BLACK, 2)
cv2.putText(overlay, '0', (sx - 10, sy + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.4, BLACK, 1)
cv2.putText(overlay, '10', (sx + 88, sy + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.4, BLACK, 1)
cv2.putText(overlay, '20', (sx + 190, sy + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.4, BLACK, 1)

# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------
def label(text, pos, color=DKBLUE, scale=0.42, thick=2, bg=WHITE):
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thick)
    x, y = pos
    cv2.rectangle(overlay, (x - 3, y - th - 4), (x + tw + 3, y + 5), bg, -1)
    cv2.rectangle(overlay, (x - 3, y - th - 4), (x + tw + 3, y + 5), BLACK, 1)
    cv2.putText(overlay, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thick)

label('Map 100 cm (E-W) x 70 cm (N-S) | 10 px = 1 cm | corrected route v2', (250, 32), color=(0, 90, 0))
label('Phase 1: stem 10.0 cm', (720, 500), color=RED)
label('Phase 2: east 16.0 cm', (760, 440), color=RED)
label('ARC 1 SE corner ~5 cm', (800, 375), color=RED)
label('Phase 4: north 18.7 cm', (850, 330), color=RED)
label('ARC 2 NE corner ~14 cm', (840, 120), color=RED)
label('Phase 6: west 58.5 cm', (560, 52), color=RED)
label('ARC 3 NW corner ~7 cm', (150, 96), color=RED)
label('Phase 8: entrance 7.5 cm', (60, 160), color=RED)
label('Roundabout D=36.0 cm | Phase 9 arc 84.8 cm', (128, 480), color=(160, 0, 0))
label('Phase 10: return 23.0 cm', (500, 445), color=RED)
label('Phase 11: return stem 10 cm', (620, 560), color=RED)
label('Start 發車區', (630, 535), color=BLACK, bg=(255, 236, 205))
label('T junction', (640, 390), color=BLACK, bg=(220, 240, 255))

cv2.imwrite(OUT, overlay)

# ---------------------------------------------------------------------------
# Report measured lengths (px -> cm)
# ---------------------------------------------------------------------------
def seg_len(pts):
    pts = np.array(pts, dtype=np.float64)
    return np.sum(np.hypot(np.diff(pts[:, 0]), np.diff(pts[:, 1]))) / 10.0

arc_len = 270 / 360.0 * 2 * np.pi * 180 / 10
print('Phase 1 stem : %.1f cm' % seg_len([(702, 505), (702, 405)]))
print('Phase 2 east : %.1f cm' % seg_len([(702, 405), (862, 405)]))
print('ARC1 SE      : %.1f cm' % seg_len([(862, 405), (878, 398), (890, 393), (895, 390)]))
print('Phase 4 north: %.1f cm' % seg_len([(895, 390), (920, 362), (933, 330), (933, 210)]))
print('ARC2 NE      : %.1f cm' % seg_len([(933, 210), (933, 168), (933, 130), (922, 102), (905, 75)]))
print('Phase 6 west : %.1f cm' % seg_len([(905, 75), (320, 75)]))
print('ARC3 NW      : %.1f cm' % seg_len([(320, 75), (311, 92), (299, 112), (290, 140)]))
print('Phase 8 entry: %.1f cm' % seg_len([(290, 140), (290, 215)]))
print('Phase 9 ring : %.1f cm (270 deg of R=180)' % arc_len)
print('Phase 10 ret : %.1f cm' % seg_len([(472, 405), (702, 405)]))
print('Phase 11 stem: %.1f cm' % seg_len([(702, 405), (702, 505)]))
total = (seg_len([(702, 505), (702, 405)]) + seg_len([(702, 405), (862, 405)]) +
         seg_len([(862, 405), (878, 398), (890, 393), (895, 390)]) +
         seg_len([(895, 390), (920, 362), (933, 330), (933, 210)]) +
         seg_len([(933, 210), (933, 168), (933, 130), (922, 102), (905, 75)]) +
         seg_len([(905, 75), (320, 75)]) + seg_len([(320, 75), (311, 92), (299, 112), (290, 140)]) +
         seg_len([(290, 140), (290, 215)]) + arc_len +
         seg_len([(472, 405), (702, 405)]) + seg_len([(702, 405), (702, 505)]))
print('TOTAL        : %.1f cm' % total)
print('saved:', OUT)
