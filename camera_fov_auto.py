import cv2
import numpy as np
import math

def estimate_fov_auto(cam_index=0, known_width_cm=21.0, distance_cm=17.0, color="red"):
    # Choose color range for detection
    if color.lower() == "red":
        # HSV range for red
        lower1 = np.array([0, 120, 70])
        upper1 = np.array([10, 255, 255])
        lower2 = np.array([170, 120, 70])
        upper2 = np.array([180, 255, 255])
    elif color.lower() == "blue":
        lower1 = np.array([100, 150, 0])
        upper1 = np.array([140, 255, 255])
        lower2 = None
        upper2 = None
    elif color.lower() == "green":
        lower1 = np.array([35, 100, 50])
        upper1 = np.array([85, 255, 255])
        lower2 = None
        upper2 = None
    else:
        raise ValueError("Color must be red, blue, or green")

    cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("❌ Cannot open camera")
        return

    print("🎥 Press 'SPACE' to capture calibration frame when your colored object is visible.")
    print("Press 'ESC' to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        cv2.imshow("Live Feed", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            cap.release()
            cv2.destroyAllWindows()
            return
        elif key == 32:  # SPACE
            break

    cap.release()
    cv2.destroyAllWindows()

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask = mask1
    if lower2 is not None:
        mask2 = cv2.inRange(hsv, lower2, upper2)
        mask = mask1 | mask2

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print("⚠️ No object detected. Try different color or lighting.")
        return

    # Use largest contour
    c = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(c)
    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    fov = 2 * math.degrees(math.atan((known_width_cm / 2) / distance_cm))
    print(f"\nDetected object pixel width: {w}px")
    print(f"Known width: {known_width_cm} cm, distance: {distance_cm} cm")
    print(f"Estimated horizontal FOV ≈ {fov:.1f}°")

    cv2.putText(frame, f"FOV ≈ {fov:.1f} deg", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imshow("Detected Object", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    print("=== Automatic Camera FOV Estimation ===")
    w = float(input("Enter known object width (cm): "))
    d = float(input("Enter distance to camera (cm): "))
    c = input("Enter object color (red/blue/green): ").strip().lower()
    estimate_fov_auto(0, w, d, c)
