import cv2
import numpy as np

p = '/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/assets/reference/task1/2026-08-16-task1-100x70-route-map-corrected.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60)).astype(np.uint8) * 255
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255
dt = cv2.distanceTransform(black, cv2.DIST_L2, 5)
ys, xs = np.where(red > 0)
d = dt[ys, xs]
far = d > 25
print('red pixels >25px (2.5cm) from black:', far.sum())
# cluster them
if far.sum():
    pts = np.column_stack([ys[far], xs[far]])
    # simple grid clustering at 40px
    seen = set()
    for y, x in pts:
        key = (y//40, x//40)
        seen.add(key)
    for ky, kx in sorted(seen):
        mask = (ys[far]//40 == ky) & (xs[far]//40 == kx)
        yy = ys[far][mask]; xx = xs[far][mask]
        print(f'  cluster at y~{yy.mean():.0f} x~{xx.mean():.0f} n={mask.sum()} maxdist={d[far][mask].max():.0f}px')
