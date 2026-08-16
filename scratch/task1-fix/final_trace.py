import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60))
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black_nr = ((gray < 100) & ~red).astype(np.uint8) * 255

def follow(start, heading, max_steps=1500, window=20):
    x, y = start
    dx, dy = heading
    path = [(x, y)]
    for _ in range(max_steps):
        px, py = x + dx*5, y + dy*5
        plen = np.hypot(dy, dx) or 1
        nx_, ny_ = -dy/plen, dx/plen
        pts = []
        for s in range(-window//2, window//2 + 1):
            sx, sy = int(px + nx_*s), int(py + ny_*s)
            if 0 <= sx < w and 0 <= sy < h and black_nr[sy, sx] > 0:
                pts.append((sx, sy))
        if not pts:
            break
        x, y = int(np.mean([p[0] for p in pts])), int(np.mean([p[1] for p in pts]))
        if len(path) > 1:
            px0, py0 = path[-1]
            dx, dy = x - px0, y - py0
            L = np.hypot(dx, dy)
            if L > 0.01: dx, dy = dx/L, dy/L
            else: dx, dy = 0, 1
        path.append((x, y))
    return path

def show(path, label, step=40):
    print(f'{label}: n={len(path)}')
    for i in range(0, len(path), step):
        print(f'   {i:4d}: ({path[i][0]:4d},{path[i][1]:4d})')
    x, y = path[-1]
    print(f'   END: ({x},{y})')

# T at stem top ~(800, 470). Trace EAST along the y~470-490 band.
show(follow((800, 470), (1, 0)), 'T(800,470) EAST')
# T trace WEST
show(follow((800, 470), (-1, 0)), 'T(800,470) WEST')
# ring right edge going down from (467, 400)
show(follow((467, 400), (0, 1)), 'ring right (467,400) DOWN')
# middle horizontal from (700,395) going WEST
show(follow((700, 395), (-1, 0)), 'middle horiz (700,395) WEST')
# double lane from (600,455) going EAST
show(follow((600, 455), (1, 0)), 'double lane (600,455) EAST')
# double lane from (600,455) going WEST
show(follow((600, 455), (-1, 0)), 'double lane (600,455) WEST')
