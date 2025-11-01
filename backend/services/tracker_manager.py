from backend.services.sort.sort import Sort
from typing import Dict
from threading import Lock


class CameraTrackerManager:
    def __init__(self):
        # TODO add history
        self._trackers: Dict[int, Sort] = {}
        self._lock = Lock()
    
    def get_tracker(self, camera_id: int) -> Sort:
        """Get or create tracker for camera"""
        with self._lock:
            if camera_id not in self._trackers:
                self._trackers[camera_id] = Sort()
            return self._trackers[camera_id]
    
    def remove_tracker(self, camera_id: int):
        """Remove tracker when camera stops"""
        with self._lock:
            if camera_id in self._trackers:
                del self._trackers[camera_id]
