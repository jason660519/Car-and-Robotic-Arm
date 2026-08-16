import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255
dt = cv2.distanceTransform(black, cv2.DIST_L2, 5)
track = ((dt >= 6) & (dt <= 17)).astype(np.uint8) * 255
track = cv2.bitwise_and(black, cv2.dilate(track, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11,11))))

n, lab, stats, cents = cv2.connectedComponentsWithStats(track)
print('components:', n)
comps = []
for i in range(1, n):
    x, y, ww, hh, area = stats[i]
    if area > 800:
        comps.append((i, x, y, ww, hh, area))
comps.sort(key=lambda c: -c[5])
for i, x, y, ww, hh, area in comps[:20]:
    print(f'  comp {i}: bbox=({x},{y},{ww},{hh}) area={area} center=({cents[i][0]:.0f},{cents[i][1]:.0f})')

# Which component contains the roundabout ring? Which the stem?
# roundabout ring points: (292,412) R=180 -> sample point (292, 300) top area, (112,412) left
for name, pt in [('ring top (292,232)', (292, 232)), ('ring left (112,412)', (112, 412)),
                 ('ring bottom (292,592)', (292, 592)), ('stem (755,560)', (755, 560)),
                 ('stem top (755,480)', (755, 480)), ('T cross (700,490)', (700, 490)),
                 ('middle horiz (700,395)', (700, 395)), ('top line (600,78)', (600, 78)),
                 ('right vert (933,300)', (933, 300)), ('entrance (290,180)', (290, 180))]:
    x, y = pt
    if 0 <= x < w and 0 <= y < h and lab[y, x] > 0:
        print(f'{name}: component {lab[y, x]}')
    else:
        print(f'{name}: NOT in track mask')
