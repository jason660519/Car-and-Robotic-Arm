import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

# ring pixels around (292,412) R=180
cx, cy, R = 292, 412, 180
ys, xs = np.where(black > 0)
rad = np.hypot(xs - cx, ys - cy)
sel = (rad > R - 10) & (rad < R + 10)
pts = np.column_stack([ys[sel], xs[sel]]).astype(np.float32)
print('ring pixels:', len(pts))
ell = cv2.fitEllipse(pts)
(ex, ey), (MA, ma), ang = ell
print('ellipse fit: center=(%.1f, %.1f) axes=(%.1f, %.1f) angle=%.1f  aspect=%.3f' % (ex, ey, MA, ma, ang, min(MA,ma)/max(MA,ma)))
print('=> aspect near 1.0 means warp is undistorted (roundabout stays circular)')

# Where exactly does the roundabout connect to the outer loop?
# Find the entrance: black track extending north from the circle top (292,232)
print('\nblack pixels column profile x=292:')
col = black[:, 292]
# print transitions
for y in range(150, 600, 10):
    c = col[y:y+10].sum()
    if c > 0:
        print(f'  y={y}-{y+10}: {c}/10')
