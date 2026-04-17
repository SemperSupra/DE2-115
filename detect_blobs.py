import cv2
import numpy as np

def main():
    img = cv2.imread('board_photo_hd.jpg')
    if img is None:
        print("Error: Could not read board_photo_hd.jpg")
        return
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Red detection (wraps around 0 and 180)
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    mask_red = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)
    
    # Green detection
    lower_green = np.array([40, 100, 100]) # Increased saturation/value threshold
    upper_green = np.array([80, 255, 255])
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    
    for color, mask in [("red", mask_red), ("green", mask_green)]:
        pixels = cv2.countNonZero(mask)
        print(f"{color.capitalize()} pixels: {pixels}")
        if pixels > 5:
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for i, cnt in enumerate(contours):
                if cv2.contourArea(cnt) > 10:
                    x, y, w, h = cv2.boundingRect(cnt)
                    print(f"  {color} blob {i}: x={x}, y={y}, w={w}, h={h}")
                    crop = img[max(0,y-20):min(img.shape[0],y+h+20), max(0,x-20):min(img.shape[1],x+w+20)]
                    cv2.imwrite(f'{color}_blob_{i}.jpg', crop)

if __name__ == "__main__":
    main()
