import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

def trace_from(start, direction, name, max_steps=300, window=22):
    """Walk along black pixels from start in direction; steer toward black centroid."""
    x, y = start
    dx, dy = direction
    path = [(x, y)]
    for _ in range(max_steps):
        # sample a perpendicular window ahead
        px, py = x + dx*4, y + dy*4
        # perpendicular unit
        plen = np.hypot(dy, dx) or 1
        nx_, ny_ = -dy/plen, dx/plen
        pts = []
        for s in range(-window//2, window//2):
            sx, sy = int(px + nx_*s), int(py + ny_*s)
            if 0 <= sx < w and 0 <= sy < h and black[sy, sx] > 0:
                pts.append((sx, sy))
        if not pts:
            break
        cx = int(np.mean([p[0] for p in pts])); cy = int(np.mean([p[1] for p in pts]))
        x, y = cx, cy
        path.append((x, y))
    return path

def print_path(path, label):
    print(f'{label}: {len(path)} points')
    # summarize: first, every 20th, last
    for i in range(0, len(path), 20):
        x, y = path[i]
        print(f'   step {i}: ({x},{y})')
    x, y = path[-1]
    print(f'   end: ({x},{y})')

# 1) From stem top (760,475), trace EAST
p1 = trace_from((760, 475), (1, 0), 'stem-top-east')
print_path(p1, 'From stem top (760,475) heading EAST')

# 2) From stem top, trace WEST
p2 = trace_from((760, 475), (-1, 0), 'stem-top-west')
print_path(p2, 'From stem top (760,475) heading WEST')

# 3) From ring right edge (467,400), trace EAST
p3 = trace_from((467, 400), (1, 0), 'ring-right-east')
print_path(p3, 'From ring right (467,400) heading EAST')

# 4) From ring right edge (467,400), trace DOWN
p4 = trace_from((467, 400), (0, 1), 'ring-right-down')
print_path(p4, 'From ring right (467,400) heading DOWN')

# 5) From ring bottom (292,600), trace EAST
p5 = trace_from((292, 600), (1, 0), 'ring-bottom-east')
print_path(p5, 'From ring bottom (292,600) heading EAST')

# 6) From T crossbar west end (697,480), trace WEST
p6 = trace_from((697, 480), (-1, 0), 'crossbar-west')
print_path(p6, 'From (697,480) heading WEST')
