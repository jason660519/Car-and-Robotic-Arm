import cv2
import numpy as np

img = cv2.imread('/tmp/lf-cap5-raw.jpg')
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# 1) Where are dark bands in the ROI (y 0.1-1.0 => y 152-1520)?
# Scan every 40px row band: longest dark run < 100
print('dark run widths per row band (x full width):')
for y in range(152, 1520, 40):
    row = gray[y]
    dark = row < 100
    xs = np.where(dark)[0]
    if len(xs) == 0: continue
    runs = []
    s = xs[0]; p_ = xs[0]
    for x in xs[1:]:
        if x - p_ > 12:
            runs.append((s, p_)); s = x
        p_ = x
    runs.append((s, p_))
    # longest run + count of ~20-50px runs (2cm line candidates at this res)
    longest = max(runs, key=lambda r: r[1]-r[0])
    thin = [r for r in runs if 15 <= (r[1]-r[0]) <= 60]
    print(f'y={y:4d}: longest={longest[1]-longest[0]:4d}px [{longest[0]}..{longest[1]}]  thin-runs={len(thin)}')

# 2) Paper corners: detect large bright quadrilateral in the frame
bright = (gray > 170).astype(np.uint8)
n, lab, stats, cents = cv2.connectedComponentsWithStats(bright)
big = sorted([(stats[i][4], i) for i in range(1, n)], reverse=True)[:5]
print('\nlargest bright components (paper?):')
for area, i in big:
    x, y, ww, hh, a = stats[i]
    print(f'  bbox=({x},{y},{ww},{hh}) area={a} fill={a/(ww*hh):.2f}')
