import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60)).astype(np.uint8) * 255
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

# Track pixels = black pixels within 18px of red route
dt_red = cv2.distanceTransform(red, cv2.DIST_L2, 5)
corridor = (dt_red <= 18).astype(np.uint8) * 255
track_corridor = cv2.bitwise_and(black, corridor)
cv2.imwrite('/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/task1-fix/track_corridor.png', track_corridor)

# Skeletonize corridor
skel = np.zeros_like(track_corridor)
tmp = track_corridor.copy()
k = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
while True:
    eroded = cv2.erode(tmp, k)
    opened = cv2.morphologyEx(eroded, cv2.MORPH_OPEN, k)
    skel |= (tmp & ~opened)
    tmp = eroded
    if cv2.countNonZero(tmp) == 0:
        break
cv2.imwrite('/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/task1-fix/track_corridor_skel.png', skel)
print('corridor skeleton pixels:', cv2.countNonZero(skel))

ys, xs = np.where(skel > 0)
print('skel bbox: x[%d..%d] y[%d..%d]' % (xs.min(), xs.max(), ys.min(), ys.max()))

# ===== Measure the route segments from actual track =====
# Phase 1 stem: vertical line near x=760, y in [470, 665]
col = skel[:, 740:780].sum(axis=0)
ys_stem = np.where(col > 0)[0]
if len(ys_stem):
    print('\nStem (x~760): y range %d..%d, length %.1f px = %.1f cm' % (ys_stem.min(), ys_stem.max(), ys_stem.max()-ys_stem.min(), (ys_stem.max()-ys_stem.min())/10))

# Phase 2: horizontal near y=476 from x=760 eastward
row = skel[470:485, :].sum(axis=0)
xs_p2 = np.where(row > 0)[0]
if len(xs_p2):
    print('Phase2 row (y~476): x range %d..%d, length %.1f px = %.1f cm' % (xs_p2.min(), xs_p2.max(), xs_p2.max()-xs_p2.min(), (xs_p2.max()-xs_p2.min())/10))

# Phase 4: vertical near x=990
col = skel[:, 980:1000].sum(axis=0)
ys_p4 = np.where(col > 0)[0]
if len(ys_p4):
    print('Phase4 col (x~990): y range %d..%d, length %.1f px = %.1f cm' % (ys_p4.min(), ys_p4.max(), ys_p4.max()-ys_p4.min(), (ys_p4.max()-ys_p4.min())/10))

# Phase 6: top horizontal near y=86
for yy in (80, 86, 90, 95, 100):
    row = skel[max(0,yy-4):min(h,yy+5), :].sum(axis=0)
    xs6 = np.where(row > 0)[0]
    if len(xs6) > 100:
        print('Phase6 row (y~%d): x range %d..%d, length %.1f px = %.1f cm' % (yy, xs6.min(), xs6.max(), xs6.max()-xs6.min(), (xs6.max()-xs6.min())/10))
        break

# Phase 8: vertical near x=230
col = skel[:, 220:240].sum(axis=0)
ys8 = np.where(col > 0)[0]
if len(ys8):
    print('Phase8 col (x~230): y range %d..%d, length %.1f px = %.1f cm' % (ys8.min(), ys8.max(), ys8.max()-ys8.min(), (ys8.max()-ys8.min())/10))

# Phase 10: from roundabout east to T - look at row y~466-476
for yy in (466, 470, 476):
    row = skel[max(0,yy-3):min(h,yy+4), :].sum(axis=0)
    xs10 = np.where(row > 0)[0]
    if len(xs10) > 50:
        print('Phase10 row (y~%d): x range %d..%d, length %.1f px = %.1f cm' % (yy, xs10.min(), xs10.max(), xs10.max()-xs10.min(), (xs10.max()-xs10.min())/10))

# ===== Roundabout: red pixels angular coverage around drawn center (405,291) R=175 =====
cx, cy, R = 405, 291, 175
ysr, xsr = np.where(red > 0)
ang = np.degrees(np.arctan2(ysr - cy, xsr - cx)) % 360
rad = np.hypot(xsr - cx, ysr - cy)
on_ring = (rad > 150) & (rad < 200)
ang_ring = ang[on_ring]
print('\nRoundabout red ring pixels around (405,291):', len(ang_ring))
if len(ang_ring):
    # coverage histogram in 30-deg bins
    hist, edges = np.histogram(ang_ring, bins=12, range=(0, 360))
    for i, c in enumerate(hist):
        if c > 0:
            print('  angle bin %3d-%3d deg (o\'clock ~%s): %d px' % (int(edges[i]), int(edges[i+1]), str(int((edges[i]+15)/30) % 12 + 1) + 'h' if False else f'{int(edges[i])}-{int(edges[i+1])}'), c)

# Which angles are MISSING on the red ring?
bins = np.histogram(ang_ring, bins=36, range=(0,360))[0]
missing = [i*10 for i, c in enumerate(bins) if c == 0]
print('missing 10-deg bins:', missing)

# ===== Where is the actual roundabout black track? =====
# Find black circle candidates on left side within y 100..600
ysb, xsb = np.where(black > 0)
left = np.column_stack([ysb[xsb<600], xsb[xsb<600]])
# distance transform to find thick line center
dtb = cv2.distanceTransform(black, cv2.DIST_L2, 5)
thick = (dtb >= 6).astype(np.uint8) * 255
n, lab, stats, cents = cv2.connectedComponentsWithStats(thick)
print('\nthick black components (>=6px from edge):')
comps = [(i, stats[i]) for i in range(1, n) if stats[i][4] > 2000]
comps.sort(key=lambda c: -c[1][4])
for i, s in comps[:10]:
    x, y, ww, hh, area = s
    print(f'  comp {i}: bbox=({x},{y},{ww},{hh}) area={area} center=({cents[i][0]:.0f},{cents[i][1]:.0f})')
