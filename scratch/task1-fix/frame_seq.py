import cv2
import numpy as np
for name in ('frame-00010.jpg', 'frame-00040.jpg', 'frame-00070.jpg'):
    img = cv2.imread('/tmp/lf-frames3/' + name)
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    print(f'== {name} ({w}x{h}) dark<100: {100*(gray<100).mean():.0f}%')
