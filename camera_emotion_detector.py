import os
import time
import threading
import tempfile
import shutil

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

from config import HAS_CAMERA


class CameraEmotionDetector(QWidget):
    emotion_detected = Signal(str)
    gaze_detected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.cap = None
        self.last_emotion = 'calm'
        self.emotion_history = []
        self.last_gaze = 'center'
        
    def start(self):
        if not HAS_CAMERA:
            return False
        try:
            import cv2
            
            temp_dir = tempfile.mkdtemp(prefix="ant_cv_")
            
            cascade_files = {
                'haarcascade_frontalface_default.xml': None,
                'haarcascade_eye.xml': None,
                'haarcascade_smile.xml': None
            }
            
            for fname in cascade_files:
                default_path = os.path.join(cv2.data.haarcascades, fname)
                if os.path.exists(default_path):
                    cascade_files[fname] = default_path
                else:
                    for root, dirs, files in os.walk(os.path.dirname(cv2.__file__)):
                        if fname in files:
                            cascade_files[fname] = os.path.join(root, fname)
                            break
            
            for fname, src_path in cascade_files.items():
                if src_path:
                    shutil.copy(src_path, os.path.join(temp_dir, fname))
            
            self.face_cascade = cv2.CascadeClassifier(os.path.join(temp_dir, 'haarcascade_frontalface_default.xml'))
            self.eye_cascade = cv2.CascadeClassifier(os.path.join(temp_dir, 'haarcascade_eye.xml'))
            self.smile_cascade = cv2.CascadeClassifier(os.path.join(temp_dir, 'haarcascade_smile.xml'))
            
            if self.face_cascade.empty() or self.eye_cascade.empty() or self.smile_cascade.empty():
                print("Haar级联文件加载失败")
                return False
                
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    return False
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.running = True
            threading.Thread(target=self.detect_loop, daemon=True).start()
            return True
        except Exception as e:
            print(f"摄像头初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop(self):
        self.running = False
        if self.cap:
            import cv2
            self.cap.release()
            self.cap = None
            cv2.destroyAllWindows()
    
    def detect_loop(self):
        import cv2
        
        while self.running:
            success, image = self.cap.read()
            if not success:
                continue
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            if len(faces) > 0:
                emotion = self.analyze_emotion(image, faces[0])
                if emotion:
                    self.emotion_history.append(emotion)
                    if len(self.emotion_history) > 5:
                        self.emotion_history = self.emotion_history[-5:]
                    most_common = max(set(self.emotion_history), key=self.emotion_history.count)
                    if most_common != self.last_emotion:
                        self.last_emotion = most_common
                        self.emotion_detected.emit(most_common)
                
                gaze = self.detect_gaze(image, faces[0])
                if gaze:
                    if gaze != self.last_gaze:
                        self.last_gaze = gaze
                        self.gaze_detected.emit(gaze)
            time.sleep(0.5)
    
    def detect_gaze(self, image, face_rect):
        try:
            x, y, w, h = face_rect
            frame_width = image.shape[1]
            face_center_x = x + w // 2
            frame_center_x = frame_width // 2
            
            diff = face_center_x - frame_center_x
            threshold = frame_width * 0.15
            
            if diff < -threshold:
                return 'left'
            elif diff > threshold:
                return 'right'
            else:
                return 'center'
        except Exception as e:
            print(f"检测视线方向时出错: {e}")
            return None
    
    def analyze_emotion(self, image, face_rect):
        import cv2
        
        try:
            x, y, w, h = face_rect
            gray_face = cv2.cvtColor(image[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
            eyes = self.eye_cascade.detectMultiScale(gray_face, 1.3, 5)
            smiles = self.smile_cascade.detectMultiScale(gray_face, 1.8, 20)
            
            if len(smiles) > 0 and any(sy + sh/2 > h*0.55 for sx, sy, sw, sh in smiles):
                return 'happy'
            if len(smiles) == 0:
                mouth_avg = cv2.mean(gray_face[int(h*0.6):int(h*0.8), :])[0]
                if mouth_avg < 80:
                    return 'sad'
            
            if len(eyes) == 2:
                eye_dist = abs(eyes[0][0] - eyes[1][0])
                if eye_dist > w * 0.3:
                    return 'surprised'
            
            return 'calm'
        except Exception as e:
            print(f"分析情绪时出错: {e}")
            return None