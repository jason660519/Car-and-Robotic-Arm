import numpy as np
import cv2

# load planned path
path = np.load('/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/line-follow-2026-08-15/planned-path.npy')
print('planned-path shape:', path.shape, 'dtype:', path.dtype)
print('first/last:', path[0], path[-1])

PX_PER_CM = 13.5

# Rebuild the same waypoints as draw_planned_route.py (they were snapped):
stem = [(868, 700), (868, 660), (867, 591)]
outer = [
    (867, 583), (950, 578), (1000, 573), (1100, 560), (1151, 545),
    (1151, 500), (1153, 400), (1148, 300), (1137, 200), (1137, 155),
    (1100, 155), (1000, 138), (800, 132), (600, 129), (400, 121),
    (320, 140), (307, 200), (307, 280),
]
ring_degs = list(range(270, -1, -8))
ret = [(550, 581), (700, 585), (867, 583), (868, 660), (868, 720)]

def seg(pts):
    pts = np.array(pts, dtype=float)
    d = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    return d.sum() / PX_PER_CM

print('\n--- waypoint segment lengths (cm @ 13.5px/cm) ---')
print('stem (T top->start): %.1f' % seg(stem))
# east straight: T -> SE corner start (before the corner curve)
print('east T->(1151,545) (whole east incl corner): %.1f' % seg([(867,583),(950,578),(1000,573),(1100,560),(1151,545)]))
print('east T->(1100,560) (straight before corner): %.1f' % seg([(867,583),(950,578),(1000,573),(1100,560)]))
print('east T->(1000,573): %.1f' % seg([(867,583),(950,578),(1000,573)]))
# right vertical
print('right vertical (SE->NE): %.1f' % seg([(1151,545),(1151,500),(1153,400),(1148,300),(1137,200),(1137,155)]))
# top
print('top (NE->NW): %.1f' % seg([(1137,155),(1100,155),(1000,138),(800,132),(600,129),(400,121)]))
# NW entry
print('NW+entry (top end -> ring): %.1f' % seg([(400,121),(320,140),(307,200),(307,280)]))
# ring
ring_pts = []
CC = np.array([307.0, 581.0]); CR = 258.0
for d in ring_degs:
    a = np.deg2rad(d)
    ring_pts.append(CC + np.array([np.cos(a), np.sin(a)]) * CR)
print('ring arc 270->0 deg: %.1f (%.1f cm if full circle D=%.1f)' % (seg(ring_pts), np.pi*2*CR/PX_PER_CM, 2*CR/PX_PER_CM))
# return
print('return (ring right -> T): %.1f' % seg([(550,581),(700,585),(867,583)]))
print('return incl stem down: %.1f' % seg([(550,581),(700,585),(867,583),(868,660)]))

print('\n--- totals ---')
tot = seg(stem) + seg(outer) + seg(ring_pts) + seg(ret)
print('stem+outer+ring+ret = %.1f' % tot)
