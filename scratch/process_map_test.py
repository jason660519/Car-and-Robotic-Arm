import cv2
import numpy as np
import os

def detect_and_warp(img_path, output_path, debug_path):
    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to load {img_path}")
        return
    
    h, w = img.shape[:2]
    print(f"Processing {img_path}: shape={w}x{h}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Threshold or Canny edge detection
    # The paper is white, carpet is dark. Thresholding white area:
    _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY)
    
    # Morphological close to close gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("No contours found!")
        return

    # Find the largest contour by area
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    map_contour = contours[0]
    
    # Approximate contour to polygon
    peri = cv2.arcLength(map_contour, True)
    approx = cv2.approxPolyDP(map_contour, 0.02 * peri, True)
    
    print(f"Approx vertices count: {len(approx)}")
    
    # Draw contour on debug image
    debug_img = img.copy()
    cv2.drawContours(debug_img, [map_contour], -1, (0, 255, 0), 5)
    
    if len(approx) == 4:
        pts = approx.reshape(4, 2)
    else:
        # Fallback to rotated bounding rectangle or minimum area rectangle if polygon doesn't have 4 points
        rect = cv2.minAreaRect(map_contour)
        pts = cv2.boxPoints(rect)
        pts = np.int32(pts)
        
    for p in pts:
        cv2.circle(debug_img, (int(p[0]), int(p[1])), 15, (0, 0, 255), -1)
        
    cv2.imwrite(debug_path, debug_img)
    print(f"Saved debug to {debug_path}")

    # Order points: top-left, top-right, bottom-right, bottom-left
    rect_pts = order_points(pts)
    (tl, tr, br, bl) = rect_pts

    # Compute width and height of new image
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    M = cv2.getPerspectiveTransform(rect_pts.astype("float32"), dst)
    warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))

    cv2.imwrite(output_path, warped)
    print(f"Saved warped map to {output_path}")

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)] # top-left has smallest sum
    rect[2] = pts[np.argmax(s)] # bottom-right has largest sum
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)] # top-right has smallest difference
    rect[3] = pts[np.argmax(diff)] # bottom-left has largest difference
    
    return rect

if __name__ == '__main__':
    detect_and_warp('IMG_0583.JPG', 'IMG_0583_warped.jpg', 'IMG_0583_debug.jpg')
    detect_and_warp('IMG_0592.JPG', 'IMG_0592_warped.jpg', 'IMG_0592_debug.jpg')
