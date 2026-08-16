import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Try multiple thresholds to understand the image
for t in (70, 90, 110, 130, 150):
    m = (gray < t).astype(np.uint8) * 255
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    big = [s for s in stats[1:] if s[4] > 3000]
    print(f'thresh {t}: black px {(m>0).sum()}, big comps {len(big)}')

# Use t=110 for track (line is solid black, text is grayish)
t = 110
black = (gray < t).astype(np.uint8) * 255

# Track line width ~20px: keep pixels whose local line width is 8..35 px.
# Use distance transform: track center has dt ~10
dt = cv2.distanceTransform(black, cv2.DIST_L2, 5)
line = ((dt >= 6) & (dt <= 22)).astype(np.uint8) * 255  # center strip of 12..44px-wide features
# Also keep full track body: within 12px of the center strip
body = cv2.dilate(line, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13,13)))
body = cv2.bitwise_and(black, body)

n, lab, stats, cents = cv2.connectedComponentsWithStats(body)
print('\ntrack-body components:')
comps = []
for i in range(1, n):
    x, y, ww, hh, area = stats[i]
    if area > 500:
        comps.append((i, x, y, ww, hh, area))
comps.sort(key=lambda c: -c[5])
for i, x, y, ww, hh, area in comps[:15]:
    print(f'  comp {i}: bbox=({x},{y},{ww},{hh}) area={area} center=({cents[i][0]:.0f},{cents[i][1]:.0f})')

cv2.imwrite('/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/task1-fix/track_body.png', body)

# Now skeletonize the body mask
skel = np.zeros_like(body)
tmp = body.copy()
k = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
while True:
    eroded = cv2.erode(tmp, k)
    opened = cv2.morphologyEx(eroded, cv2.MORPH_OPEN, k)
    skel |= (tmp & ~opened)
    tmp = eroded
    if cv2.countNonZero(tmp) == 0:
        break
cv2.imwrite('/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/task1-fix/track_skeleton2.png', skel)
print('\nskeleton pixels:', cv2.countNonZero(skel))

# Fit the roundabout: find circle on the left side (x < 500)
pts = np.column_stack(np.where(skel > 0))  # (y, x)
left = pts[pts[:, 1] < 500]
print('left-side skeleton points:', len(left))

# Simple circle fit via algebraic fit
def fit_circle(pts):
    x = pts[:, 1].astype(np.float64); y = pts[:, 0].astype(np.float64)
    A = np.column_stack([2*x, 2*y, np.ones_like(x)])
    b = x*x + y*y
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy, c = sol
    R = np.sqrt(c + cx*cx + cy*cy)
    return cx, cy, R

if len(left) > 10:
    cx, cy, R = fit_circle(left)
    print(f'left-side circle fit: center=({cx:.1f},{cy:.1f}) R={R:.1f}px D={2*R/10:.1f}cm')
    resid = np.hypot(left[:,1]-cx, left[:,0]-cy) - R
    print(f'  fit residual: rms={np.sqrt((resid**2).mean()):.1f}px max={np.abs(resid).max():.1f}px')

# Fit ellipse to left points (circularity check)
if len(left) > 20:
    ell = cv2.fitEllipse(left.astype(np.float32))
    (ex, ey), (MA, ma), ang = ell
    print(f'left-side ellipse: center=({ex:.1f},{ey:.1f}) axes=({MA:.1f},{ma:.1f}) angle={ang:.1f}  aspect={MA/max(ma,1e-9):.2f}')
