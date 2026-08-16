import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def vwidth(x, y):
    """Width of dark band around (x,y) vertically and horizontally."""
    col = gray[max(0,y-30):y+30, x] < 100
    row = gray[y, max(0,x-30):x+30] < 100
    # longest runs
    def longest(mask):
        best = 0; cur = 0
        for v in mask:
            cur = cur + 1 if v else 0
            best = max(best, cur)
        return best
    return longest(col), longest(row)

for name, x, y in [('crossbar (560,475)', 560, 475), ('crossbar (700,475)', 700, 475),
                   ('crossbar (800,475)', 800, 475), ('crossbar (880,475)', 880, 475),
                   ('stem (755,560)', 755, 560), ('lineA (932,250)', 932, 250),
                   ('ring left (112,412)', 112, 412), ('top line (600,75)', 600, 75),
                   ('middle (700,395)', 700, 395), ('entrance (290,180)', 290, 180)]:
    vw, hw = vwidth(x, y)
    print(f'{name}: vert={vw}px horiz={hw}px  (track should be ~17-22px)')
