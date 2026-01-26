import cv2
from ultralytics import YOLO

class PersonDetector:
    def __init__(self, model_path='yolov8n-pose.pt'):
        """
        Initializes the YOLOv8-Pose model for person detection and keypoint extraction.
        Using YOLOv8-Pose allows us to logically infer posture rather than assuming it.
        """
        self.model = YOLO(model_path)

    def detect(self, frame):
        """
        Detects persons in the frame and returns bounding boxes and keypoints.
        Returns: 
            results: List of detections with boxes, confidences, and keypoints.
        """
        results = self.model(frame, classes=[0], verbose=False)  # Class 0 is 'person'
        return results[0]
