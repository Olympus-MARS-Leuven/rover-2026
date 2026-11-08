#run with python color_test.py and place the mp4 video inside /camera directory, at the root
import cv2

VIDEO = "../erc_leo_2021.mp4" #or add your video
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
        ok, frame = cap.read() #read new frame
        if not ok:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0) #when the video ends (ok is False), jump back to frame 0 instead of quitting
            continue
        frame = cv2.resize(frame, None, fx=0.5, fy=0.5) #optional resizing the screen
        state["frame"] = frame
        state["clicks"] = []

    display = state["frame"].copy()
    for (cx, cy) in state["clicks"]:
        cv2.circle(display, (cx, cy), 5, (0, 255, 0), 2) #draws the circle: image, where the middle goes in pixels, how big from the centre, bgr, line width
    

    # clicked on deep blue houses to create contrast
    # (657,346)  BGR=(132,55,10)  HSV=(109,236,132)
    # (630,329)  BGR=(76,13,10)  HSV=(119,221,76)
    # (814,389)  BGR=(59,6,9)  HSV=(122,229,59)
    # (812,319)  BGR=(188,193,70)  HSV=(89,163,193)
    # (545,223)  BGR=(219,200,130)  HSV=(96,104,219)
    # (585,125)  BGR=(190,176,74)  HSV=(94,156,190)

    blurred = cv2.GaussianBlur(state["frame"], (5, 5), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    # values i extracted for deep blue
    # lower = (105, 180, 40)
    # upper = (130, 255, 255)
    h_min = cv2.getTrackbarPos("H min", "mask")
    h_max = cv2.getTrackbarPos("H max", "mask")
    s_min = cv2.getTrackbarPos("S min", "mask")
    s_max = cv2.getTrackbarPos("S max", "mask")
    v_min = cv2.getTrackbarPos("V min", "mask")
    v_max = cv2.getTrackbarPos("V max", "mask")

    lower = (105, 180, 40)
    upper = (130, 255, 255)
    mask = cv2.inRange(hsv, lower, upper)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)) #can try with 3 or 9 to experiment
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    cv2.imshow("mask", mask)

    #contour around the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        biggest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(biggest)
        if area > 300:
                x, y, w, h = cv2.boundingRect(biggest)

                m = cv2.moments(biggest)
                cx = int(m["m10"] / m["m00"])
                cy = int(m["m01"] / m["m00"])

                cv2.drawContours(display, [biggest], -1, (255, 0, 255), 2)
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 255), 2)
                cv2.circle(display, (cx, cy), 6, (0, 0, 255), -1)
                cv2.putText(display, f"blue ({cx},{cy}) {int(area)}px",
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

                print(f"centre=({cx},{cy})  area={int(area)}  box=({x},{y},{w},{h})")

    cv2.imshow("video", display)

    key = cv2.waitKey(30)
    if key == 27:            #Esc
        break
    if key == ord(" "):      #Space
        paused = not paused

cap.release()
cv2.destroyAllWindows()