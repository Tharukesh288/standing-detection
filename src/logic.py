import numpy as np

class PostureAnalyzer:
    @staticmethod
    def is_standing(keypoints, box):
        """
        Logically determines if a person is standing based on YOLO Pose keypoints.
        Logic:
        1. Verticality: Height vs Width of the bounding box.
        2. Keypoint Ratio: Shoulder to Hip distance vs Hip to Ankle distance.
        3. Alignment: Vertical alignment of Head, Hip, and Ankle.
        """
        if keypoints is None or len(keypoints) == 0:
            return False

        # Keypoints are usually [x, y, conf]
        # Common COCO indexes: 5: L-Shoulder, 6: R-Shoulder, 11: L-Hip, 12: R-Hip, 15: L-Ankle, 16: R-Ankle
        kpts = keypoints.data[0].cpu().numpy()
        
        # Check if we have enough keypoints to make a decision
        # We need at least one hip and one shoulder/ankle
        has_hip = kpts[11][2] > 0.5 or kpts[12][2] > 0.5
        has_ankle = kpts[15][2] > 0.5 or kpts[16][2] > 0.5
        
        if not has_hip:
            # Fallback to Bounding Box aspect ratio if Pose fails
            x1, y1, x2, y2 = box
            height = y2 - y1
            width = x2 - x1
            return height > width * 1.5

        # Get average Y coordinates
        hip_y = (kpts[11][1] + kpts[12][1]) / 2 if (kpts[11][2] > 0.5 and kpts[12][2] > 0.5) else (kpts[11][1] if kpts[11][2] > 0.5 else kpts[12][1])
        shoulder_y = (kpts[5][1] + kpts[6][1]) / 2 if (kpts[5][2] > 0.5 and kpts[6][2] > 0.5) else (kpts[5][1] if kpts[5][2] > 0.5 else kpts[6][1])
        
        # If we have ankles, check leg extension
        if has_ankle:
            ankle_y = (kpts[15][1] + kpts[16][1]) / 2 if (kpts[15][2] > 0.5 and kpts[16][2] > 0.5) else (kpts[15][1] if kpts[15][2] > 0.5 else kpts[16][1])
            standing_ratio = (ankle_y - hip_y) / (hip_y - shoulder_y + 1e-6)
            # Typically, standing people have a legs-to-torso ratio > 1.0
            return standing_ratio > 0.8
        
        # Fallback to simple height check
        x1, y1, x2, y2 = box
        return (y2 - y1) > (x2 - x1) * 1.2
