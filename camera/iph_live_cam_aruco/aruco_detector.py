# Core ArUco processing. Knows nothing about cameras, files or ROS 2.

# Every frame source (iPhone, webcam, video file, ROS 2 topic) just calls
# ArucoProcessor.process(frame), so this file never changes when you switch
# from your Mac to the rover.

# Requires: pip install opencv-contrib-python   (OpenCV >= 4.7)
from dataclasses import dataclass
import cv2
import numpy as np


@dataclass
class Detection:
    marker_id: int
    corners: np.ndarray  # shape (4, 2): pixel coordinates, clockwise from top-left
    center: tuple        # (x, y) in pixels


class ArucoProcessor:
    def __init__(self, dict_name: str = "4X4_50"): #marker family
        dict_id = getattr(cv2.aruco, "DICT_" + dict_name.upper(), None)
        if dict_id is None:
            raise ValueError(f"Unknown ArUco dictionary: {dict_name}")
        self.detector = cv2.aruco.ArucoDetector(
            cv2.aruco.getPredefinedDictionary(dict_id),
            cv2.aruco.DetectorParameters(),
        )

    def process(self, frame: np.ndarray):
        # Detect markers in a BGR frames
        # Returns (detections, annotated_frame). The input frame is not modified.
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self.detector.detectMarkers(gray)

        detections = []
        annotated = frame.copy()
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(annotated, corners, ids)
            for c, i in zip(corners, ids.flatten()): #c comes from the black border, i from the data grid
                pts = c.reshape(4, 2)
                cx, cy = pts.mean(axis=0)
                detections.append(Detection(int(i), pts, (float(cx), float(cy))))
        return detections, annotated

#   c = these 4 corners
#   ↓                 ↓
#   # # # # # #
#   # . # . . #
#   # # . # . #     ← i = the number these inner cells decode to
#   # # # . . #
#   # # # . # #
#   # # # # # #
#   ↑                 ↑
#id 0 example aruco marker
# 1 0 1 1
# 0 1 0 1
# 0 0 1 1
# 0 0 1 0