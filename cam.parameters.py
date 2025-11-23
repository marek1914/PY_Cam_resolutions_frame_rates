"""
to check the true technical parameters (like resolution, frame rate, and sometimes even approximate field of view) yourself once the USB camera is connected.
You can do this with simple tools or short Python scripts.
Check recognized resolutions and frame rates
this tells you
The working resolutions → the ones the camera actually supports.
The actual FPS → you’ll see if it’s truly 30 fps or just 10–15 fps.
You can visually inspect a frame to see lens distortion (helps estimate field of view).

by default, OpenCV (and most video tools) opens the first available camera (index 0), which is usually your laptop’s built-in webcam.
To be sure you’re testing the external USB camera, you have to explicitly select the correct camera index or device path.

Camera index 0 detected
Camera index 1 detected

Then:
    0 → usually your internal webcam
    1 (or higher) → likely your external USB camera

install OpenCV
opencv-python

"""

import cv2, time

for i in range(5):
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    if cap.isOpened():
        print(f"Camera index {i} detected")
        cap.release()

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # CAP_DSHOW avoids MSMF issues


if not cap.isOpened():
    print("Camera not detected.")
    exit()

name = cap.getBackendName()
print("Backend:", name)

print("Default resolution:", cap.get(cv2.CAP_PROP_FRAME_WIDTH), "x", cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

test_modes = [(320, 240), (640, 480), (800, 600), (1024, 768), (1280, 720)]
for w, h in test_modes:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    time.sleep(0.5)  # let it settle
    ret, frame = cap.read()
    if not ret or frame is None:
        print(f"❌ Mode {w}x{h} not supported")
        continue
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"✅ Mode {w}x{h} works as {actual_w}x{actual_h}")

    # quick FPS test
    frames, start = 0, time.time()
    while frames < 60:
        ret, frame = cap.read()
        if not ret:
            break
        frames += 1
    fps = frames / (time.time() - start)
    print(f"   ≈ {fps:.1f} fps")

cap.release()
cv2.destroyAllWindows()

import cv2

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
while True:
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow("Camera Test", frame)
    if cv2.waitKey(1) == 27:  # ESC to exit
        break

cap.release()
cv2.destroyAllWindows()