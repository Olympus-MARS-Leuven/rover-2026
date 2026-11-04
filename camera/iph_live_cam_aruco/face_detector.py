#Face detection with the same interface as ArucoProcessor: process(frame) -> (detections, annotated).

#Uses OpenCV's YuNet detector (a small neural network, ~230 KB). The model file is
#downloaded automatically next to this script the first time you run it.
#It finds faces (where they are), it does not recognise who someone is.

from dataclasses import dataclass
import os
import urllib.request
import cv2
import numpy as np

MODEL_URL = ("https://media.githubusercontent.com/media/opencv/opencv_zoo/main/"
             "models/face_detection_yunet/face_detection_yunet_2023mar.onnx")
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "face_detection_yunet_2023mar.onnx")


@dataclass
class FaceDetection:
    box: tuple        # (x, y, w, h) in pixels
    center: tuple     # (x, y) in pixels
    score: float      # confidence 0..1
    landmarks: list   # 5 points: right eye, left eye, nose tip, right & left mouth corner


def _ensure_model():
    if not os.path.isfile(MODEL_PATH) or os.path.getsize(MODEL_PATH) < 100_000:
        print("Downloading face model (one time, ~230 KB)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


class FaceProcessor:
    def __init__(self, score_threshold: float = 0.8): #model must be 80% sure
        _ensure_model()
        # Input size is set per frame in process(), so any camera resolution works
        self.detector = cv2.FaceDetectorYN.create(MODEL_PATH, "", (320, 320), #starting image size, changes
                                                  score_threshold=score_threshold)
        self._size = None

    def process(self, frame: np.ndarray):
        h, w = frame.shape[:2]
        if self._size != (w, h):
            self.detector.setInputSize((w, h))
            self._size = (w, h)

        _, faces = self.detector.detect(frame)

        detections = []
        annotated = frame.copy()
        if faces is not None:
            for f in faces:
                x, y, bw, bh = (int(v) for v in f[:4]) #first four values of the box, x/y top left corner, bw/bh - width/height
                pts = [(int(f[4 + 2 * k]), int(f[5 + 2 * k])) for k in range(5)] #collects the 5 face points
                score = float(f[14])

                cv2.rectangle(annotated, (x, y), (x + bw, y + bh), (0, 200, 255), 2) #drawing the box
                for p in pts:
                    cv2.circle(annotated, p, 3, (0, 255, 0), -1)
                cv2.putText(annotated, f"{score:.2f}", (x, y - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
                detections.append(FaceDetection((x, y, bw, bh),
                                                (x + bw / 2, y + bh / 2), score, pts))
        return detections, annotated