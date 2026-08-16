import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

# x 590..830, y 440..680 at 4px
X0, Y0, CELL = 590, 440, 4
CW, CH = 60, 60
print('STEM region raw black (x 590-830, y 440-680), 4px. #=black>=12/16')
tick = ''.join(str((X0+cx*CELL)//100 % 10) if (X0+cx*CELL) % 100 == 0 else ' ' for cx in range(CW))
print('x:' + tick)
for cy in range(CH):
    row = ''
    for cx in range(CW):
        x0, x1 = X0+cx*CELL, min(w, X0+(cx+1)*CELL)
        y0, y1 = Y0+cy*CELL, min(h, Y0+(cy+1)*CELL)
        b = black[y0:y1, x0:x1].sum()
        if b > 12: row += '#'
        elif b > 0: row += '+'
        else: row += ' '
    print(f'{Y0+cy*CELL:4d} ' + row)
