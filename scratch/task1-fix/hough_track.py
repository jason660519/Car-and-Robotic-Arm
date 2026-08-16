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

lines = cv2.HoughLinesP(track, 1, np.pi/360, threshold=40, minLineLength=60, maxLineGap=12)
segs = []
for l in lines:
    x1, y1, x2, y2 = int(l[0]), int(l[1]), int(l[2]), int(l[3])
    L = np.hypot(x2-x1, y2-y1)
    ang = np.degrees(np.arctan2(y2-y1, x2-x1))
    segs.append((L, ang, x1, y1, x2, y2))
segs.sort(reverse=True)
print('top 40 longest lines:')
for L, ang, x1, y1, x2, y2 in segs[:40]:
    kind = 'H' if abs(ang) < 20 or abs(ang) > 160 else ('V' if 70 < abs(ang) < 110 else 'D')
    print(f'  {kind} len={L:5.0f}px ({L/10:4.1f}cm) ang={ang:6.1f}  ({x1:4d},{y1:4d})->({x2:4d},{y2:4d})')
