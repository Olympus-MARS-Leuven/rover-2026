#run with python color_test.py and place the mp4 video inside camera directory, at the root
import cv2

VIDEO = "../erc_leo_2021.mp4"
cap = cv2.VideoCapture(VIDEO)
#quick check
if not cap.isOpened():
    raise SystemExit(f"Could not open {VIDEO}")

#example loop for running a video with
# while True:
#     ok, frame = cap.read()
#     if not ok:
#         break
#     cv2.imshow("video", frame)
#     if cv2.waitKey(30) == 27: #Esc
#         break

#function to react to clicks
def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print("clicked at", x, y)

cv2.namedWindow("video") #creates window
cv2.setMouseCallback("video", on_mouse) #calls for mouse events

paused = False

while True:
    if not paused:
        ok, frame = cap.read()
        if not ok:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0) #when the video ends (ok is False), jump back to frame 0 instead of quitting
            continue
        # frame = cv2.resize(frame, None, fx=0.5, fy=0.5) #optional resizing the screen

    cv2.imshow("video", frame)

    key = cv2.waitKey(30)
    if key == 27:            #Esc
        break
    if key == ord(" "):      #Space
        paused = not paused

cap.release()
cv2.destroyAllWindows()