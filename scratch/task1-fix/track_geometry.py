import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Isolate the 2cm black track: exclude very large black regions (poster border/text)
# Track width is ~20px; use morphology: black pixels that are NOT near the poster edge
black = (gray < 90).astype(np.uint8) * 255

# Border exclusion: the poster border is a thick black frame at the image edges.
# Erode with a big kernel to remove border+text, keep track (line width 20px survives erosion ~10px)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
track_core = cv2.morphologyEx(black, cv2.MORPH_OPEN, kernel)  # removes thin noise

# skeleton of track core
skel = cv2.ximgproc.thinning(track_core) if hasattr(cv2, 'ximgproc') else None
if skel is None:
    # manual skeleton via repeated erosion
    skel = np.zeros_like(track_core)
    tmp = track_core.copy()
    k = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
    while True:
        eroded = cv2.erode(tmp, k)
        opened = cv2.morphologyEx(eroded, cv2.MORPH_OPEN, k)
        skel |= (tmp & ~opened)
        tmp = eroded
        if cv2.countNonZero(tmp) == 0:
            break

cv2.imwrite('/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/task1-fix/track_core.png', track_core)
cv2.imwrite('/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/task1-fix/track_skeleton.png', skel)

# Connected components of track core
n, labels, stats, cents = cv2.connectedComponentsWithStats(track_core)
print('components:', n)
for i in range(1, n):
    x, y, ww, hh, area = stats[i]
    if area > 2000:
        print(f'  comp {i}: bbox=({x},{y},{ww},{hh}) area={area} center=({cents[i][0]:.0f},{cents[i][1]:.0f})')

# Find the roundabout: largest blob that is roughly circular. 
# Search black core for circles via Hough
circles = cv2.HoughCircles(track_core.astype(np.uint8), cv2.HOUGH_GRADIENT, dp=1.2, minDist=200,
                           param1=100, param2=40, minRadius=120, maxRadius=220)
if circles is not None:
    for c in circles[0]:
        print('Hough circle: center=(%.0f,%.0f) R=%.1f px -> D=%.1f cm' % (c[0], c[1], c[2], 2*c[2]/10))

# Row/column profile of track core to find horizontal/vertical lines
colp = (track_core > 0).sum(axis=0)
rowp = (track_core > 0).sum(axis=1)
# long horizontal runs (top edge ~y=86?)
for y in range(0, 700, 5):
    if rowp[y] > 400:
        print('long horizontal track at row y=%d width=%d px (%.1f cm)' % (y, rowp[y], rowp[y]/10))
for x in range(0, 1000, 5):
    if colp[x] > 300:
        print('long vertical track at col x=%d height=%d px (%.1f cm)' % (x, colp[x], colp[x]/10))
