import cv2
import numpy as np

for name, p in [('raw', '/tmp/lf-cap-raw.jpg'), ('overlay', '/tmp/lf-cap-overlay.jpg')]:
    img = cv2.imread(p)
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    print(f'== {name}: {w}x{h}')
    print('brightness grid (mean gray per 8x6 block):')
    for by in range(6):
        row = ''
        for bx in range(8):
            y0, y1 = by*h//6, (by+1)*h//6
            x0, x1 = bx*w//8, (bx+1)*w//8
            m = gray[y0:y1, x0:x1].mean()
            row += f'{m:5.0f}'
        print('  ' + row)
    # dark fraction per row band
    dark = (gray < 100)
    print('dark(<100) fraction by row band (0-1520, every 190px):')
    for y in range(0, h, 190):
        band = dark[y:y+190]
        print(f'  y={y:4d}: {100*band.mean():5.1f}%')
