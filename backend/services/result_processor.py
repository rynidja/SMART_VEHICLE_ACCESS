import asyncio
from typing import Dict
from backend.services.worker_pool import worker_pool
from backend.database import AsyncSessionLocal
from backend.schemas.plate import PlateStatus
from backend.models import LicensePlate, LicensePlateDetection
from collections import OrderedDict
from backend.core.config import settings
import logging
from sqlalchemy import select

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ResultProcessor:
    def __init__(self):
        self._frames: Dict[int, bytes] = {}
        self._task = None
        self.history = OrderedDict()

    async def start(self):
        self._task = asyncio.create_task(self.result_handler())

    async def result_handler(self):
        while True:
            result = worker_pool.get_result()
            if not result:
                # use the free time to clean history
                while len(self.history) > settings.HISTORY_SIZE_THRESHOLD:
                    self.history.popitem(last=False)

                await asyncio.sleep(0.01)
                continue

            camera_id = result['camera_id']
            self._frames[camera_id] = result['annotated_frame']
            
            for detection in result['detections']:
                plate_text = detection["ocr"]["text"]
                detection_id = detection["id"]
                confidence = detection["overall_confidence"]

                if not plate_text:
                    continue

                prev =  self.history.get(detection_id)

                async with AsyncSessionLocal() as db:
                    try:
                        if prev and prev[0] != plate_text:
                            db_result = await db.execute(
                                select(LicensePlateDetection).where(LicensePlateDetection.id == prev[2])
                            )
                            plate_detection = db_result.scalar_one_or_none()

                            db_result = await db.execute(
                                select(LicensePlate).where(LicensePlate.plate_text.ilike(f"%{plate_text}%"))
                            )
                            plate = db_result.scalar_one_or_none()
                            if plate:
                                plate_detection.status = PlateStatus.from_flags(plate.is_authorized, plate.is_blacklisted)

                            plate_detection.detected_plate_text = plate_text
                            plate_detection.overall_confidence = confidence

                            prev[0] = plate_text
                            prev[1] = confidence

                            await db.commit()
                            self.history.move_to_end(detection_id)
                            continue

                        if prev:
                            self.history.move_to_end(detection_id)
                            continue

                        db_result = await db.execute(
                            select(LicensePlate).where(LicensePlate.plate_text.ilike(f"%{plate_text}%"))
                        )
                        plate = db_result.scalar_one_or_none()
                        plate_id = plate.id if plate else None
                        status = PlateStatus.from_flags(plate.is_authorized, plate.is_blacklisted) if plate else PlateStatus.UNKNOWN

                        new_detection = LicensePlateDetection(
                            detected_plate_text=plate_text,
                            overall_confidence=confidence,
                            status=status,
                            thumbnail_path=None, # TODO add file storage
                            processing_time_ms=detection["processing_time_ms"],
                            detected_at=result["timestamp"],
                            camera_id=camera_id,
                            plate_id=plate_id
                        )

                        db.add(new_detection)
                        await db.commit()
                        await db.refresh(new_detection)

                        self.history[detection_id] = [plate_text, confidence, new_detection.id]
                        self.history.move_to_end(detection_id)
                    except Exception as e:
                        logger.error(f"Error handling results: {e}")


    async def gen_frames(self, camera_id):
        try:
            while True:
                frame = self._frames.get(camera_id)
                if frame is not None:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                # TODO make this dynamic
                await asyncio.sleep(0.1) # for ~10 fps
        except:
            pass

    async def shutdown(self):
        if self._task:
            self._task.cancel()


result_processor = ResultProcessor()
