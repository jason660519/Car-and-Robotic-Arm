import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60)).astype(np.uint8) * 255
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

# Fine search for black ring: center grid 100..600, radius 100..240 step 10
best = []
for cx in range(100, 600, 8):
    for cy in range(100, 600, 8):
        for R in range(100, 241, 10):
            hit = 0; tot = 0
            for a in range(0, 360, 3):
                px = int(cx + R*np.cos(np.radians(a))); py = int(cy + R*np.sin(np.radians(a)))
                if 0 <= px < w and 0 <= py < h:
                    tot += 1
                    if black[py, px] > 0: hit += 1
            if tot and hit/tot > 0.5:
                best.append((hit/tot, cx, cy, R))
best.sort(reverse=True)
print('best black rings (score, cx, cy, R):')
for s, cx, cy, R in best[:12]:
    print(f'  {s:.2f} center=({cx},{cy}) R={R} D={2*R/10:.1f}cm')

# Same search but on red
bestr = []
for cx in range(100, 600, 8):
    for cy in range(100, 600, 8):
        for R in range(100, 241, 10):
            hit = 0; tot = 0
            for a in range(0, 360, 3):
                px = int(cx + R*np.cos(np.radians(a))); py = int(cy + R*np.sin(np.radians(a)))
                if 0 <= px < w and 0 <= py < h:
                    tot += 1
                    if red[py, px] > 0: hit += 1
            if tot and hit/tot > 0.35:
                bestr.append((hit/tot, cx, cy, R))
bestr.sort(reverse=True)
print('\nbest RED rings (drawn route):')
for s, cx, cy, R in bestr[:8]:
    print(f'  {s:.2f} center=({cx},{cy}) R={R} D={2*R/10:.1f}cm')

# Coverage of black ring for the drawn center (405,291) at various R
print('\nblack ring coverage around drawn center (405,291):')
for R in (130, 150, 175, 190, 210):
    hit = tot = 0
    for a in range(0, 360, 3):
        px = int(405 + R*np.cos(np.radians(a))); py = int(291 + R*np.sin(np.radians(a)))
        tot += 1
        if black[py, px] > 0: hit += 1
    print(f'  R={R}: {hit}/{tot} = {hit/tot:.2f}')

# Coverage of black ring around Hough center (289,385) R=151
print('\nblack ring coverage around Hough center (289,385):')
for R in (130, 145, 151, 160, 175):
    hit = tot = 0
    for a in range(0, 360, 3):
        px = int(289 + R*np.cos(np.radians(a))); py = int(385 + R*np.sin(np.radians(a)))
        tot += 1
        if black[py, px] > 0: hit += 1
    print(f'  R={R}: {hit}/{tot} = {hit/tot:.2f}')

# Angular profile of the black ring at best candidate
if best:
    s, cx, cy, R = best[0]
    print(f'\nbest black ring at ({cx},{cy}) R={R}: angular coverage:')
    ang_hist = np.zeros(12)
    for a in range(0, 360, 3):
        px = int(cx + R*np.cos(np.radians(a))); py = int(cy + R*np.sin(np.radians(a)))
        if black[py, px] > 0:
            ang_hist[a // 30] += 1
    for i, c in enumerate(ang_hist):
        print(f'  {i*30}-{i*30+30} deg: {c}/10')
