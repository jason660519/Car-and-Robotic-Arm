import cv2
import numpy as np

for name, p in [('bev-t', '/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/line-follow-2026-08-15/track-bev-phone-t-junction.jpg'),
                ('quad-t', '/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/line-follow-2026-08-15/track-quad-phone-t-junction.jpg')]:
    img = cv2.imread(p)
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    print(f'== {name}: {w}x{h}')
    # coarse gradient view
    chars = ' .:-=+*#%@'
    CH, CW = 30, 40
    for cy in range(CH):
        row = ''
        for cx in range(CW):
            x0, x1 = cx*w//CW, (cx+1)*w//CW
            y0, y1 = cy*h//CH, (cy+1)*h//CH
            m = gray[y0:y1, x0:x1].mean()
            row += chars[min(9, int(m/25.6))]
        print(f'{y0:4d} ' + row)
    print()
