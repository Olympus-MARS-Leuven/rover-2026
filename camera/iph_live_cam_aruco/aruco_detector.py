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
    side_px: float
    distance_cm: float = None


class ArucoProcessor:
    def __init__(self, dict_name: str = "4X4_50", marker_cm: float = 9.75, focal: float = None):
        self.marker_cm = marker_cm
        self.focal = focal
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
            for c, i in zip(corners, ids.flatten()):
                pts = c.reshape(4, 2)
                cx, cy = pts.mean(axis=0)

                sides = [np.linalg.norm(pts[k] - pts[(k + 1) % 4]) for k in range(4)]
                side_px = sum(sides) / 4

                distance_cm = None
                if self.focal is not None:
                    distance_cm = self.focal * self.marker_cm / side_px
                    cv2.putText(annotated, f"{distance_cm:.0f} cm", (int(cx), int(cy)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                print(f"id {i}: side_px = {side_px:.1f}")
                detections.append(Detection(int(i), pts, (float(cx), float(cy)),
                                            side_px, distance_cm))
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