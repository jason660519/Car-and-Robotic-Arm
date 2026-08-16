import cv2
import numpy as np

# The planned route drawn on the BEV photo (13.5 px/cm per planned-route-lengths.txt)
p = '/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/line-follow-2026-08-15/planned-route-inventory.jpg'
img = cv2.imread(p)
h, w = img.shape[:2]
print('planned-route-inventory:', w, 'x', h)

# Extract colored route (likely green or red)
b,g,r = cv2.split(img.astype(np.int16))
red = ((r > 120) & (r > g + 60) & (r > b + 60)).astype(np.uint8) * 255
green = ((g > 120) & (g > r + 60) & (g > b + 60)).astype(np.uint8) * 255
blue = ((b > 120) & (b > g + 60) & (b > r + 60)).astype(np.uint8) * 255
print('red px:', (red>0).sum(), ' green px:', (green>0).sum(), ' blue px:', (blue>0).sum())

for name, mask in [('red', red), ('green', green), ('blue', blue)]:
    ys, xs = np.where(mask > 0)
    if len(xs):
        print(f'{name}: bbox x[{xs.min()}..{xs.max()}] y[{ys.min()}..{ys.max()}] n={len(xs)}')
