import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255
dt = cv2.distanceTransform(black, cv2.DIST_L2, 5)
track = ((dt >= 6) & (dt <= 17)).astype(np.uint8) * 255
track = cv2.bitwise_and(black, cv2.dilate(track, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11,11))))

n, lab, stats, cents = cv2.connectedComponentsWithStats(track)

def trace_comp(comp_id, name):
    mask = (lab == comp_id).astype(np.uint8) * 255
    ys, xs = np.where(mask > 0)
    print(f'--- comp {comp_id} ({name}): {len(xs)} px, bbox x[{xs.min()}..{xs.max()}] y[{ys.min()}..{ys.max()}]')
    # print the component at 10px cells
    for y in range(ys.min()//10*10, min(ys.max()+10, h), 10):
        row = ''
        for x in range(0, w, 10):
            if mask[y:y+10, x:x+10].sum() > 0: row += '#'
            else: row += ' '
        if row.strip():
            print(f'  y={y:3d}: {row}')

trace_comp(7, 'middle horiz + right vert')
trace_comp(18, 'stem top')
trace_comp(20, 'bottom blob (stem)')
