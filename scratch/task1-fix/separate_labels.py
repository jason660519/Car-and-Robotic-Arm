import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60)).astype(np.uint8) * 255
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Label text: red pixels on/inside white background. Route: red on dark bg.
# For each red pixel, check 3x3 neighborhood gray median.
route_red = red.copy()
ys, xs = np.where(red > 0)
for y, x in zip(ys, xs):
    y0, y1 = max(0,y-3), min(h-1,y+3)
    x0, x1 = max(0,x-3), min(w-1,x+3)
    if gray[y0:y1+1, x0:x1+1].mean() > 190:
        route_red[y, x] = 0  # label pixel

cv2.imwrite('/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/task1-fix/route_red_only.png', route_red)
print('route red pixels (excl. labels):', (route_red > 0).sum())

# zoom x 440..900, y 430..700 at 4px
X0, Y0, CELL = 440, 430, 4
CW, CH = 115, 68
print('\nBottom-right, ROUTE-ONLY red on track (#=track, X=route+track, R=route)')
for cy in range(CH):
    row = ''
    for cx in range(CW):
        x0, x1 = X0+cx*CELL, min(w, X0+(cx+1)*CELL)
        y0, y1 = Y0+cy*CELL, min(h, Y0+(cy+1)*CELL)
        rd = route_red[y0:y1, x0:x1].sum()
        t = (gray[y0:y1, x0:x1] < 100).sum()
        if rd > 20 and t > 20: row += 'X'
        elif rd > 20: row += 'R'
        elif t > 12: row += '#'
        elif t > 0: row += '+'
        else: row += ' '
    if cy % 5 == 0:
        print(f'{Y0+cy*CELL:4d} ' + row)
    else:
        print('     ' + row)

# Also full-map route red ascii (10px cells) for topology
print('\nFULL MAP route-only (10px): R=route, .=thin-black, #=black')
for cy in range(70):
    row = ''
    for cx in range(100):
        x0, x1 = cx*10, min(w, (cx+1)*10)
        y0, y1 = cy*10, min(h, (cy+1)*10)
        rd = route_red[y0:y1, x0:x1].sum()
        t = (gray[y0:y1, x0:x1] < 100).sum()
        if rd > 30 and t > 30: row += 'X'
        elif rd > 30: row += 'R'
        elif t > 60: row += '#'
        elif t > 15: row += '.'
        else: row += ' '
    print(f'{cy*10:4d} ' + row)
