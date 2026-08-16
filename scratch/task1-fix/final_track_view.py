import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60))
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black_nr = ((gray < 100) & ~red).astype(np.uint8) * 255
dt = cv2.distanceTransform(black_nr, cv2.DIST_L2, 5)
track = ((dt >= 6) & (dt <= 17)).astype(np.uint8) * 255
track = cv2.bitwise_and(black_nr, cv2.dilate(track, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11,11))))
cv2.imwrite('/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/task1-fix/track_final.png', track)

n, lab, stats, cents = cv2.connectedComponentsWithStats(track)
print('components (no-red track):', n)
comps = []
for i in range(1, n):
    x, y, ww, hh, area = stats[i]
    if area > 600:
        comps.append((i, x, y, ww, hh, area))
comps.sort(key=lambda c: -c[5])
for i, x, y, ww, hh, area in comps[:18]:
    print(f'  comp {i}: bbox=({x},{y},{ww},{hh}) area={area}')

# Full map view at 10px
print('\nTRUE TRACK (no red), 10px cells:')
for cy in range(70):
    row = ''
    for cx in range(100):
        x0, x1 = cx*10, min(w, (cx+1)*10)
        y0, y1 = cy*10, min(h, (cy+1)*10)
        t = track[y0:y1, x0:x1].sum()
        if t > 40: row += '#'
        elif t > 12: row += '+'
        else: row += ' '
    print(f'{cy*10:4d} ' + row)
