import cv2
import numpy as np

img = cv2.imread('/tmp/lf-cap5-raw.jpg')
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# ROI y 486-881 (0.32-0.58). Find dark bands per row, cluster by x.
bands = {}  # (x_bin) -> count of rows seeing a band there
for y in range(486, 881, 8):
    row = gray[y]
    dark = row < 100
    xs = np.where(dark)[0]
    runs = []
    if len(xs):
        s = xs[0]; p_ = xs[0]
        for x in xs[1:]:
            if x - p_ > 10:
                runs.append((s, p_)); s = x
            p_ = x
        runs.append((s, p_))
    for a, b in runs:
        if 12 <= (b-a) <= 60:  # 2cm-line candidates (~20-40px at this res)
            key = ((a+b)//2)//50
            bands.setdefault(key, []).append((y, a, b))
print('2cm-line candidates by x-bin (center x bin, count, examples):')
for k in sorted(bands):
    rows = bands[k]
    ys = [r[0] for r in rows]
    print(f'  x~{k*50+25}: rows={min(ys)}-{max(ys)} n={len(rows)} width~{[r[2]-r[1] for r in rows[:3]]}')

# and the big dark block at x~1105-1256, y 1072+: which rows?
print('\nbig dark block x~1100-1260 present at rows:')
for y in range(900, 1520, 20):
    seg = gray[y, 1100:1260]
    frac = (seg < 100).mean()
    if frac > 0.5:
        print(f'  y={y}: {100*frac:.0f}% dark')
