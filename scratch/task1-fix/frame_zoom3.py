import cv2
import numpy as np

img = cv2.imread('/tmp/lf-cap3-raw.jpg')
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
chars = ' .:-=+*#%@'
# zoom x 300..1800, y 900..1200 at 6px
X0, Y0, CELL = 300, 900, 6
CW, CH = 250, 50
for cy in range(CH):
    row = ''
    for cx in range(CW):
        x0, x1 = X0+cx*CELL, min(w, X0+(cx+1)*CELL)
        y0, y1 = Y0+cy*CELL, min(h, Y0+(cy+1)*CELL)
        m = gray[y0:y1, x0:x1].mean()
        row += chars[min(9, int(m/25.6))]
    print(f'{Y0+cy*CELL:4d} ' + row)
