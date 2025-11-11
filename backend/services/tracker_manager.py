from backend.services.sort.sort import Sort
from typing import Dict
from collections import OrderedDict


# WARNING: this is no more thread safe!
class CameraTrackerManager:
    def __init__(self):
        self._trackers: Dict[int, Sort] = {}
        self._history: OrderedDict[int, Dict[int, List[str, int]]] = {}
    
    def get_tracker(self, camera_id: int) -> Sort:
        """Get or create tracker for camera"""
        if camera_id not in self._trackers:
            self._trackers[camera_id] = Sort()
        return self._trackers[camera_id]
    
    def get_history(self, camera_id: int):
        if camera_id not in self._history:
            self._history[camera_id] = OrderedDict()
        return self._history[camera_id]
