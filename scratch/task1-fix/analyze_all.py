import cv2
import numpy as np
import os

folder = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615'
files = [f for f in sorted(os.listdir(folder)) if f.endswith(('.png', '.jpg'))]

for f in files:
    p = os.path.join(folder, f)
    img = cv2.imread(p)
    if img is None:
        print(f, 'cannot read'); continue
    h, w = img.shape[:2]
    print(f'== {f}: {w}x{h}  aspect={w/h:.3f}')
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    black = (gray < 90).astype(np.uint8)
    ys, xs = np.where(black > 0)
    if len(xs):
        print(f'   black bbox: x[{xs.min()}..{xs.max()}] y[{ys.min()}..{ys.max()}]  size {(xs.max()-xs.min())}x{(ys.max()-ys.min())}')
    b, g, r = cv2.split(img.astype(np.int16))
    red = (r > 120) & (r > g + 60) & (r > b + 60)
    print(f'   red pixels: {red.sum()}')
    # find red route bbox
    if red.sum() > 0:
        ys2, xs2 = np.where(red)
        print(f'   red bbox: x[{xs2.min()}..{xs2.max()}] y[{ys2.min()}..{ys2.max()}]')
    # roundabout check: Hough on black
    circ = cv2.HoughCircles(black.astype(np.uint8), cv2.HOUGH_GRADIENT, dp=1.2, minDist=200, param1=100, param2=40, minRadius=80, maxRadius=260)
    if circ is not None:
        for c in circ[0][:4]:
            print(f'   hough circle: center=({c[0]:.0f},{c[1]:.0f}) R={c[2]:.0f}px D={2*c[2]/10:.1f}cm @10px/cm')
