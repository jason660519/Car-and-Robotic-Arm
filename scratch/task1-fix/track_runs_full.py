import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255
dt = cv2.distanceTransform(black, cv2.DIST_L2, 5)
track = ((dt >= 6) & (dt <= 17)).astype(np.uint8) * 255
track = cv2.bitwise_and(black, cv2.dilate(track, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11,11))))

def runs(row, minlen=8):
    xs = np.where(row > 0)[0]
    if len(xs) == 0: return []
    out = []
    s = xs[0]; p_ = xs[0]
    for x in xs[1:]:
        if x - p_ > 8:
            out.append((s, p_)); s = x
        p_ = x
    out.append((s, p_))
    return [r for r in out if r[1]-r[0] >= minlen]

print('y      track runs (x0-x1)')
for y in range(40, 700, 10):
    rs = runs(track[y])
    if rs:
        s = '  '.join(f'{a}-{b}' for a, b in rs)
        print(f'{y:4d}   {s}')
