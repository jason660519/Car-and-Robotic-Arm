import cv2
import numpy as np

p = '/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/assets/reference/task1/2026-08-16-task1-100x70-route-map-corrected.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60)).astype(np.uint8) * 255
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

print('v2 map 10px cells: R=route, #=track')
for cy in range(70):
    row = ''
    for cx in range(100):
        x0, x1 = cx*10, min(w, (cx+1)*10)
        y0, y1 = cy*10, min(h, (cy+1)*10)
        rd = red[y0:y1, x0:x1].sum()
        bl = black[y0:y1, x0:x1].sum()
        if rd > 30 and bl > 30: row += 'X'
        elif rd > 30: row += 'R'
        elif bl > 60: row += '#'
        elif bl > 15: row += '.'
        else: row += ' '
    print(f'{cy*10:4d} ' + row)
