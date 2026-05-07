import cv2
import time


def capture_from_camera(save_path="captured.png", crop=False, countdown=3):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError("Camera not working")

    print("Press SPACE to start timer | ESC to exit")

    countdown_started = False
    start_time = None

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        display_frame = frame.copy()

        key = cv2.waitKey(1)

        # 🔥 Start countdown on SPACE
        if key == 32 and not countdown_started:
            countdown_started = True
            start_time = time.time()
            print("⏳ Countdown started")

        # 🔥 Exit on ESC
        if key == 27:
            cap.release()
            cv2.destroyAllWindows()
            print("❌ Capture cancelled")
            return None

        # 🔥 Handle countdown
        if countdown_started:
            elapsed = time.time() - start_time # type: ignore
            remaining = int(countdown - elapsed) + 1

            if remaining > 0:
                cv2.putText(
                    display_frame,
                    str(remaining),
                    (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    3,
                    (0, 0, 255),
                    5,
                    cv2.LINE_AA
                )
            else:
                cv2.imwrite(save_path, frame)
                print("✅ Image captured!")
                break

        cv2.imshow("Camera", display_frame)

    cap.release()
    cv2.destroyAllWindows()

    # ================== OPTIONAL CROP ==================
    if crop:
        img = cv2.imread(save_path)
        h, w = img.shape[:2] # type: ignore
        cropped = img[h//4:3*h//4, w//4:3*w//4] # type: ignore

        cropped_path = save_path.replace(".png", "_cropped.png")
        cv2.imwrite(cropped_path, cropped)

        return cropped_path

    return save_path