import cv2
import os
import json

os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
cv2.setLogLevel(0)


class CameraManager:
    def __init__(self):
        self.cap = None
        self.current_index = None
        self.pan_position = 0
        self.tilt_position = 0
        self.zoom_position = 0
        self.config = self.load_config()
    
    def load_config(self):
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                'controls': {'pan_step': 5, 'tilt_step': 5, 'zoom_step': 100},
                'camera': {'default_camera': 0}
            }
    
    def save_config(self):
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False
    
    def get_pan_step(self):
        return self.config.get('controls', {}).get('pan_step', 5)
    
    def get_tilt_step(self):
        return self.config.get('controls', {}).get('tilt_step', 5)
    
    def get_zoom_step(self):
        return self.config.get('controls', {}).get('zoom_step', 100)
    
    def set_pan_step(self, value):
        self.config['controls']['pan_step'] = max(1, value)
        self.save_config()
    
    def set_tilt_step(self, value):
        self.config['controls']['tilt_step'] = max(1, value)
        self.save_config()
    
    def set_zoom_step(self, value):
        self.config['controls']['zoom_step'] = max(1, value)
        self.save_config()
    
    def find_available_cameras(self):
        available = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available.append(i)
                cap.release()
        return available
    
    def open_camera(self, index):
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        
        self.cap = cv2.VideoCapture(index)
        if self.cap.isOpened():
            self.current_index = index
            return True
        return False
    
    def read_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            return frame
        return None
    
    def release(self):
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
            self.cap = None
            self.current_index = None
    
    def is_opened(self):
        return self.cap is not None and self.cap.isOpened()
    
    def set_pan(self, value):
        if self.cap is None or not self.cap.isOpened():
            return False
        self.pan_position = max(-100, min(100, value))
        try:
            self.cap.set(cv2.CAP_PROP_PAN, self.pan_position)
            return True
        except:
            return False
    
    def set_tilt(self, value):
        if self.cap is None or not self.cap.isOpened():
            return False
        self.tilt_position = max(-100, min(100, value))
        try:
            self.cap.set(cv2.CAP_PROP_TILT, self.tilt_position)
            return True
        except:
            return False
    
    def set_zoom(self, value):
        if self.cap is None or not self.cap.isOpened():
            return False
        self.zoom_position = max(0, value)
        try:
            self.cap.set(cv2.CAP_PROP_ZOOM, self.zoom_position)
            return True
        except:
            return False
    
    def pan_left(self, step=None):
        if step is None:
            step = self.get_pan_step()
        return self.set_pan(self.pan_position - step)
    
    def pan_right(self, step=None):
        if step is None:
            step = self.get_pan_step()
        return self.set_pan(self.pan_position + step)
    
    def tilt_up(self, step=None):
        if step is None:
            step = self.get_tilt_step()
        return self.set_tilt(self.tilt_position + step)
    
    def tilt_down(self, step=None):
        if step is None:
            step = self.get_tilt_step()
        return self.set_tilt(self.tilt_position - step)
    
    def zoom_in(self, step=None):
        if step is None:
            step = self.get_zoom_step()
        return self.set_zoom(self.zoom_position + step)
    
    def zoom_out(self, step=None):
        if step is None:
            step = self.get_zoom_step()
        return self.set_zoom(self.zoom_position - step)
    
    def reset_ptz(self):
        self.set_pan(0)
        self.set_tilt(0)
        self.set_zoom(0)
    
    def calibrate_range(self, direction='zoom'):
        min_val = None
        max_val = None
        
        if direction == 'zoom':
            setter = self.set_zoom
            getter = lambda: self.zoom_position
            initial = 0
            increment = 100
            max_tries = 20
        elif direction == 'pan':
            setter = self.set_pan
            getter = lambda: self.pan_position
            initial = 0
            increment = 10
            max_tries = 25
        elif direction == 'tilt':
            setter = self.set_tilt
            getter = lambda: self.tilt_position
            initial = 0
            increment = 10
            max_tries = 25
        else:
            return None, None
        
        setter(initial)
        for _ in range(max_tries):
            setter(getter() - increment)
            prev = getter()
            setter(getter() - increment)
            if getter() == prev:
                min_val = getter()
                break
        
        setter(initial)
        for _ in range(max_tries):
            setter(getter() + increment)
            prev = getter()
            setter(getter() + increment)
            if getter() == prev:
                max_val = getter()
                break
        
        setter(initial)
        
        return min_val if min_val is not None else -100, max_val if max_val is not None else 100
