import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def line_profile(x, y_lo, y_hi):
    """Find dark pixels and their mean color at column x."""
    col = img[:, x, :]
    g = gray[:, x]
    dark = np.where(g < 130)[0]
    dark = dark[(dark >= y_lo) & (dark <= y_hi)]
    if len(dark) == 0: return 'none'
    mean_bgr = col[dark].mean(axis=0)
    return f'{len(dark)}px gray={g[dark].mean():.0f} bgr=({mean_bgr[0]:.0f},{mean_bgr[1]:.0f},{mean_bgr[2]:.0f})'

for name, x, y1, y2 in [('Line A (933)', 933, 150, 380), ('Line B (985)', 985, 150, 460),
                        ('border (996)', 996, 150, 460), ('track top (600,75)', 600, 70, 90),
                        ('ring left (112,412)', 112, 400, 430), ('stem (755,560)', 755, 550, 580),
                        ('crossbar (700,475)', 700, 470, 485), ('middle horiz (700,395)', 700, 388, 410)]:
    print(f'{name}: {line_profile(x, y1, y2)}')

# Horizontal: check where track vs text: gray profile across x at y=200
print('\ngray at y=200, x 880-1000:')
row = gray[200, 880:1000]
for x in range(880, 1000, 4):
    seg = row[x-880:x-880+4].mean()
    print(f'  x={x}: {seg:.0f}')
