import cv2
import numpy as np
img = cv2.imread('/tmp/lf-cap-live.jpg')
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
print('live frame:', w, 'x', h)
chars = ' .:-=+*#%@'
CH, CW = 40, 60
for cy in range(CH):
    row = ''
    for cx in range(CW):
        x0, x1 = cx*w//CW, (cx+1)*w//CW
        y0, y1 = cy*h//CH, (cy+1)*h//CH
        m = gray[y0:y1, x0:x1].mean()
        row += chars[min(9, int(m/25.6))]
    print(f'{y0:4d} ' + row)
