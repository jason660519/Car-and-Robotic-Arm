import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

# For rows 100..480, count black runs in x 880..999
print('y    black runs x880-999 (raw)')
for y in range(100, 481, 10):
    row = black[y, 880:1000]
    xs = np.where(row > 0)[0] + 880
    if len(xs) == 0:
        print(f'{y:4d}  -')
        continue
    runs = []
    s = xs[0]; p_ = xs[0]
    for x in xs[1:]:
        if x - p_ > 6:
            runs.append((s, p_)); s = x
        p_ = x
    runs.append((s, p_))
    print(f'{y:4d}  ' + '  '.join(f'{a}-{b}' for a, b in runs))
