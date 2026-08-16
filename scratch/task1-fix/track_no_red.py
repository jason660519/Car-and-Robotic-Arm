import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60))
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black_nr = ((gray < 100) & ~red).astype(np.uint8) * 255  # black EXCLUDING red

# find the crossbar east of T: scan y 440..520, x 700..1000 for black bands
print('Black (no red) runs at various y, x 700-1000:')
for y in range(440, 521, 5):
    row = black_nr[y, 700:1000]
    xs = np.where(row > 0)[0] + 700
    if len(xs) == 0: continue
    runs = []
    s = xs[0]; p_ = xs[0]
    for x in xs[1:]:
        if x - p_ > 8:
            runs.append((s, p_)); s = x
        p_ = x
    runs.append((s, p_))
    rs = '  '.join(f'{a}-{b}' for a, b in runs if b-a >= 10)
    if rs: print(f'y={y}: {rs}')

# vertical profile at specific x to find the track y-center
print('\nVertical black(no-red) bands at x=800, 850, 880, 915:')
for x in (800, 850, 880, 915):
    col = black_nr[:, x]
    ys = np.where(col > 0)[0]
    if len(ys) == 0:
        print(f'  x={x}: none'); continue
    runs = []
    s = ys[0]; p_ = ys[0]
    for y in ys[1:]:
        if y - p_ > 8:
            runs.append((s, p_)); s = y
        p_ = y
    runs.append((s, p_))
    rr = [f'{a}-{b}' for a, b in runs if b-a >= 8]
    print(f'  x={x}: {rr}')
