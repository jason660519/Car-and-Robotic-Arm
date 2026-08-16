import cv2
import numpy as np

p = '/tmp/lf-cap-raw.jpg'
img = cv2.imread(p)
h, w = img.shape[:2]
print('frame:', w, 'x', h)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
chars = ' .:-=+*#%@'
CH, CW = 50, 66
for cy in range(CH):
    row = ''
    for cx in range(CW):
        x0, x1 = cx*w//CW, (cx+1)*w//CW
        y0, y1 = cy*h//CH, (cy+1)*h//CH
        m = gray[y0:y1, x0:x1].mean()
        row += chars[min(9, int(m/25.6))]
    print(f'{y0:4d} ' + row)
