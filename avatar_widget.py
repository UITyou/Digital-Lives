import os
import random

from PySide6.QtWidgets import QApplication, QWidget, QLabel
from PySide6.QtCore import Qt, QPoint, QTimer, Signal
from PySide6.QtGui import QPixmap

from config import CHARACTER_NAME, DEFAULT_EMOTION, DEFAULT_AVATAR, EMOTION_AVATARS
from src.client.sound_player import SoundPlayer


class AvatarWidget(QWidget):
    clicked = Signal()
    double_clicked = Signal()
    
    def __init__(self, nurture_system=None, parent=None):
        super().__init__(parent)
        self.nurture_system = nurture_system
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(100, 100)
        self.setStyleSheet("background-color: transparent;")
        self.avatar_label = QLabel(self)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setGeometry(0, 0, 100, 100)
        self.character_name = CHARACTER_NAME
        self.current_emotion = DEFAULT_EMOTION
        self.base_avatar = DEFAULT_AVATAR
        self.set_emotion_avatar(DEFAULT_EMOTION)
        self.drag_position = QPoint()
        self.sound_player = SoundPlayer()
        
        self.is_dragging = False
        self.is_bouncing_paused = False
        self.chat_visibility_check = None
        self.last_emotion_before_pause = DEFAULT_EMOTION
        
        self.bounce_timer = QTimer()
        self.bounce_timer.timeout.connect(self.bounce)
        self.bounce_timer.start(33)
        
        self.bounce_x = random.randint(2, 5)
        self.bounce_y = random.randint(2, 5)
        
        self.pause_button_widget = None
        
        self.show()
        self.raise_()
    
    def set_emotion_avatar(self, emotion):
        self.current_emotion = emotion
        avatar_path = EMOTION_AVATARS.get(emotion, DEFAULT_AVATAR)
        
        if os.path.exists(avatar_path):
            pixmap = QPixmap(avatar_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.avatar_label.setPixmap(pixmap)
            else:
                try:
                    from PIL import Image
                    img = Image.open(avatar_path)
                    img = img.convert('RGB')
                    import io
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    pixmap = QPixmap()
                    pixmap.loadFromData(buffer.getvalue())
                    pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.avatar_label.setPixmap(pixmap)
                except Exception:
                    self.avatar_label.setText(f"{self.character_name or '乐乐'}\n{emotion}")
        else:
            self.avatar_label.setText(f"{self.character_name or '乐乐'}\n{emotion}")
    
    def set_chat_visibility_check(self, callback):
        self.chat_visibility_check = callback
    
    def bounce(self):
        if self.is_dragging:
            return
        
        if self.chat_visibility_check and self.chat_visibility_check():
            return
        
        if self.is_bouncing_paused:
            return
        
        screen = QApplication.primaryScreen().geometry()
        new_x = self.x() + self.bounce_x
        new_y = self.y() + self.bounce_y
        
        if new_x <= 0 or new_x >= screen.width() - self.width():
            self.bounce_x = -self.bounce_x
        if new_y <= 0 or new_y >= screen.height() - self.height():
            self.bounce_y = -self.bounce_y
        
        self.move(self.x() + self.bounce_x, self.y() + self.bounce_y)
        
        if self.pause_button_widget:
            self.pause_button_widget.update_position()
    
    def toggle_bounce(self):
        self.is_bouncing_paused = not self.is_bouncing_paused
        
        if self.is_bouncing_paused:
            self.last_emotion_before_pause = self.current_emotion
            self.set_emotion_avatar('surprised')
            if self.pause_button_widget:
                self.pause_button_widget.hide()
        else:
            self.set_emotion_avatar(self.last_emotion_before_pause)
            if self.pause_button_widget:
                self.pause_button_widget.show()
                self.pause_button_widget.update_position()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.drag_start_pos = event.globalPosition().toPoint()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            if self.pause_button_widget:
                self.pause_button_widget.update_position()
            event.accept()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            drag_distance = (event.globalPosition().toPoint() - self.drag_start_pos).manhattanLength()
            
            if self.is_bouncing_paused:
                if drag_distance < 10:
                    self.toggle_bounce()
                    if self.pause_button_widget:
                        self.pause_button_widget.show()
                        self.pause_button_widget.update_position()
                else:
                    if self.pause_button_widget:
                        self.pause_button_widget.update_position()
            else:
                if drag_distance < 10:
                    self.clicked.emit()
            event.accept()
            
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit()
            event.accept()