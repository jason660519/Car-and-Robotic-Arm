import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

def trace_from(start, direction, max_steps=400, window=20):
    x, y = start
    dx, dy = direction
    path = [(x, y)]
    for _ in range(max_steps):
        px, py = x + dx*4, y + dy*4
        plen = np.hypot(dy, dx) or 1
        nx_, ny_ = -dy/plen, dx/plen
        pts = []
        for s in range(-window//2, window//2):
            sx, sy = int(px + nx_*s), int(py + ny_*s)
            if 0 <= sx < w and 0 <= sy < h and black[sy, sx] > 0:
                pts.append((sx, sy))
        if not pts:
            break
        x, y = int(np.mean([p[0] for p in pts])), int(np.mean([p[1] for p in pts]))
        path.append((x, y))
    return path

def show(path, label, step=25):
    print(f'{label}: n={len(path)}')
    for i in range(0, len(path), step):
        print(f'   {i:3d}: ({path[i][0]},{path[i][1]})')
    print(f'   END: ({path[-1][0]},{path[-1][1]})')

# SE corner: from (915,475) going NORTH
show(trace_from((915, 475), (0, -1)), 'SE corner: (915,475) going NORTH')

# right vertical: from (933,390) going NORTH
show(trace_from((933, 390), (0, -1)), 'right vert: (933,390) going NORTH')

# NE corner: from (933,150) going NORTH
show(trace_from((933, 150), (0, -1)), 'NE corner: (933,150) going NORTH')

# Ring counterclockwise from top entry: trace along circle from (292,232) going LEFT (west)
# follow black pixels with a leftward bias
show(trace_from((292, 232), (-1, 0)), 'ring: (292,232) going WEST (CCW?)')

# ring from top going RIGHT (clockwise)
show(trace_from((292, 232), (1, 0)), 'ring: (292,232) going EAST (CW?)')

# crossbar from T going west: where does it end?
show(trace_from((700, 476), (-1, 0)), 'crossbar: (700,476) going WEST', step=15)
