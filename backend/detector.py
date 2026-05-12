import cv2
import yaml
from ultralytics import YOLO

class StandingDetector:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        self.model = YOLO(self.config['detection']['model_path'])
        self.conf_thresh = self.config['detection']['confidence_threshold']
        self.aspect_ratio_thresh = self.config['detection']['aspect_ratio_threshold']
        
    def process_frame(self, frame):
        standing_count = 0
        sitting_count = 0
        
        # verbose=False stops it from printing to terminal
        results = self.model(frame, stream=True, classes=[0], conf=self.conf_thresh, verbose=False) # class 0 is person
        
        for r in results:
            boxes = r.boxes
            keypoints = r.keypoints # Pose estimates

            if boxes is None:
                continue
                
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                width = max(1, x2 - x1)
                height = max(1, y2 - y1)
                
                is_standing = False
                
                # Check if we have valid pose data
                if keypoints is not None and keypoints.data.shape[1] >= 15:
                    kps = keypoints.data[i] # [17, 3] tensor (x, y, confidence)
                    
                    l_hip = kps[11]
                    r_hip = kps[12]
                    l_knee = kps[13]
                    r_knee = kps[14]
                    
                    hip_y = -1
                    knee_y = -1
                    
                    # Try finding highly confident left or right joints
                    if l_hip[2] > 0.5 and l_knee[2] > 0.5:
                        hip_y = l_hip[1].item()
                        knee_y = l_knee[1].item()
                    elif r_hip[2] > 0.5 and r_knee[2] > 0.5:
                        hip_y = r_hip[1].item()
                        knee_y = r_knee[1].item()
                        
                    if hip_y != -1 and knee_y != -1:
                        # If the vertical distance from hip to knee is significant, they are standing
                        # People who are sitting form a 90-degree angle, so knee and hip Y-values are close to each other
                        vertical_dist = knee_y - hip_y 
                        
                        # We use > 15% of the total bounding box height as the rule for "Standing"
                        if vertical_dist > (0.15 * height):
                            is_standing = True
                    else:
                        # Fallback to pure aspect ratio if hips/knees are blocked
                        if (height / width) > self.aspect_ratio_thresh:
                            is_standing = True
                else:
                    # Fallback to pure aspect ratio if no pose models are loaded
                    if (height / width) > self.aspect_ratio_thresh:
                        is_standing = True

                # Determine Colors and Counts
                if is_standing:
                    standing_count += 1
                    label = "Standing"
                    color = (140, 190, 163) # Nord Green (BGR)
                else:
                    sitting_count += 1
                    label = "Sitting"
                    color = (106, 97, 191) # Nord Red (BGR)
                    
                # Draw Box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{label}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                # Draw the Skeleton overlay (just connecting dots for visibility)
                if keypoints is not None and keypoints.data.shape[1] >= 17:
                    points = keypoints.data[i].tolist()
                    for pt in points:
                        kx, ky, kconf = pt
                        if kconf > 0.5:
                            cv2.circle(frame, (int(kx), int(ky)), 3, color, -1)
                
        return frame, standing_count, sitting_count
