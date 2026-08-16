import cv2
import numpy as np

img = cv2.imread('/tmp/lf-cap-raw.jpg')
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
chars = ' .:-=+*#%@'
# zoom x 400..1700, y 400..1000 at 8px
X0, Y0, CELL = 400, 400, 8
CW, CH = 160, 75
for cy in range(0, CH, 3):
    row = ''
    for cx in range(CW):
        x0, x1 = X0+cx*CELL, min(w, X0+(cx+1)*CELL)
        y0, y1 = Y0+cy*CELL, min(h, Y0+(cy+1)*CELL)
        m = gray[y0:y1, x0:x1].mean()
        row += chars[min(9, int(m/25.6))]
    print(f'{Y0+cy*CELL:4d} ' + row)
