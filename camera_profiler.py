import cv2
import time
import csv
from datetime import datetime
import subprocess
import re

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

    for width, height in resolutions:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        time.sleep(0.2)
        w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        frame_count = 0
        start = time.time()
        while time.time() - start < test_time:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
        end = time.time()
        fps = frame_count / (end - start) if frame_count > 0 else 0

        print(f"✅ Mode {width}x{height} works as {int(w)}x{int(h)} ≈ {fps:.1f} fps")
        results.append((index, name, width, height, int(w), int(h), round(fps, 1)))

    cap.release()
    return results


if __name__ == "__main__":
    resolutions = [(320, 240), (640, 480), (800, 600), (1024, 768), (1280, 720)]
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outfile = f"camera_profile_{timestamp}.csv"

    devices = list_cameras_dshow()
    results_all = []

    for i in range(5):
        print(f"\n--- Testing camera index {i} ---")
        name = devices[i] if i < len(devices) else f"Camera_{i}"
        res = test_camera(i, name, resolutions)
        results_all.extend(res)

    if results_all:
        with open(outfile, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Index", "Name", "Requested_Width", "Requested_Height",
                             "Actual_Width", "Actual_Height", "FPS"])
            writer.writerows(results_all)
        print(f"\n✅ Results saved to: {outfile}")
    else:
        print("\n⚠️ No working cameras detected.")
