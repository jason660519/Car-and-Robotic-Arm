import cv2
import numpy as np

p = '/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/line-follow-2026-08-15/map-bev-inventory-rotated.jpg'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
print('BEV photo:', w, 'x', h)

# track width ~27px (2cm @13.5px/cm). Width filter.
black = (gray < 100).astype(np.uint8) * 255
dt = cv2.distanceTransform(black, cv2.DIST_L2, 5)
track = ((dt >= 9) & (dt <= 22)).astype(np.uint8) * 255
track = cv2.bitwise_and(black, cv2.dilate(track, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15,15))))

# find the stem: near x=868 per planned path; scan columns 820..920 for long verticals
print('\ncolumns near stem (x 820-920), longest black runs:')
for x in range(820, 921, 10):
    col = black[:, x]
    ys = np.where(col > 0)[0]
    if len(ys) == 0: continue
    runs = []
    s = ys[0]; p_ = ys[0]
    for y in ys[1:]:
        if y - p_ > 10:
            runs.append((s, p_)); s = y
        p_ = y
    runs.append((s, p_))
    long = [f'{a}-{b}' for a, b in runs if b-a > 30]
    if long: print(f'  x={x}: {long}')

# The T: horizontal at y~583. Scan rows 540..640 for long horizontals
print('\nrows near T (y 540-640), longest black runs:')
for y in range(540, 641, 5):
    row = black[y, :]
    xs = np.where(row > 0)[0]
    if len(xs) == 0: continue
    runs = []
    s = xs[0]; p_ = xs[0]
    for x in xs[1:]:
        if x - p_ > 10:
            runs.append((s, p_)); s = x
        p_ = x
    runs.append((s, p_))
    long = [f'{a}-{b}({b-a})' for a, b in runs if b-a > 60]
    if long: print(f'  y={y}: {long}')
