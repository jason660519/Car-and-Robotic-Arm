import cv2
import numpy as np

img = cv2.imread('/tmp/lf-cap7-bev.jpg')
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
print('BEV:', w, 'x', h)

# find dark bands per row (BEV: 2cm line = 10px)
print('\ndark bands (<100) per row band (every 20px):')
for y in range(0, h, 20):
    row = gray[y]
    dark = row < 100
    xs = np.where(dark)[0]
    if len(xs) == 0:
        continue
    runs = []
    s = xs[0]; p_ = xs[0]
    for x in xs[1:]:
        if x - p_ > 6:
            runs.append((s, p_)); s = x
        p_ = x
    runs.append((s, p_))
    good = [(a, b) for a, b in runs if b-a >= 5]
    if good:
        print(f'  y={y:3d}: ' + '  '.join(f'{a}-{b}({b-a})' for a, b in good))
