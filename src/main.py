# src/main.py
import cv2
import json
import time
import argparse
from src.detector import PersonDetector
from src.tracker import ObjectTracker
from src.logic import PostureAnalyzer

class StandingDetectionSystem:
    def __init__(self, source=0, output_json="data/results.json", on_update_callback=None):
        self.detector = PersonDetector()
        self.tracker = ObjectTracker(max_age=30)
        self.source = source
        self.output_json = output_json
        self.on_update_callback = on_update_callback
        self.standing_count = 0
        self.historical_data = []

    def run(self):
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            print(f"Error: Could not open video source {self.source}")
            return

        print(f"Starting tracking on source: {self.source}")
        print("Press 'q' to quit.")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # 1. Detection
                results = self.detector.detect(frame)
                
                detections = []
                if results.boxes:
                    for i, box in enumerate(results.boxes):
                        coords = box.xyxy[0].cpu().numpy()
                        conf = box.conf[0].cpu().numpy()
                        x1, y1, x2, y2 = coords
                        w, h = x2 - x1, y2 - y1
                        detections.append(([x1, y1, w, h], conf, 'person'))

                # 2. Tracking
                tracks = self.tracker.update(detections, frame)
                
                current_standing_ids = set()
                
                # 3. Process each track
                for track in tracks:
                    if not track.is_confirmed():
                        continue
                    
                    track_id = track.track_id
                    lt_rb = track.to_ltrb() # [left, top, right, bottom]
                    
                    # Match track to YOLO keypoints via IOU
                    # In a high-speed system, we might pass embedding features
                    # Here we map back to the current frame's detections for keypoints
                    best_kpts = None
                    max_iou = 0.0
                    
                    if results.boxes:
                        for i, det_box in enumerate(results.boxes):
                            d_coords = det_box.xyxy[0].cpu().numpy()
                            iou = self._calc_iou(lt_rb, d_coords)
                            if iou > 0.5 and iou > max_iou:
                                max_iou = iou
                                # Check if keypoints exist
                                if results.keypoints is not None and len(results.keypoints) > i:
                                    best_kpts = results.keypoints[i]

                    is_standing = False
                    if best_kpts is not None:
                        is_standing = PostureAnalyzer.is_standing(best_kpts, lt_rb)
                    else:
                        # Fallback if no keypoints matched but track exists
                        h = lt_rb[3] - lt_rb[1]
                        w = lt_rb[2] - lt_rb[0]
                        if w > 0:
                            is_standing = (h / w) > 1.4 # Simple aspect ratio fallback

                    if is_standing:
                        current_standing_ids.add(track_id)
                    
                    # Visualization
                    color = (0, 255, 0) if is_standing else (0, 0, 255)
                    label = f"ID:{track_id}"
                    cv2.rectangle(frame, (int(lt_rb[0]), int(lt_rb[1])), (int(lt_rb[2]), int(lt_rb[3])), color, 2)
                    cv2.putText(frame, label, (int(lt_rb[0]), int(lt_rb[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                self.standing_count = len(current_standing_ids)
                
                # 4. Global Info
                cv2.putText(frame, f"Standing Count: {self.standing_count}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                cv2.imshow("Standing Detection System", frame)

                # 5. Data Snapshot
                snapshot = {
                    "timestamp": time.time(),
                    "standing_count": self.standing_count,
                    "ids": list(current_standing_ids)
                }
                self.historical_data.append(snapshot)
                
                # Real-time Broadcast
                if self.on_update_callback:
                    try:
                        self.on_update_callback(snapshot)
                    except Exception:
                        pass # Don't let callback errors kill the vision loop
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        except KeyboardInterrupt:
            print("Interrupted by user.")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.export_data()

    def _calc_iou(self, boxA, boxB):
        # box: [x1, y1, x2, y2]
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        
        interArea = max(0, xB - xA) * max(0, yB - yA)
        
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        
        union = float(boxAArea + boxBArea - interArea)
        if union == 0: return 0
        return interArea / union

    def export_data(self):
        try:
            with open(self.output_json, 'w') as f:
                json.dump(self.historical_data, f, indent=4)
            print(f"Data successfully exported to {self.output_json}")
        except Exception as e:
            print(f"Failed to export data: {e}")
