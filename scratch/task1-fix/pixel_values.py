import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# histogram of dark pixels in bottom-right region
roi = gray[430:700, 440:900]
hist = np.histogram(roi, bins=16, range=(0, 255))[0]
print('gray histogram of bottom-right region:')
for i in range(16):
    print(f'  {i*16:3d}-{i*16+15:3d}: {hist[i]}')

# distinct dark levels: find local minima
dark = roi[roi < 150]
print('\ndark pixels < 150:', len(dark), ' mean:', dark.mean(), ' p10:', np.percentile(dark, 10), ' median:', np.median(dark))

# threshold at 60 (pure black track) vs 100 (text)
for t in (50, 70, 90, 110):
    m = (roi < t).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    big = [(stats[i][0], stats[i][1], stats[i][2], stats[i][3], stats[i][4]) for i in range(1, n) if stats[i][4] > 500]
    print(f'\nthreshold {t}: comps>{500}: {len(big)}')
    for b in sorted(big, key=lambda x: -x[4])[:8]:
        print(f'   bbox=({b[0]},{b[1]},{b[2]},{b[3]}) area={b[4]}')
