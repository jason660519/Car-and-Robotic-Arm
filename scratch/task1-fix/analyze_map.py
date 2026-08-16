import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
print('image:', w, 'x', h)

# 1) Red route mask (pure red-ish pixels)
b,g,r = cv2.split(img.astype(np.int16))
red_mask = (r > 120) & (r > g + 60) & (r > b + 60)
red_mask = (red_mask * 255).astype(np.uint8)
print('red pixel count:', (red_mask > 0).sum())

# 2) Black track mask: dark pixels
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black_mask = (gray < 90).astype(np.uint8) * 255
print('black pixel count:', (black_mask > 0).sum())

# Save masks for visual inspection
cv2.imwrite('/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/task1-fix/red_mask.png', red_mask)
cv2.imwrite('/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/task1-fix/black_mask.png', black_mask)

# 3) Find red path components -> check continuity of the red polyline
contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print('red contours:', len(contours))
for i, c in enumerate(sorted(contours, key=cv2.contourArea, reverse=True)[:20]):
    x,y,ww,hh = cv2.boundingRect(c)
    print(f'  contour {i}: area={cv2.contourArea(c):.0f} bbox=({x},{y},{ww},{hh})')

# 4) Sample red path pixels along expected route geometry from the script
#    Expected route points from warp_new_photo.py:
route = [
    ('P1 stem', (760, 660), (760, 476)),
    ('P2 east', (760, 476), (860, 476)),
    ('ARC1', (860, 476), (990, 346)),
    ('P4 north', (990, 346), (990, 216)),
    ('ARC2', (990, 216), (860, 86)),
    ('P6 west', (860, 86), (360, 86)),
    ('ARC3', (360, 86), (230, 216)),
    ('P8 south', (230, 216), (230, 291)),
    ('P9 roundabout', (230, 291), (405, 466)),
    ('P10 east', (405, 466), (760, 476)),
    ('P11 return', (760, 476), (760, 660)),
]

def near_red(pt, rad=12):
    x, y = pt
    x0, x1 = max(0, x-rad), min(w-1, x+rad)
    y0, y1 = max(0, y-rad), min(h-1, y+rad)
    return bool((red_mask[y0:y1+1, x0:x1+1] > 0).any())

print('\nRoute endpoint continuity check (is red near the junction?):')
for name, a, b in route:
    print(f'  {name}: start={a} red_near={near_red(a)}  end={b} red_near={near_red(b)}')

# 5) Distance between consecutive segments' endpoints
pts = [a for name,a,b in route] + [route[-1][2]]
print('\nGap between consecutive segments (start of next vs end of prev):')
prev = None
for name, a, b in route:
    if prev is not None:
        d = np.hypot(a[0]-prev[0], a[1]-prev[1])
        print(f'  {name} start vs prev end: gap={d:.1f}px (={d/10:.1f}cm)')
    prev = b
