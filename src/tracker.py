from deep_sort_realtime.deepsort_tracker import DeepSort

class ObjectTracker:
    def __init__(self, max_age=30, n_init=3):
        """
        Initializes DeepSORT tracker.
        - max_age: Frames to keep a track alive without detection.
        - n_init: Number of consecutive detections before a track is confirmed.
        """
        self.tracker = DeepSort(max_age=max_age, n_init=n_init)

    def update(self, detections, frame):
        """
        Updates tracks with new detections.
        detections format: list of [ [x1, y1, w, h], confidence, class_id ]
        """
        tracks = self.tracker.update_tracks(detections, frame=frame)
        return tracks
