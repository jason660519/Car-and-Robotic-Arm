import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60)).astype(np.uint8) * 255
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

def longest_run(arr):
    best = (0, 0, 0)
    start = None
    for i, v in enumerate(arr):
        if v > 0 and start is None: start = i
        elif v == 0 and start is not None:
            if i - start > best[2]: best = (start, i-1, i-start)
            start = None
    if start is not None and len(arr) - start > best[2]:
        best = (start, len(arr)-1, len(arr)-start)
    return best

print('=== Stem (x 730..790) ===')
for x in range(730, 791, 4):
    s, e, L = longest_run(black[:, x])
    if L > 80:
        print(f'col x={x}: y[{s}..{e}] len={L/10:.1f}cm')

print('\n=== Horizontal line at y 460..500 (return path) ===')
for y in range(440, 510, 5):
    s, e, L = longest_run(black[y])
    if L > 100:
        print(f'row y={y}: x[{s}..{e}] len={L/10:.1f}cm')

print('\n=== Left verticals x 200..260 (Phase 8) ===')
for x in range(200, 261, 4):
    s, e, L = longest_run(black[:, x])
    if L > 30:
        print(f'col x={x}: y[{s}..{e}] len={L/10:.1f}cm')

print('\n=== Roundabout black ring search (score, cx, cy, R) ===')
cands = []
for cx in range(220, 520, 12):
    for cy in range(150, 500, 12):
        for R in (120, 140, 160, 180, 200):
            hit = 0; tot = 0
            for a in range(0, 360, 4):
                px = int(cx + R*np.cos(np.radians(a))); py = int(cy + R*np.sin(np.radians(a)))
                if 0 <= px < w and 0 <= py < h:
                    tot += 1
                    if black[py, px] > 0: hit += 1
            score = hit/tot
            if score > 0.75:
                cands.append((score, cx, cy, R))
cands.sort(reverse=True)
for c in cands[:8]:
    print('  score=%.2f center=(%d,%d) R=%d D=%.1fcm' % c)

print('\n=== Red route vs black track ===')
def on_black(px, py, rad=8):
    x0, x1 = max(0, px-rad), min(w-1, px+rad)
    y0, y1 = max(0, py-rad), min(h-1, py+rad)
    return bool((black[y0:y1+1, x0:x1+1] > 0).any())

def line_check(name, x1, y1, x2, y2):
    n = 40; n_on = 0
    for i in range(n+1):
        t = i/n
        px, py = int(x1 + (x2-x1)*t), int(y1 + (y2-y1)*t)
        if on_black(px, py): n_on += 1
    L = np.hypot(x2-x1, y2-y1)
    print(f'{name}: drawn {L/10:.1f}cm  on-track {n_on}/{n+1}')

line_check('P1 stem', 760, 660, 760, 476)
line_check('P2 east', 760, 476, 860, 476)
line_check('P4 north', 990, 346, 990, 216)
line_check('P6 west', 860, 86, 360, 86)
line_check('P8 south', 230, 216, 230, 291)
line_check('P10 east', 405, 466, 760, 476)
line_check('P11 return', 760, 476, 760, 660)

# Roundabout drawn arc: which angles of the red ring are present?
cx, cy, R = 405, 291, 175
ysr, xsr = np.where(red > 0)
rad = np.hypot(xsr - cx, ysr - cy)
ang = np.degrees(np.arctan2(ysr - cy, xsr - cx)) % 360
sel = (rad > 150) & (rad < 200)
ang_sel = ang[sel]
hist = np.histogram(ang_sel, bins=36, range=(0, 360))[0]
present = [i*10 for i, c in enumerate(hist) if c > 20]
missing = [i*10 for i, c in enumerate(hist) if c <= 20]
print(f'\nDrawn roundabout arc: {len(ang_sel)} ring pixels, present 10deg bins: {present}')
print(f'missing bins: {missing}')

# Which angles does the REAL track circle cover (best candidate center)?
if cands:
    sc, ccx, ccy, cR = cands[0]
    ysrb, xsrb = np.where(black > 0)
    radb = np.hypot(xsrb - ccx, ysrb - ccy)
    angb = np.degrees(np.arctan2(ysrb - ccy, xsrb - ccx)) % 360
    selb = (radb > cR-8) & (radb < cR+8)
    histb = np.histogram(angb[selb], bins=36, range=(0, 360))[0]
    presentb = [i*10 for i, c in enumerate(histb) if c > 50]
    missingb = [i*10 for i, c in enumerate(histb) if c <= 50]
    print(f'\nReal track ring center=({ccx},{ccy}) R={cR}: present bins {presentb}')
    print(f'real track missing bins: {missingb}')
