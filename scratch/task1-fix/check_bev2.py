import cv2
import numpy as np
img = cv2.imread('/tmp/lf-cap7-bev.jpg')
h, w = img.shape[:2]
print('BEV image:', w, 'x', h)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
chars = ' .:-=+*#%@'
CH, CW = 30, 50
for cy in range(CH):
    row = ''
    for cx in range(CW):
        x0, x1 = cx*w//CW, (cx+1)*w//CW
        y0, y1 = cy*h//CH, (cy+1)*h//CH
        m = gray[y0:y1, x0:x1].mean()
        row += chars[min(9, int(m/25.6))]
    print(f'{y0:4d} ' + row)
# dark band analysis
dark = gray < 100
print('\ndark fraction per row band:')
for y in range(0, h, max(h//12, 1)):
    band = dark[y:y+max(h//12,1)]
    print(f'  y={y:4d}: {100*band.mean():5.1f}%')
