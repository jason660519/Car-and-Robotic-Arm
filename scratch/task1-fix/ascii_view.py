import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
b,g,r = cv2.split(img.astype(np.int16))
red = (r > 120) & (r > g + 60) & (r > b + 60)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = gray < 100

# downsample to 100x70 cells (10px each)
CH, CW = 70, 100
def cell_counts():
    rc = np.zeros((CH, CW)); bc = np.zeros((CH, CW)); oc = np.zeros((CH, CW))
    for cy in range(CH):
        for cx in range(CW):
            y0, y1 = cy*10, min(h, (cy+1)*10)
            x0, x1 = cx*10, min(w, (cx+1)*10)
            rc[cy,cx] = red[y0:y1, x0:x1].sum()
            bc[cy,cx] = black[y0:y1, x0:x1].sum()
            oc[cy,cx] = 100 - bc[cy,cx]
    return rc, bc, oc
rc, bc, oc = cell_counts()

chars = []
for cy in range(CH):
    row = ''
    for cx in range(CW):
        r_ = rc[cy,cx]; b_ = bc[cy,cx]
        if r_ >= 30 and b_ >= 15:
            row += 'X'   # red route on black track
        elif r_ >= 30:
            row += 'R'   # red route off track
        elif b_ >= 60:
            row += '#'   # heavy black (border/text)
        elif b_ >= 20:
            row += '.'   # light black (text)
        elif b_ >= 5:
            row += ','   # trace
        else:
            row += ' '
    chars.append(row)

# print with row labels every 10 (cm marks) and column labels
print('   ' + ''.join(str((i//10)%10) if i%10==0 else ' ' for i in range(100)))
for cy, row in enumerate(chars):
    mark = f'{cy//10}{cy%10}' if cy % 10 == 0 else '  '
    print(mark + row)
