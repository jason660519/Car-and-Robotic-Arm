import cv2
import numpy as np

p = '/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/assets/reference/task1/2026-08-16-task1-100x70-route-map-corrected.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60)).astype(np.uint8) * 255

# Check red ring coverage around (292,412) R=180 for angles 0..360
cx, cy, R = 292, 412, 180
ang_hist = np.zeros(36)
for a in range(0, 360, 1):
    px, py = int(cx + R*np.cos(np.radians(a))), int(cy + R*np.sin(np.radians(a)))
    if red[py, px] > 0:
        ang_hist[a // 10] += 1
print('red ring coverage by 10deg bin (angle: count):')
for i, c in enumerate(ang_hist):
    if c > 0:
        print(f'  {i*10:3d}-{i*10+10:3d} deg: {c}/10')
missing = [i*10 for i, c in enumerate(ang_hist) if c == 0]
print('empty bins:', missing)
