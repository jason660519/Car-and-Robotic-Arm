import cv2
import numpy as np

p = '/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/assets/reference/task1/2026-08-16-task1-100x70-route-map-corrected.png'
img = cv2.imread(p)
h, w = img.shape[:2]
print('image:', w, 'x', h)

b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60)).astype(np.uint8) * 255
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

dt = cv2.distanceTransform(black, cv2.DIST_L2, 5)
ys, xs = np.where(red > 0)
d = dt[ys, xs]
print('red pixels:', len(xs))
print('median dist red->black track: %.2f px (%.2f cm)' % (np.median(d), np.median(d)/10))
print('frac red > 10px from track: %.1f%%' % (100*(d > 10).mean()))
print('frac red > 20px from track: %.1f%%' % (100*(d > 20).mean()))

# Show where red is far from track (top offenders)
far = d > 25
if far.sum():
    fy, fx = ys[far], xs[far]
    print('red pixels >25px from track:', far.sum())
    for y, x in zip(fy[:20], fx[:20]):
        print(f'   ({x},{y}) dist={dt[y,x]:.0f}')

# Continuity: check red at each segment junction
junctions = [(760,485), (985,485), (895,390), (933,210), (905,75), (320,75), (290,140), (290,215), (455,465), (760,480)]
print('\nJunction red presence (radius 8):')
for x, y in junctions:
    x0, x1 = max(0,x-8), min(w-1,x+8)
    y0, y1 = max(0,y-8), min(h-1,y+8)
    ok = bool((red[y0:y1+1, x0:x1+1] > 0).any())
    print(f'  ({x},{y}): {"OK" if ok else "MISSING"}')
