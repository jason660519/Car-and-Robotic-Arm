import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60)).astype(np.uint8) * 255
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

# zoom x 830..1000, y 60..450 at 3px cells
X0, Y0, CELL = 830, 60, 3
CW = 57; CH = 130
print('Right side zoom (x 830-1000, y 60-450), 3px cells')
for cy in range(CH):
    row = ''
    for cx in range(CW):
        x0, x1 = X0+cx*CELL, min(w, X0+(cx+1)*CELL)
        y0, y1 = Y0+cy*CELL, min(h, Y0+(cy+1)*CELL)
        bl = black[y0:y1, x0:x1].sum()
        rd = red[y0:y1, x0:x1].sum()
        if rd > 30 and bl > 30: row += 'X'
        elif rd > 30: row += 'R'
        elif bl > 15: row += '#'
        elif bl > 4: row += '+'
        else: row += ' '
    if cy % 6 == 0:
        print(f'{Y0+cy*CELL:4d} ' + row)
    else:
        print('     ' + row)
