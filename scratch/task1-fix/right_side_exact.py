import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60)).astype(np.uint8) * 255
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

def runs_of(mask_row, minlen=5):
    xs = np.where(mask_row > 0)[0]
    if len(xs) == 0: return []
    runs = []
    s = xs[0]; p_ = xs[0]
    for x in xs[1:]:
        if x - p_ > 6:
            runs.append((s, p_)); s = x
        p_ = x
    runs.append((s, p_))
    return [f'{a}-{b}' for a, b in runs if b-a >= minlen]

print('y     black-runs(x>=880)        red-runs(x>=880)')
for y in range(100, 401, 10):
    br = runs_of(black[y]); rr = runs_of(red[y])
    br = [x for x in br if int(x.split('-')[0]) >= 880]
    rr = [x for x in rr if int(x.split('-')[0]) >= 880]
    print(f'{y:4d}  {str(br):45s} {rr}')
