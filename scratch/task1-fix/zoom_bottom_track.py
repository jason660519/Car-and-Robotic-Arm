import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255
dt = cv2.distanceTransform(black, cv2.DIST_L2, 5)
track = ((dt >= 6) & (dt <= 17)).astype(np.uint8) * 255
track = cv2.bitwise_and(black, cv2.dilate(track, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11,11))))

# x 560..900, y 430..700 at 4px
X0, Y0, CELL = 560, 430, 4
CW, CH = 85, 68
print('Bottom-right TRACK only (x 560-900, y 430-700):')
for cy in range(CH):
    row = ''
    for cx in range(CW):
        x0, x1 = X0+cx*CELL, min(w, X0+(cx+1)*CELL)
        y0, y1 = Y0+cy*CELL, min(h, Y0+(cy+1)*CELL)
        t = track[y0:y1, x0:x1].sum()
        if t > 12: row += '#'
        elif t > 0: row += '+'
        else: row += ' '
    if cy % 5 == 0:
        print(f'{Y0+cy*CELL:4d} ' + row)
    else:
        print('     ' + row)
