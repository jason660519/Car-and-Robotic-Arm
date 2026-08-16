import cv2
import numpy as np

p = '/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png'
img = cv2.imread(p)
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
black = (gray < 100).astype(np.uint8) * 255

def track_center_vertical(x, y_lo, y_hi):
    """For a vertical corridor at x, find black center x per row."""
    out = []
    for y in range(y_lo, y_hi, 10):
        seg = black[y, max(0,x-25):min(w,x+26)]
        xs = np.where(seg > 0)[0]
        if len(xs) > 3:
            # longest run
            runs = []
            s = xs[0]; p_ = xs[0]
            for v in xs[1:]:
                if v - p_ > 6:
                    runs.append((s,p_)); s = v
                p_ = v
            runs.append((s,p_))
            best = max(runs, key=lambda r: r[1]-r[0])
            cx = (best[0]+best[1])//2 + max(0,x-25)
            out.append((y, cx, best[1]-best[0]+1))
    return out

def track_center_horizontal(y, x_lo, x_hi):
    out = []
    for x in range(x_lo, x_hi, 10):
        seg = black[max(0,y-25):min(h,y+26), x]
        ys = np.where(seg > 0)[0]
        if len(ys) > 3:
            runs = []
            s = ys[0]; p_ = ys[0]
            for v in ys[1:]:
                if v - p_ > 6:
                    runs.append((s,p_)); s = v
                p_ = v
            runs.append((s,p_))
            best = max(runs, key=lambda r: r[1]-r[0])
            cy = (best[0]+best[1])//2 + max(0,y-25)
            out.append((x, cy, best[1]-best[0]+1))
    return out

print('=== STEM vertical track (x~740-790) ===')
for x in range(735, 795, 5):
    pts = track_center_vertical(x, 470, 660)
    if pts:
        ys = [p[0] for p in pts]; cs = [p[1] for p in pts]
        print(f'x={x}: rows={ys[0]}-{ys[-1]} centers={cs[0]}..{cs[-1]}')

print('\n=== TOP horizontal track (y~60-110) ===')
for y in range(55, 115, 5):
    pts = track_center_horizontal(y, 200, 980)
    if pts:
        xs = [p[0] for p in pts]; cs = [p[1] for p in pts]
        run = max(pts, key=lambda p: -999)
        # find longest contiguous x span
        xspan = [p[0] for p in pts if p[2] > 10]
        if len(xspan) > 10:
            print(f'y={y}: xspan={xspan[0]}-{xspan[-1]} center_y_med={np.median(cs):.0f}')

print('\n=== RIGHT vertical track (x~880-1000) ===')
for x in range(880, 1001, 5):
    pts = track_center_vertical(x, 100, 420)
    if pts and len(pts) > 5:
        ys = [p[0] for p in pts]; cs = [p[1] for p in pts]
        print(f'x={x}: rows={ys[0]}-{ys[-1]} center_x_med={np.median(cs):.0f}')

print('\n=== MIDDLE horizontal track (y~380-420) ===')
for y in range(370, 430, 5):
    pts = track_center_horizontal(y, 200, 980)
    if pts:
        good = [p for p in pts if p[2] > 10]
        if len(good) > 10:
            xs = [p[0] for p in good]
            print(f'y={y}: xspan={xs[0]}-{xs[-1]} (n={len(good)})')

print('\n=== RETURN horizontal track (y~430-490) ===')
for y in range(430, 500, 5):
    pts = track_center_horizontal(y, 300, 980)
    if pts:
        good = [p for p in pts if p[2] > 10]
        if len(good) > 10:
            xs = [p[0] for p in good]
            print(f'y={y}: xspan={xs[0]}-{xs[-1]} (n={len(good)})')

print('\n=== BOTTOM horizontal (y~620-700) ===')
for y in range(620, 701, 10):
    pts = track_center_horizontal(y, 300, 980)
    if pts:
        good = [p for p in pts if p[2] > 10]
        if len(good) > 10:
            xs = [p[0] for p in good]
            print(f'y={y}: xspan={xs[0]}-{xs[-1]} (n={len(good)})')
