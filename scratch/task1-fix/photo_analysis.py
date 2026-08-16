import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/media__1786840258952.jpg'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# The poster is bright paper on a darker table. Find bright region.
bright = (gray > 200).astype(np.uint8) * 255
n, lab, stats, cents = cv2.connectedComponentsWithStats(bright)
big = sorted([(i, stats[i]) for i in range(1, n)], key=lambda c: -c[1][4])[:6]
print('bright components:')
for i, s in big:
    x, y, ww, hh, area = s
    print(f'  ({x},{y},{ww},{hh}) area={area} frac={area/(ww*hh):.2f}')

# Look at the mid-bright poster vs table
mid = ((gray > 150) & (gray < 210)).astype(np.uint8) * 255
n2, lab2, stats2, cents2 = cv2.connectedComponentsWithStats(mid)
big2 = sorted([(i, stats2[i]) for i in range(1, n2)], key=lambda c: -c[1][4])[:6]
print('\nmid components:')
for i, s in big2:
    x, y, ww, hh, area = s
    print(f'  ({x},{y},{ww},{hh}) area={area}')

# Where is the poster? Sample the photo: brightness histogram per region
print('\nMean gray by 128x128 blocks:')
for y in range(0, h, 128):
    row = ''
    for x in range(0, w, 128):
        m = gray[y:y+128, x:x+128].mean()
        row += f'{m:4.0f} '
    print(f'y={y:4d}: {row}')
