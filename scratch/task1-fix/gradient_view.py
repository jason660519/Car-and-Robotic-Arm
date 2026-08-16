import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# T region x 600..900, y 440..540, 3px cells, gradient chars
X0, Y0, CELL = 600, 440, 3
CW, CH = 100, 34
chars = ' .:-=+*#%@'
print('T region gradient (3px cells). Dark=@ #, light=. .')
tick = ''.join(str((X0+cx*CELL)//100 % 10) if (X0+cx*CELL) % 100 == 0 else ' ' for cx in range(CW))
print('    ' + tick)
for cy in range(CH):
    row = ''
    for cx in range(CW):
        x0, x1 = X0+cx*CELL, min(w, X0+(cx+1)*CELL)
        y0, y1 = Y0+cy*CELL, min(h, Y0+(cy+1)*CELL)
        m = gray[y0:y1, x0:x1].mean()
        row += chars[min(9, int(m/25.6))]
    print(f'{Y0+cy*CELL:4d} ' + row)
