import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

# Track line width ~20px: distance transform 6..16px from edge = 12..32px wide features
dt = cv2.distanceTransform(black, cv2.DIST_L2, 5)
track = ((dt >= 6) & (dt <= 17)).astype(np.uint8) * 255
# restore full line body: dilate by 5 then AND with black
track = cv2.bitwise_and(black, cv2.dilate(track, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11,11))))
cv2.imwrite('/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/task1-fix/track_only.png', track)

# visualize at 5px cells
CELL = 5
CW, CH = w//CELL, h//CELL
print('TRACK-ONLY map (5px cells): #=track')
for cy in range(CH):
    row = ''
    for cx in range(CW):
        x0, x1 = cx*CELL, (cx+1)*CELL
        y0, y1 = cy*CELL, (cy+1)*CELL
        t = track[y0:y1, x0:x1].sum()
        if t > 8: row += '#'
        elif t > 0: row += '+'
        else: row += ' '
    if cy % 10 == 0:
        print(f'{cy*CELL:4d} ' + row)
    else:
        print('     ' + row)
