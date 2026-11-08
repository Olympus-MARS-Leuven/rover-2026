#run with python color_test.py and place the mp4 video inside camera directory, at the root
import cv2

VIDEO = "../erc_leo_2021.mp4"
cap = cv2.VideoCapture(VIDEO)
#quick check
if not cap.isOpened():
    raise SystemExit(f"Could not open {VIDEO}")

state = {"frame": None, "clicks": []}

#function to react to clicks
def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and state["frame"] is not None:
        frame = state["frame"]

        b, g, r = frame[y, x] #pixel at the click :p

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = hsv[y, x]

        print(f"({x},{y})  BGR=({b},{g},{r})  HSV=({h},{s},{v})")
        state["clicks"].append((x, y))

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
        state["frame"] = frame
        state["clicks"] = []

    display = state["frame"].copy()
    for (cx, cy) in state["clicks"]:
        cv2.circle(display, (cx, cy), 5, (0, 255, 0), 2) #draws the circle: image, where the middle goes in pixels, how big from the centre, bgr, line width
    cv2.imshow("video", display)

    # clicked on deep blue houses to create contrast
    # (657,346)  BGR=(132,55,10)  HSV=(109,236,132)
    # (630,329)  BGR=(76,13,10)  HSV=(119,221,76)
    # (814,389)  BGR=(59,6,9)  HSV=(122,229,59)
    # (812,319)  BGR=(188,193,70)  HSV=(89,163,193)
    # (545,223)  BGR=(219,200,130)  HSV=(96,104,219)
    # (585,125)  BGR=(190,176,74)  HSV=(94,156,190)
    
    hsv = cv2.cvtColor(state["frame"], cv2.COLOR_BGR2HSV)
    lower = (105, 180, 40)     # H, S, V minimum - put your numbers here
    upper = (130, 255, 255)    # H, S, V maximum
    mask = cv2.inRange(hsv, lower, upper)
    cv2.imshow("mask", mask)

    key = cv2.waitKey(30)
    if key == 27:            #Esc
        break
    if key == ord(" "):      #Space
        paused = not paused

cap.release()
cv2.destroyAllWindows()