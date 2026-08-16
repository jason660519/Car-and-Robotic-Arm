import cv2
import numpy as np

for name, p in [('cap2', '/tmp/lf-cap2-raw.jpg'), ('cap3', '/tmp/lf-cap3-raw.jpg')]:
    img = cv2.imread(p)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    print(f'== {name}')
    regions = {
        'texture band y900-990 x400-1700': gray[900:990, 400:1700],
        'texture band lap': lap[900:990, 400:1700].var(),
        'paper y1020-1130': gray[1020:1130, 400:1700].var(),
        'whole': gray.var(),
    }
    r = {}
    r['texture mean'] = gray[900:990, 400:1700].mean()
    r['texture std'] = gray[900:990, 400:1700].std()
    r['texture lap var'] = lap[900:990, 400:1700].var()
    r['whole lap var'] = lap.var()
    print('  ', r)
