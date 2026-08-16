import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

print('y    black runs x420-1000 (raw):')
for y in range(380, 530, 5):
    row = black[y, 420:1000]
    xs = np.where(row > 0)[0] + 420
    if len(xs) == 0:
        print(f'{y:4d}  -')
        continue
    runs = []
    s = xs[0]; p_ = xs[0]
    for x in xs[1:]:
        if x - p_ > 8:
            runs.append((s, p_)); s = x
        p_ = x
    runs.append((s, p_))
    rs = '  '.join(f'{a}-{b}' for a, b in runs if b-a >= 5)
    print(f'{y:4d}  {rs}')
