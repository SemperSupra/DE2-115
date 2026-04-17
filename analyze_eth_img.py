import cv2
import numpy as np

def main():
    img = cv2.imread('q1_zoom.jpg')
    if img is None:
        print("Error: Could not read q1_zoom.jpg")
        return
    
    # Standard Green LED
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([40, 50, 100]), np.array([80, 255, 255]))
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"Found {len(contours)} potential green blobs.")
    
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area > 50:
            x, y, w, h = cv2.boundingRect(cnt)
            print(f"Blob {i}: x={x}, y={y}, w={w}, h={h}, area={area}")
            # Crop and save for "viewing" (mental model)
            crop = img[max(0,y-20):y+h+20, max(0,x-20):x+w+20]
            cv2.imwrite(f'eth_blob_{i}.jpg', crop)

if __name__ == "__main__":
    main()
