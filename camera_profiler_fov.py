import cv2
import time
import csv
from datetime import datetime
import subprocess
import re
import math
import os

# === CONFIGURATION ===
TEST_RESOLUTIONS = [(320, 240), (640, 480), (800, 600), (1024, 768), (1280, 720)]
TEST_DURATION = 3          # seconds for FPS measurement
SAVE_SNAPSHOTS = True      # set False to skip saving frames
CALIBRATION_FOV = True     # ask user for object width and distance to estimate FOV

def list_cameras_dshow():
    """List cameras by name (Windows DirectShow) using ffmpeg."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
            stderr=subprocess.PIPE,
            text=True
        ).stderr
        devices = re.findall(r'"(.*?)"', result)
        print("🎥 Detected cameras:", devices)
        return devices
    except Exception as e:
        print("⚠️ Could not list devices via ffmpeg:", e)
        return []

def estimate_fov(frame, known_width_cm, distance_cm, pixel_width):
    """
    Estimate horizontal field of view (in degrees) using pinhole model:
    FOV = 2 * atan((object_width / (2 * distance))).
    """
    if distance_cm <= 0 or known_width_cm <= 0 or pixel_width <= 0:
        return None
    # assume measured width in pixels corresponds to known_width_cm
    fov_rad = 2 * math.atan((known_width_cm / 2) / distance_cm)
    return math.degrees(fov_rad)

def test_camera(index, name, resolutions, test_time=3):
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print(f"❌ Cannot open camera index {index}")
        return []

    backend = cap.getBackendName()
    print(f"\nBackend: {backend}")
    results = []

    default_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    default_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"Default resolution: {default_width} x {default_height}")

    save_dir = f"cam_{index}_{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(save_dir, exist_ok=True)

    for width, height in resolutions:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        time.sleep(0.3)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        frame_count = 0
        start = time.time()
        while time.time() - start < test_time:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            if frame_count == 1 and SAVE_SNAPSHOTS:
                cv2.imwrite(os.path.join(save_dir, f"snapshot_{w}x{h}.jpg"), frame)
        end = time.time()
        fps = frame_count / (end - start) if frame_count > 0 else 0

        print(f"✅ Mode {width}x{height} works as {w}x{h} ≈ {fps:.1f} fps")
        results.append((index, name, width, height, w, h, round(fps, 1)))

    cap.release()
    return results


if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outfile = f"camera_profile_{timestamp}.csv"

    devices = list_cameras_dshow()
    results_all = []

    for i in range(5):
        print(f"\n--- Testing camera index {i} ---")
        name = devices[i] if i < len(devices) else f"Camera_{i}"
        res = test_camera(i, name, TEST_RESOLUTIONS, TEST_DURATION)
        results_all.extend(res)

    if results_all:
        with open(outfile, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Index", "Name", "Requested_Width", "Requested_Height",
                             "Actual_Width", "Actual_Height", "FPS"])
            writer.writerows(results_all)
        print(f"\n✅ Results saved to: {outfile}")

    # --- Optional FOV estimation ---
    if CALIBRATION_FOV:
        print("\n📏 FOV estimation (optional)")
        try:
            known_width = float(input("Enter known object width (cm): "))
            distance = float(input("Enter distance to camera (cm): "))
            pixel_width = float(input("Enter object width on image (pixels): "))
            fov = estimate_fov(None, known_width, distance, pixel_width)
            if fov:
                print(f"\nEstimated Horizontal FOV ≈ {fov:.1f}°")
            else:
                print("⚠️ Invalid calibration parameters.")
        except Exception as e:
            print("⚠️ Skipping FOV estimation:", e)
