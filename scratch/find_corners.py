import cv2
import numpy as np

def inspect_corners(img_path, corners_approx, output_path):
    img = cv2.imread(img_path)
    h_img, w_img = img.shape[:2]
    patches = []
    
    for i, (x, y) in enumerate(corners_approx):
        x1, x2 = max(0, x-150), min(w_img, x+150)
        y1, y2 = max(0, y-150), min(h_img, y+150)
        crop = img[y1:y2, x1:x2].copy()
        
        # Pad to 300x300 if needed
        patch = np.zeros((300, 300, 3), dtype=np.uint8)
        cx, cy = x - x1, y - y1
        patch[0:crop.shape[0], 0:crop.shape[1]] = crop
        
        # draw marker at actual (cx, cy)
        cv2.drawMarker(patch, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
        cv2.putText(patch, f"P{i}: ({x},{y})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        patches.append(patch)
        
    top_row = np.hstack((patches[0], patches[1]))
    bot_row = np.hstack((patches[2], patches[3]))
    grid = np.vstack((top_row, bot_row))
    cv2.imwrite(output_path, grid)
    print(f"Saved corner inspection grid to {output_path}")

# Approx corners for IMG_0583
# Order: Top-Left, Top-Right, Bottom-Right, Bottom-Left
corners_0583 = [
    (130, 480),   # Top-Left approx
    (2890, 160),  # Top-Right approx
    (2900, 3850), # Bottom-Right approx
    (150, 3950)   # Bottom-Left approx
]

# Approx corners for IMG_0592
corners_0592 = [
    (260, 370),   # Top-Left approx
    (2690, 450),  # Top-Right approx
    (2740, 3550), # Bottom-Right approx
    (180, 3530)   # Bottom-Left approx
]

if __name__ == '__main__':
    base_dir = '/Volumes/KLEVV-4T-1/Danny/Car-and-Robotic-Arm'
    inspect_corners(f'{base_dir}/IMG_0583.JPG', corners_0583, f'{base_dir}/scratch/IMG_0583_corners_check.jpg')
    inspect_corners(f'{base_dir}/IMG_0592.JPG', corners_0592, f'{base_dir}/scratch/IMG_0592_corners_check.jpg')
