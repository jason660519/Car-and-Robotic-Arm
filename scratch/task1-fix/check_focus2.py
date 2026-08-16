import cv2
import numpy as np
img = cv2.imread('/tmp/lf-cap3-raw.jpg')
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
lap = cv2.Laplacian(gray, cv2.CV_64F)
print('frame %dx%d  Laplacian variance overall: %.0f' % (w, h, lap.var()))
print('paper band var: %.0f' % lap[300:900, 400:1700].var())
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
