import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

def follow(start, heading, max_steps=2500, window=18):
    """Follow the black line continuously, steering toward the black centroid ahead."""
    x, y = start
    dx, dy = heading  # unit-ish
    path = [(x, y)]
    for _ in range(max_steps):
        # look ahead 6px
        px, py = x + dx*6, y + dy*6
        plen = np.hypot(dx, dy) or 1
        nx_, ny_ = -dy/plen, dx/plen
        pts = []
        for s in range(-window//2, window//2 + 1):
            sx, sy = int(px + nx_*s), int(py + ny_*s)
            if 0 <= sx < w and 0 <= sy < h and black[sy, sx] > 0:
                pts.append((sx, sy))
        if not pts:
            break
        x, y = int(np.mean([p[0] for p in pts])), int(np.mean([p[1] for p in pts]))
        # update heading from movement
        if len(path) > 1:
            px0, py0 = path[-1]
            dx, dy = x - px0, y - py0
            L = np.hypot(dx, dy)
            if L > 0.01: dx, dy = dx/L, dy/L
            else: dx, dy = 0, 1
        path.append((x, y))
    return path

path = follow((755, 478), (1, 0))  # from T going east
print('loop trace n =', len(path))
for i in range(0, len(path), 80):
    x, y = path[i]
    print(f'  step {i:4d}: ({x:4d},{y:4d})')
x, y = path[-1]
print(f'  END: ({x},{y})')
