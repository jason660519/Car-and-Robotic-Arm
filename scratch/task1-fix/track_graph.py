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

# skeleton
skel = np.zeros_like(track)
tmp = track.copy()
k = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
while True:
    eroded = cv2.erode(tmp, k)
    opened = cv2.morphologyEx(eroded, cv2.MORPH_OPEN, k)
    skel |= (tmp & ~opened)
    tmp = eroded
    if cv2.countNonZero(tmp) == 0:
        break
cv2.imwrite('/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/task1-fix/track_skel3.png', skel)

# junctions: pixels with >=3 neighbors in 8-connectivity
ys, xs = np.where(skel > 0)
k8 = np.ones((3,3), np.uint8); k8[1,1] = 0
nb = cv2.filter2D(skel.astype(np.float32), -1, k8, borderType=cv2.BORDER_CONSTANT)
junc = ((skel > 0) & (nb >= 3)).astype(np.uint8)
jy, jx = np.where(junc > 0)
print('junction pixels:', len(jy))
# cluster junctions
seen = set()
clusters = []
for y, x in zip(jy, jx):
    if (y, x) in seen: continue
    stack = [(y, x)]; seen.add((y, x)); comp = []
    while stack:
        cy, cx = stack.pop(); comp.append((cy, cx))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny, nx = cy+dy, cx+dx
                if 0 <= ny < h and 0 <= nx < w and junc[ny, nx] and (ny, nx) not in seen:
                    seen.add((ny, nx)); stack.append((ny, nx))
    clusters.append((np.mean([c[0] for c in comp]), np.mean([c[1] for c in comp]), len(comp)))
clusters.sort(key=lambda c: c[1])
print('junction clusters (y, x, size):')
for cy, cx, n in clusters:
    print(f'  ({cy:.0f}, {cx:.0f}) size={n}')

# endpoints: pixels with exactly 1 neighbor
endp = ((skel > 0) & (nb == 1)).astype(np.uint8)
ey, ex = np.where(endp > 0)
print('\nendpoints:', len(ey))
for y, x in zip(ey, ex):
    print(f'  ({y}, {x})')
