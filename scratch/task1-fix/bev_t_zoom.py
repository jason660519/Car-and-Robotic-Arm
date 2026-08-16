import cv2
import numpy as np

p = '/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/line-follow-2026-08-15/map-bev-inventory-rotated.jpg'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# T region: x 500..1200, y 500..740 at 3px
X0, Y0, CELL = 500, 500, 3
CW, CH = 233, 80
chars = ' .:-=+*#%@'
tick = ''.join(str((X0+cx*CELL)//100 % 10) if (X0+cx*CELL) % 100 == 0 else ' ' for cx in range(CW))
print('    ' + tick)
for cy in range(0, CH, 3):
    row = ''
    for cx in range(CW):
        x0, x1 = X0+cx*CELL, min(w, X0+(cx+1)*CELL)
        y0, y1 = Y0+cy*CELL, min(h, Y0+(cy+1)*CELL)
        m = gray[y0:y1, x0:x1].mean()
        row += chars[min(9, int(m/25.6))]
    print(f'{Y0+cy*CELL:4d} ' + row)
