import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/media__1786840258952.jpg'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# warped (760,480) -> photo ~(520,332). Render photo x 400..700, y 230..430 at 3px
X0, Y0, CELL = 400, 230, 3
CW, CH = 100, 67
chars = ' .:-=+*#%@'
print('Photo T region (x 400-700, y 230-430), 3px gradient:')
tick = ''.join(str((X0+cx*CELL)//100 % 10) if (X0+cx*CELL) % 100 == 0 else ' ' for cx in range(CW))
print('    ' + tick)
for cy in range(0, CH, 2):
    row = ''
    for cx in range(CW):
        x0, x1 = X0+cx*CELL, min(w, X0+(cx+1)*CELL)
        y0, y1 = Y0+cy*CELL, min(h, Y0+(cy+1)*CELL)
        m = gray[y0:y1, x0:x1].mean()
        row += chars[min(9, int(m/25.6))]
    print(f'{Y0+cy*CELL:4d} ' + row)
