import cv2
import requests
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.detector import PersonDetector

def main():
    # URL of a crowded street/concert image (Wikimedia Commons - Public Domain)
    image_url = "https://upload.wikimedia.org/wikipedia/commons/c/c7/Crowd_at_thursday_night_concert_in_downtown_buffalo.jpg" 
    # (This is a crowd of people walking)

    print(f"Downloading benchmark image from {image_url}...")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        resp = requests.get(image_url, stream=True, headers=headers)
        resp.raise_for_status()
        
        # Convert to numpy array for OpenCV
        arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)
        
        if img is None:
            raise ValueError("Failed to decode image")

    except Exception as e:
        print(f"Error downloading image: {e}")
        return

    print("Initializing YOLOv8-Pose Detector...")
    detector = PersonDetector(model_path='yolov8n-pose.pt')
    
    print("Running detection...")
    results = detector.detect(img)
    
    # Count people
    # YOLO results[0].boxes contains all detections
    # By default we filter for class 0 in the detector wrapper, effectively
    count = len(results.boxes)
    
    print(f"\n--- BENCHMARK RESULTS ---")
    print(f"Total People Detected: {count}")
    print(f"-------------------------")
    
    # Visualization
    for box in results.boxes:
        coords = box.xyxy[0].cpu().numpy()
        x1, y1, x2, y2 = map(int, coords)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
    output_path = "data/benchmark_crowd_result.jpg"
    cv2.imwrite(output_path, img)
    print(f"Visual result saved to: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    main()
