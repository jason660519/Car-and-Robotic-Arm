import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60)).astype(np.uint8) * 255
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 90).astype(np.uint8) * 255

# distance from every pixel to nearest black track pixel
dt = cv2.distanceTransform(black, cv2.DIST_L2, 5)
ys, xs = np.where(red > 0)
d_red_to_black = dt[ys, xs]
print('red pixels total:', len(xs))
print('median dist red->black track: %.1f px (%.1f cm)' % (np.median(d_red_to_black), np.median(d_red_to_black)/10))
print('mean   dist red->black track: %.1f px (%.1f cm)' % (d_red_to_black.mean(), d_red_to_black.mean()/10))
for t in (5, 10, 15, 20, 30, 40, 50):
    print('  red pixels > %d px (%.1f cm) from track: %d (%.1f%%)' % (t, t/10, (d_red_to_black > t).sum(), 100*(d_red_to_black > t).mean()))

# black track bbox
ys2, xs2 = np.where(black > 0)
print('\nblack track bbox: x[%d..%d] y[%d..%d]' % (xs2.min(), xs2.max(), ys2.min(), ys2.max()))
print('track bbox size: %d x %d px -> %.1f x %.1f cm' % (xs2.max()-xs2.min(), ys2.max()-ys2.min(), (xs2.max()-xs2.min())/10, (ys2.max()-ys2.min())/10))

# Where is the track actually located? Row/col profiles
col_profile = black.sum(axis=0)
row_profile = black.sum(axis=1)
# find big gaps in black track columns (to see if track reaches frame edges)
print('\ntrack present in leftmost 50px columns:', (col_profile[:50] > 0).sum(), '/50')
print('track present in rightmost 50px columns:', (col_profile[-50:] > 0).sum(), '/50')
print('track present in top 50px rows:', (row_profile[:50] > 0).sum(), '/50')
print('track present in bottom 50px rows:', (row_profile[-50:] > 0).sum(), '/50')

# Save a distance-heatmap debug image: red pixels colored by distance to track
debug = img.copy()
for y, x, d in zip(ys, xs, d_red_to_black):
    if d > 12:
        cv2.circle(debug, (int(x), int(y)), 3, (0, 255, 255), -1)  # yellow = far from track
    elif d > 5:
        cv2.circle(debug, (int(x), int(y)), 2, (255, 255, 0), -1)  # cyan = slightly off
cv2.imwrite('/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/task1-fix/red_vs_track_debug.png', debug)
print('\nsaved red_vs_track_debug.png (yellow=far, cyan=slightly off)')
