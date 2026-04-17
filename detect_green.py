import cv2
import numpy as np

def main():
    img = cv2.imread('board_photo_hd.jpg')
    if img is None:
        print("Error: Could not read board_photo_hd.jpg")
        return
    
    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Define range for green color (LEDs)
    lower_green = np.array([40, 50, 50])
    upper_green = np.array([80, 255, 255])
    
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    green_pixels = cv2.countNonZero(mask)
    print(f"Green pixels found: {green_pixels}")
    
    # If many green pixels, save a crop of that area
    if green_pixels > 10:
        # Find bounding box of green pixels
        coords = cv2.findNonZero(mask)
        x, y, w, h = cv2.boundingRect(coords)
        print(f"Green area: x={x}, y={y}, w={w}, h={h}")
        # Add some padding
        pad = 50
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(img.shape[1], x + w + pad)
        y2 = min(img.shape[0], y + h + pad)
        crop = img[y1:y2, x1:x2]
        cv2.imwrite('green_leds_crop.jpg', crop)
        print("Saved green_leds_crop.jpg")

if __name__ == "__main__":
    main()
