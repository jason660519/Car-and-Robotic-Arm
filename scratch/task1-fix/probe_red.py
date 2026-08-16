import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60)).astype(np.uint8) * 255
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

# For a given probe point, report red presence in window
def probe(name, x, y, rw=10):
    x0, x1 = max(0, x-rw), min(w-1, x+rw)
    y0, y1 = max(0, y-rw), min(h-1, y+rw)
    redc = red[y0:y1+1, x0:x1+1].sum()
    blc = black[y0:y1+1, x0:x1+1].sum()
    print(f'{name}: window ({x0},{y0})-({x1},{y1}) red={redc} black={blc}')

print('=== Probe the drawn route coordinates ===')
probe('P1 stem mid (760,560)', 760, 560)
probe('P1 stem top (760,476)', 760, 476)
probe('P2 east mid (800,476)', 800, 476)
probe('P2 east end (860,476)', 860, 476)
probe('ARC1 mid (920,410)', 920, 410)
probe('P4 north mid (990,280)', 990, 280)
probe('ARC2 mid (925,150)', 925, 150)
probe('P6 west mid (600,86)', 600, 86)
probe('ARC3 mid (290,150)', 290, 150)
probe('P8 south (230,250)', 230, 250)
probe('P8 south (230,280)', 230, 280)
probe('P9 ring left (230,291)', 230, 291)
probe('P9 ring bottom (405,466)', 405, 466)
probe('P9 ring right (580,291)', 580, 291)
probe('P9 ring top (405,116)', 405, 116)
probe('P10 east mid (580,470)', 580, 470)
probe('P10 east end (760,476)', 760, 476)

print('\n=== Where is the actual red line near Phase 8? ===')
# scan rows 200..300, find red x-extents
for y in (200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320):
    row_red = red[y]
    xs = np.where(row_red > 0)[0]
    if len(xs):
        # cluster into runs
        runs = []
        s = xs[0]; p_ = xs[0]
        for x in xs[1:]:
            if x - p_ > 8:
                runs.append((s, p_)); s = x
            p_ = x
        runs.append((s, p_))
        runs = [f'{a}-{b}' for a,b in runs if b-a > 3]
        print(f'y={y}: red x-runs: {runs}')
    else:
        print(f'y={y}: no red')

print('\n=== Where is the actual red near the roundabout ring? (y=291) ===')
row_red = red[291]
xs = np.where(row_red > 0)[0]
runs = []
s = xs[0]; p_ = xs[0]
for x in xs[1:]:
    if x - p_ > 8:
        runs.append((s, p_)); s = x
    p_ = x
runs.append((s, p_))
print('red x-runs at y=291:', runs)

print('\n=== Roundabout black ring: where is it? Scan rows ===')
for y in (240, 260, 280, 300, 320, 340, 360, 380, 400, 420, 440, 460, 480, 500, 520, 540, 560):
    rowb = black[y]
    xs = np.where(rowb > 0)[0]
    if len(xs) < 5: 
        print(f'y={y}: no black'); continue
    runs = []
    s = xs[0]; p_ = xs[0]
    for x in xs[1:]:
        if x - p_ > 10:
            runs.append((s, p_)); s = x
        p_ = x
    runs.append((s, p_))
    big = [f'{a}-{b}({b-a})' for a,b in runs if b-a > 15]
    print(f'y={y}: black runs: {big}')
