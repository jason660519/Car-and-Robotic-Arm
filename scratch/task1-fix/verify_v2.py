import cv2
import numpy as np

# v2 image
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
print('image:', w, 'x', h)
print('red px:', len(xs), ' median dist to track: %.2f px (%.2f cm)' % (np.median(d), np.median(d)/10))
for t in (10, 20, 30):
    print(f'  red > {t}px ({t/10}cm) from track: {100*(d>t).mean():.1f}%')
far = d > 30
if far.sum():
    fy, fx = ys[far], xs[far]
    print('  worst clusters:')
    seen = set()
    for y, x in zip(fy, fx):
        k = (y//40, x//40)
        if k not in seen:
            seen.add(k)
            mask = (fy//40 == k[0]) & (fx//40 == k[1])
            print(f'    y~{fy[mask].mean():.0f} x~{fx[mask].mean():.0f} n={mask.sum()} max={d[far][mask].max():.0f}px')

# junction continuity
junctions = [(702,405), (862,405), (895,390), (933,210), (905,75), (320,75), (290,140), (290,215), (472,405), (702,505)]
print('\njunction red check:')
for x, y in junctions:
    x0, x1 = max(0,x-8), min(w-1,x+8)
    y0, y1 = max(0,y-8), min(h-1,y+8)
    ok = bool((red[y0:y1+1, x0:x1+1] > 0).any())
    print(f'  ({x},{y}): {"OK" if ok else "MISSING"}')

# ring arc coverage: 270 deg from 270 (top) CCW to 0 (3 o'clock) = angles {0..270}
cx, cy, R = 292, 412, 180
ang_hist = np.zeros(36)
for a in range(0, 360):
    px, py = int(cx + R*np.cos(np.radians(a))), int(cy + R*np.sin(np.radians(a)))
    if red[py, px] > 0:
        ang_hist[a // 10] += 1
empty = [i*10 for i, c in enumerate(ang_hist) if c == 0]
print('\nring arc empty 10-deg bins:', empty, '(expect only 270-360 = NE quadrant)')
