import cv2
import numpy as np

p = '/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/assets/reference/task1/2026-08-16-task1-100x70-route-map-corrected.png'
img = cv2.imread(p)
for name, x, y in [('(315,215) ring-top-text?', 315, 215), ('(290,180) entrance', 290, 180),
                   ('(292,300) ring top arc', 292, 300), ('(112,412) ring left', 112, 412),
                   ('(292,592) ring bottom', 292, 592), ('(455,465) ring exit', 455, 465),
                   ('(760,560) stem', 760, 560), ('(895,390) ARC1 end', 895, 390),
                   ('(933,250) Line A', 933, 250), ('(905,75) top east', 905, 75)]:
    b, g, r = img[y, x].astype(int)
    print(f'{name}: bgr=({b},{g},{r})')
