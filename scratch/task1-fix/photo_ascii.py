import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/media__1786840258952.jpg'
img = cv2.imread(p)
h, w = img.shape[:2]
print('photo:', w, 'x', h)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# coarse: 12px cells -> 64 x 85
CH, CW = 85, 64
out = []
for cy in range(CH):
    row = ''
    for cx in range(CW):
        y0, y1 = cy*12, min(h, (cy+1)*12)
        x0, x1 = cx*12, min(w, (cx+1)*12)
        cell = gray[y0:y1, x0:x1]
        mn = cell.min()
        mean = cell.mean()
        if mn < 60: row += '#'
        elif mn < 110: row += '+'
        elif mean < 140: row += '.'
        elif mean < 190: row += ' '
        else: row += ' '
    out.append(row)
for cy, row in enumerate(out):
    if cy % 5 == 0:
        print(f'{cy*12:4d} ' + row)
    else:
        print('     ' + row)
