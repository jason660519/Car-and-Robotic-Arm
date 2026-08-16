import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60))
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black_nr = ((gray < 100) & ~red).astype(np.uint8) * 255

# x 880..1000, y 380..520 at 2px
X0, Y0, CELL = 880, 380, 2
CW, CH = 60, 70
print('SE region x 880-1000, y 380-520, 2px:')
for cy in range(CH):
    row = ''
    for cx in range(CW):
        x0, x1 = X0+cx*CELL, min(w, X0+(cx+1)*CELL)
        y0, y1 = Y0+cy*CELL, min(h, Y0+(cy+1)*CELL)
        bl = black_nr[y0:y1, x0:x1].sum()
        if bl > 7: row += '#'
        elif bl > 2: row += '+'
        else: row += ' '
    print(f'{Y0+cy*CELL:4d} ' + row)
