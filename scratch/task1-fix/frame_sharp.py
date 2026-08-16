import cv2
import numpy as np

img = cv2.imread('/tmp/lf-cap-raw.jpg')
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# sharpness: Laplacian variance per region
print('Laplacian variance per block (sharpness; low = blurry):')
lap = cv2.Laplacian(gray, cv2.CV_64F)
for by in range(6):
    row = ''
    for bx in range(8):
        y0, y1 = by*h//6, (by+1)*h//6
        x0, x1 = bx*w//8, (bx+1)*w//8
        v = lap[y0:y1, x0:x1].var()
        row += f'{v:7.0f}'
    print('  ' + row)

# structure inside the big dark region (x 1080-1700, y 472-950)
roi = gray[472:950, 1080:1700]
print('\ndark region stats: mean=%.0f std=%.0f (std low = uniform/blur)' % (roi.mean(), roi.std()))
roi2 = gray[472:950, 400:940]
print('left dark region: mean=%.0f std=%.0f' % (roi2.mean(), roi2.std()))

# gradient magnitudes in dark region
gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
mag = np.hypot(gx, gy)
print('edge magnitude in dark region (x1080-1700,y472-950): %.1f (mean), p99=%.1f' % (mag[472:950, 1080:1700].mean(), np.percentile(mag[472:950, 1080:1700], 99)))
print('edge magnitude in paper band (x400-1700,y334-455): %.1f (mean), p99=%.1f' % (mag[334:455, 400:1700].mean(), np.percentile(mag[334:455, 400:1700], 99)))
