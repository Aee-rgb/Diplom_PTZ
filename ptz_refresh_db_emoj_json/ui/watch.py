# ui/watch.py
import threading
import time
import cv2
import numpy as np


class HumanTracker:
    def __init__(self, camera_manager, db_manager=None, deadzone_px=60, cmd_cooldown=0.15):
        self.camera_manager = camera_manager
        self.db = db_manager
        self.deadzone_px = deadzone_px
        self.cmd_cooldown = cmd_cooldown
        self.is_tracking = False
        self._thread = None
        self._stop_event = threading.Event()
        self._last_cmd_time = 0

    def start(self):
        if self.is_tracking:
            return
        self.is_tracking = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._tracking_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_tracking = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def _tracking_loop(self):
        while self.is_tracking and not self._stop_event.is_set():
            if not self.camera_manager.is_opened():
                time.sleep(0.1)
                continue
            frame = self.camera_manager.read_frame()
            if frame is None:
                time.sleep(0.03)
                continue
            bbox = self._detect_person(frame)
            if bbox:
                self._adjust_camera(bbox, frame.shape[:2])
            time.sleep(0.05)

    def _detect_person(self, frame):
        return None  # Заглушка

    def _adjust_camera(self, bbox, frame_shape):
        now = time.time()
        if now - self._last_cmd_time < self.cmd_cooldown:
            return
        h, w = frame_shape
        person_cx = bbox[0] + bbox[2] // 2
        person_cy = bbox[1] + bbox[3] // 2
        frame_cx, frame_cy = w // 2, h // 2
        dx = person_cx - frame_cx
        dy = person_cy - frame_cy

        action = None
        if abs(dx) > self.deadzone_px:
            if dx > 0:
                self.camera_manager.pan_right()
                action = "pan_right"
            else:
                self.camera_manager.pan_left()
                action = "pan_left"
            self._last_cmd_time = now
        elif abs(dy) > self.deadzone_px:
            if dy > 0:
                self.camera_manager.tilt_down()
                action = "tilt_down"
            else:
                self.camera_manager.tilt_up()
                action = "tilt_up"
            self._last_cmd_time = now
        
        # 🔹 Логирование в БД (только при значительных движениях)
        if self.db and action and abs(dx) > self.deadzone_px * 2 or abs(dy) > self.deadzone_px * 2:
            try:
                self.db.log_tracking_event(
                    camera_id=getattr(self.camera_manager, 'current_index', 1) or 1,
                    bbox={"x": int(bbox[0]), "y": int(bbox[1]), "w": int(bbox[2]), "h": int(bbox[3])},
                    confidence=0.85,
                    action=action,
                    ptz_pos={
                        "pan": getattr(self.camera_manager, 'pan_position', 0),
                        "tilt": getattr(self.camera_manager, 'tilt_position', 0),
                        "zoom": getattr(self.camera_manager, 'zoom_position', 0)
                    }
                )
            except:
                pass  # Не блокируем работу при ошибке БД