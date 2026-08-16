import cv2
import numpy as np

old = cv2.imread('/Users/jasonmacbbookpro/.gemini/antigravity-ide/brain/766f6800-0916-4543-be32-d4997b148615/task1_birds_eye_view_warped_map.png')
new = cv2.imread('/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/assets/reference/task1/2026-08-16-task1-100x70-route-map-corrected.png')
H, W = old.shape[:2]
canvas = np.zeros((H, W * 2 + 20, 3), np.uint8)
canvas[:, :W] = old
canvas[:, W + 20:] = new
cv2.line(canvas, (W + 10, 0), (W + 10, H), (0, 255, 255), 6)
cv2.putText(canvas, 'BEFORE (Gemini)', (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)
cv2.putText(canvas, 'AFTER (corrected)', (W + 50, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)
cv2.imwrite('/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm/scratch/task1-fix/comparison-before-after.png', canvas)
print('saved comparison')
