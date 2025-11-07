import asyncio
import cv2
import time
from backend.services.worker_pool import worker_pool
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class CameraManager:
    def __init__(self):
        self.camera_pool = {}
        self.tasks = []

    async def start_camera(self, camera_id: int, stream_url: str):
        """
        user must ensure not calling this twice
        """
        self.camera_pool[camera_id] = {
            'active': True,
            'stream_url': stream_url,
        }

        task = asyncio.create_task(self.capture_frames(camera_id))
        self.tasks.append(task)
    
    def stop_camera(self, camera_id):
        self.camera_pool[camera_id]['active'] = False

    def is_camera_active(self, camera_id):
        if not self.camera_pool.get(camera_id):
            return False
        return self.camera_pool[camera_id]['active']

    async def shutdown(self):
        for cam in self.camera_pool.values():
            cam['active'] = False

        # Wait for all capture tasks to finish
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
        logger.info("All camera capture tasks stopped")

    async def capture_frames(self, camera_id: int):
        stream_url = self.camera_pool[camera_id]['stream_url']

        cap = cv2.VideoCapture(stream_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        frame_count = 0
        
        while self.camera_pool.get(camera_id, {}).get('active', False):
            ret, frame = cap.read()
            if not ret:
                await asyncio.sleep(0.1)
                continue
            
            frame_count += 1
            if frame_count % settings.FRAME_SKIP != 0:
                continue
            
            submitted = worker_pool.submit_frame(
                camera_id=camera_id,
                frame=frame,
                timestamp=time.time(),
            )
            
            if not submitted:
                logger.warning(f"Camera {camera_id}: worker queue full, skipping frame")
            
            await asyncio.sleep(0.03)  # Yield control
        
        cap.release()
        logger.info(f"Camera {camera_id} capture stopped")


camera_manager = CameraManager()
