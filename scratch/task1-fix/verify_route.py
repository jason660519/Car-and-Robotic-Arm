import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60)).astype(np.uint8) * 255
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

# Real track centerline via: for each row/col, the longest black run
def longest_run(arr):
    best = (0, 0, 0)  # start, end, length
    start = None
    for i, v in enumerate(arr):
        if v > 0 and start is None: start = i
        elif v == 0 and start is not None:
            if i - start > best[2]: best = (start, i-1, i-start)
            start = None
    if start is not None:
        if len(arr) - start > best[2]: best = (start, len(arr)-1, len(arr)-start)
    return best

print('=== Real black track lines (longest runs) ===')
# Top horizontal: scan rows 60..110
for y in range(60, 115, 5):
    s, e, L = longest_run(black[y])
    if L > 100:
        print(f'row y={y}: x[{s}..{e}] len={L}px={L/10:.1f}cm center_x={(s+e)/2:.0f}')
# Right vertical: scan cols 940..1000
for x in range(940, 1001, 5):
    s, e, L = longest_run(black[:, x])
    if L > 60:
        print(f'col x={x}: y[{s}..{e}] len={L}px={L/10:.1f}cm center_y={(s+e)/2:.0f}')
# Stem near x=760: cols 740..780
for x in range(740, 781, 5):
    s, e, L = longest_run(black[:, x])
    if L > 80:
        print(f'stem col x={x}: y[{s}..{e}] len={L}px={L/10:.1f}cm')
# Roundabout: sample circle ring at radius ~150 from candidate centers
print('\n=== Roundabout black circle search ===')
best = None
for cx in range(200, 500, 10):
    for cy in range(200, 500, 10):
        ring_hit = 0; ring_tot = 0
        for ang_deg in range(0, 360, 6):
            a = np.radians(ang_deg)
            for rad in (140, 150, 160, 170, 180, 190):
                px = int(cx + rad*np.cos(a)); py = int(cy + rad*np.sin(a))
                if 0 <= px < w and 0 <= py < h:
                    ring_tot += 1
                    if black[py, px] > 0: ring_hit += 1
        score = ring_hit / max(ring_tot, 1)
        if best is None or score > best[0]:
            best = (score, cx, cy)
print('best ring fit: score=%.2f center=(%d,%d)' % best)

# Now verify red route segments: sample along each segment, check black under it
print('\n=== Red route vs black track ===')
route = [
    ('P1 stem', (760, 660), (760, 476)),
    ('P2 east', (760, 476), (860, 476)),
    ('ARC1', (860, 476), (990, 346)),
    ('P4 north', (990, 346), (990, 216)),
    ('ARC2', (990, 216), (860, 86)),
    ('P6 west', (860, 86), (360, 86)),
    ('ARC3', (360, 86), (230, 216)),
    ('P8 south', (230, 216), (230, 291)),
    ('P9 arc', (230, 291), (405, 466), 'arc', (405, 291), 175),
    ('P10 east', (405, 466), (760, 476)),
    ('P11 return', (760, 476), (760, 660)),
]
def on_black(px, py, rad=8):
    x0, x1 = max(0, px-rad), min(w-1, px+rad)
    y0, y1 = max(0, py-rad), min(h-1, py+rad)
    return bool((black[y0:y1+1, x0:x1+1] > 0).any())

for seg in route:
    name = seg[0]
    if seg[1] == seg[2]:
        continue
    if len(seg) > 4 and seg[3] == 'arc':
        # sample along circular arc from start angle to end angle (3/4 cw from 9 o'clock)
        cx, cy, R = seg[4], seg[5], seg[6]
        angs = np.linspace(180, 90, 60)  # from 9 o'clock to 6 o'clock clockwise via 12,3
        # cv2 sweep: 90..360 covers 6->9->12->3; travel should be 9->12->3->6 => angles 180..90 wrapping
        angs = np.array([a if a >= 0 else a + 360 for a in np.arange(180, -270, -6)])
        n_on = 0
        for a in angs:
            px = int(cx + R*np.cos(np.radians(a))); py = int(cy + R*np.sin(np.radians(a)))
            if on_black(px, py): n_on += 1
        print(f'{name}: arc center=({cx},{cy}) R={R}  on-track {n_on}/{len(angs)}')
    else:
        (x1,y1),(x2,y2) = seg[1], seg[2]
        n = 30; n_on = 0
        for i in range(n+1):
            t = i/n
            px, py = int(x1 + (x2-x1)*t), int(y1 + (y2-y1)*t)
            if on_black(px, py): n_on += 1
        # actual length
        L = np.hypot(x2-x1, y2-y1)
        print(f'{name}: drawn len={L:.0f}px={L/10:.1f}cm  on-track {n_on}/{n+1}')
