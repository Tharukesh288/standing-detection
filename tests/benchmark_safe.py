import cv2
from ultralytics import YOLO
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("Running Benchmark...")
    
    # We use the raw YOLO model here to leverage its robust internal downloader
    # This will automatically download 'bus.jpg' if not found
    model = YOLO('yolov8n-pose.pt')
    
    # URLs to try (in order of preference)
    urls = [
        "https://ultralytics.com/images/bus.jpg", # Standard reliable test
    ]
    
    results = None
    source_used = ""
    
    for url in urls:
        print(f"Attempting to process: {url}")
        try:
            # Run inference directly on the URL
            # save=True will save the annotated image to 'runs/pose/predict'
            results = model.predict(source=url, save=True, conf=0.25)
            source_used = url
            break
        except Exception as e:
            print(f"Failed to process {url}: {e}")
            continue
            
    if not results:
        print("Could not process any images due to network restrictions.")
        return

    # Results is a list (one per image)
    r = results[0]
    count = len(r.boxes)
    
    print(f"\n===========================================")
    print(f" DETECTION REPORT")
    print(f" Source: {source_used}")
    print(f" Model: YOLOv8n-Pose")
    print(f"-------------------------------------------")
    print(f" PEOPLE DETECTED: {count}")
    print(f"===========================================")
    print(f"Annotated image saved to: {r.save_dir}")

if __name__ == "__main__":
    main()
