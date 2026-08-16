import cv2
import numpy as np
img = cv2.imread('/tmp/lf-cap2-raw.jpg')
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
lap = cv2.Laplacian(gray, cv2.CV_64F)
overall = lap.var()
print('frame %dx%d  Laplacian variance overall: %.0f' % (w, h, overall))
print('(before focusing: ~2-30; in-focus paper scene usually >100-300)')
# paper band region
band = lap[300:900, 400:1700]
print('paper band Laplacian var: %.0f' % band.var())
