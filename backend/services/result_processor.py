import asyncio
from typing import Dict
from backend.services.worker_pool import worker_pool

class ResultProcessor:
    def __init__(self):
        self._frames: Dict[int, bytes] = {}
        self._task = None

    async def start(self):
        self._task = asyncio.create_task(self.result_handler())

    async def result_handler(self):
        while True:
            result = worker_pool.get_result()
            if not result:
                await asyncio.sleep(0.01)
                continue

            camera_id = result['camera_id']
            self._frames[camera_id] = result['annotated_frame']
            
            # TODO do other processing here

    async def gen_frames(self, camera_id):
        try:
            while True:
                frame = self._frames.get(camera_id, None)
                if frame:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                else:
                    break
                await asyncio.sleep(0)
        except:
            pass

    async def shutdown(self):
        if self._task:
            self._task.cancel()


result_processor = ResultProcessor()
