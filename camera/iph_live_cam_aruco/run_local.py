#Run live detection on your Mac: iPhone (Continuity Camera), built-in webcam, or a video file.

#Usage:
#    python run_local.py --list                 # show which camera index is which
#    python run_local.py 0                      # ArUco markers, camera index 0 for iphone and 1 for laptop
#    python run_local.py 0 --mode face          # faces instead of markers
#    python run_local.py test_video.mp4 --dict ARUCO_ORIGINAL


import argparse
import os
import platform
import time
import cv2
from aruco_detector import ArucoProcessor
from face_detector import FaceProcessor

# On macOS, AVFoundation is the backend that sees Continuity Camera
BACKEND = cv2.CAP_AVFOUNDATION if platform.system() == "Darwin" else cv2.CAP_ANY


def read_with_warmup(cap, timeout=3.0):
    #timeout for opening the camera
    deadline = time.time() + timeout
    while time.time() < deadline:
        ok, frame = cap.read()
        if ok:
            return True, frame
        time.sleep(0.1)
    return False, None


#list the available cameras (for personal case it is mac webcam and iph camera)
def list_cameras(max_index=4):
    print("Probing cameras (macOS may ask for camera permission the first time)...")
    print("(Warnings about 'out device of bound' just mean that index doesn't exist.)")
    for i in range(max_index):
        cap = cv2.VideoCapture(i, BACKEND)
        if cap.isOpened():
            ok, frame = read_with_warmup(cap)
            if ok:
                h, w = frame.shape[:2] #height x width
                print(f"  index {i}: {w}x{h}")
            else:
                print(f"  index {i}: opened but sent no frames (is the iPhone locked and in landscape?)")
        cap.release()
    print("Tip: run each index and look at the window to see which one is your iPhone.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("source", nargs="?", default="0",
                   help="camera index, stream URL, or video file") # 0 or 1 in my case
    p.add_argument("--dict", default="4X4_50", help="e.g. 4X4_50, 6X6_250, ARUCO_ORIGINAL") #which aruco marker family to look for
    p.add_argument("--mode", choices=["aruco", "face"], default="aruco",
                   help="what to detect") #aruco or face, hoices rejects anything else
    p.add_argument("--list", action="store_true", help="list available cameras and exit") #a simple on/off switch, store_true means it’s True if you type --list, otherwise False
    args = p.parse_args()

    if args.list:
        list_cameras()
        return

    is_file = os.path.isfile(args.source)
    if args.source.isdigit():
        cap = cv2.VideoCapture(int(args.source), BACKEND)
    else:
        cap = cv2.VideoCapture(args.source)
    if not cap.isOpened():
        raise SystemExit(f"Could not open source: {args.source}")

    processor = FaceProcessor() if args.mode == "face" else ArucoProcessor(args.dict, focal=1140) # focal = (side_px + 50 )/9.75 , sidepx was 222.3 at 50cm distance, so 1140

    # Video files play at their own frame rate, so they behave like a live feed
    fps_file = cap.get(cv2.CAP_PROP_FPS) if is_file else 0
    period = 1.0 / fps_file if fps_file and fps_file > 0 else 0

    prev, paused = time.time(), False
    while True:
        delay = 50
        if not paused:
            start = time.time()
            ok, frame = cap.read()
            if not ok:
                if is_file:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # loop the video
                    continue
                ok, frame = read_with_warmup(cap)  # give slow camera a moment
                if not ok:
                    print("No frames from camera, stopping.")
                    break

            detections, annotated = processor.process(frame) #runs the detector and gets back what it found plus a copy of the frame with boxes drawn on it

            now = time.time()
            fps, prev = 1.0 / max(now - prev, 1e-6), now #FPS = 1 divided by the time since the last frame. max(..., 1e-6) avoids dividing by zero if two frames come at the exact same instant
            if args.mode == "face":
                label = f"faces: {len(detections)}"
            else:
                label = f"ids: {[d.marker_id for d in detections]}"
            cv2.putText(annotated, f"{fps:.0f} FPS  {label}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow("ArUco", annotated)

            spare = period - (time.time() - start)
            delay = max(1, int(spare * 1000)) if period else 1 #this works out how much of the frame’s time slot is left after processing and waits that long, so the video plays at normal speed

        key = cv2.waitKey(delay) & 0xFF
        if key == 27:
            break
        if key == ord(" "):
            paused = not paused #waitKey waits for a key press and also lets the window redraw; & 0xFF keeps only the last 8 bits of the key code, which makes it work the same on every operating system. 27 is Esc, so it quits. ord(" ") is the code for Space, which flips paused between True and False. This part is outside if not paused, so keys still work while paused.

    #just for cleanup
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()