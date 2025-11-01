import multiprocessing as mp
from multiprocessing import Process, Queue
import logging
from queue import Empty
import numpy as np
import torch
import cv2

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def model_worker(
    worker_id: int,
    input_queue: Queue,
    output_queue: Queue,
):
    """Worker process - loads model once and processes frames from any camera"""
    
    from backend.services.image_processing import LicensePlateProcessor
    from backend.services.tracker_manager import CameraTrackerManager
    
    processor = LicensePlateProcessor()
    tracker_manager = CameraTrackerManager()
    
    logger.info(f"Worker {worker_id} started on device: {processor.device}")
    
    while True:
        try:
            task = input_queue.get(timeout=1)
            if task is None:
                continue
            
            camera_id = task['camera_id']
            frame = task['frame']
            timestamp = task['timestamp']
            
            tracker = tracker_manager.get_tracker(camera_id)
            
            license_plates = processor.detect_license_plates(frame)
            
            # TODO add history
            detections = []
            if len(license_plates) > 0:
                tracked_plates = tracker.update(license_plates)
                
                for plate in tracked_plates:
                    x1, y1, x2, y2, track_id = plate
                    
                    ious = [
                        max(0, min(x2, px2) - max(x1, px1)) *
                        max(0, min(y2, py2) - max(y1, py1))
                        for px1, py1, px2, py2, _ in license_plates
                    ]
                    confidence = license_plates[np.argmax(ious)][4] if ious else 0.0
                    
                    bbox = (int(x1), int(y1), int(x2), int(y2))
                    plate_roi = processor.extract_plate_roi(frame, bbox)
                    ocr_result = processor.recognize_plate_text(plate_roi, int(track_id))
                    
                    if ocr_result['text']:
                        detections.append({
                            'id': int(track_id),
                            'bbox': bbox,
                            'confidence': float(confidence),
                            'ocr': ocr_result,
                            'overall_confidence': (confidence + ocr_result['confidence']) / 2
                        })
            
            annotated_frame = processor.annotate_frame(frame, detections)
            ret, jpeg = cv2.imencode('.jpg', annotated_frame)
            if not ret:
                annotated_frame = b''
            annotated_frame = jpeg.tobytes()

            output_queue.put({
                'camera_id': camera_id,
                'annotated_frame': annotated_frame,
                'timestamp': timestamp,
                'detections': detections,
                'worker_id': worker_id
            })
            
        except Empty:
            continue
        except Exception as e:
            logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
    
    logger.info(f"Worker {worker_id} shutting down")


class WorkerPool:
    """Manages pool of worker processes"""
    
    def __init__(self, num_workers: int = 1):
        self.num_workers = num_workers
        self.input_queues = [mp.Queue(maxsize=100) for _ in range(self.num_workers)]
        self.output_queue = mp.Queue()
        self.workers: List[Process] = []
    
    def start(self):
        """Start all worker processes"""
        for i in range(self.num_workers):
            worker = Process(
                target=model_worker,
                args=(i, self.input_queues[i], self.output_queue)
            )
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        logger.info(f"Started {self.num_workers} workers")
    
    def submit_frame(self, camera_id: int, frame: np.ndarray, 
                     timestamp: float):
        """Submit frame for processing (non-blocking)"""
        worker_id = camera_id % self.num_workers # just to avoid sharing the tracker
        try:
            self.input_queues[worker_id].put_nowait({
                'camera_id': camera_id,
                'frame': frame,
                'timestamp': timestamp,
            })
            return True
        except:
            return False  # Queue full, skip frame
    
    def get_result(self, timeout: float = 0.01):
        """Get processing result (non-blocking)"""
        try:
            return self.output_queue.get(timeout=timeout)
        except:
            return None
    
    def shutdown(self):
        """Gracefully shutdown workers"""
        for worker in self.workers:
            worker.join(timeout=5)
            if worker.is_alive():
                worker.terminate()

        for i in range(self.num_workers):
            self.input_queues[i].close()
        self.output_queue.close()
        
        logger.info("Worker pool shutdown complete")

worker_pool = WorkerPool(num_workers=2 if torch.cuda.is_available() else 1)
