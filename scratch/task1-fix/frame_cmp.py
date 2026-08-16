import cv2
import numpy as np
a = cv2.imread('/tmp/lf-cap2-raw.jpg')
b = cv2.imread('/tmp/lf-cap3-raw.jpg')
diff = cv2.absdiff(a, b)
print('max pixel diff:', diff.max())
print('mean pixel diff:', diff.mean())
print('fraction identical pixels: %.4f' % (100*(diff.sum(axis=2) == 0).mean()))
