import os
import threading

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QMenu
from PySide6.QtCore import Qt, QTimer, QPoint, Signal

from config import CHARACTER_NAME
from src.core.game_system import RiddleGameWindow, DrawingGameWindow, FindDiffGameWindow


class ChatWindow(QWidget):
    emotion_changed = Signal(str)
    response_ready = Signal(str, str, str)
    nurture_updated = Signal()
    
    def __init__(self, avatar_widget, deepseek_client, nurture_system, game_system):
        super().__init__()
        self.avatar_widget = avatar_widget
        self.deepseek_client = deepseek_client
        self.nurture_system = nurture_system
        self.game_system = game_system
        self.character_name = CHARACTER_NAME
        self.setWindowTitle(f"{CHARACTER_NAME} - 数字生命")
        self.setFixedSize(400, 550)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.emotion_changed.connect(self.avatar_widget.set_emotion_avatar)
        self.response_ready.connect(self.on_response_ready)
        self.nurture_updated.connect(self.update_nurture_status)
        self.is_at_bottom = True
        self.init_ui()
    
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_bar = QWidget()
        self.title_bar.setStyleSheet("background-color: #4caf50;")
        self.title_bar.setFixedHeight(30)
        self.title_layout = QHBoxLayout(self.title_bar)
        self.title_layout.setContentsMargins(10, 0, 10, 0)
        
        self.title_label = QLabel(f"{self.character_name}")
        self.title_label.setStyleSheet("color: white; font-weight: bold;")
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addStretch()
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setStyleSheet("color: white; background-color: transparent; border: none; font-size: 16px;")
        self.close_btn.clicked.connect(self.close)
        self.title_layout.addWidget(self.close_btn)
        self.layout.addWidget(self.title_bar)
        
        self.nurture_bar = QWidget()
        self.nurture_bar.setStyleSheet("background-color: #e8f5e9; padding: 5px; border-radius: 5px;")
        self.nurture_layout = QHBoxLayout(self.nurture_bar)
        
        self.nurture_label = QLabel(self.nurture_system.get_status_text())
        self.nurture_label.setStyleSheet("font-size: 12px;")
        self.nurture_layout.addWidget(self.nurture_label)
        self.nurture_layout.addStretch()
        
        self.feed_btn = QPushButton("🍖")
        self.feed_btn.setStyleSheet("background-color: #ffcc80; border: none; border-radius: 10px; padding: 3px 6px; font-size: 12px;")
        self.feed_btn.clicked.connect(self.feed_pet)
        
        self.game_btn = QPushButton("🎮")
        self.game_btn.setStyleSheet("background-color: #81c784; border: none; border-radius: 10px; padding: 3px 6px; font-size: 12px;")
        self.game_btn.clicked.connect(self.show_game_menu)
        
        self.nurture_layout.addWidget(self.feed_btn)
        self.nurture_layout.addWidget(self.game_btn)
        self.layout.addWidget(self.nurture_bar)
        
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("background-color: #f5f5f5; border: none; padding: 10px;")
        self.chat_area.verticalScrollBar().valueChanged.connect(self.on_scroll_changed)
        self.layout.addWidget(self.chat_area)
        
        self.scroll_to_bottom_btn = QPushButton("↓")
        self.scroll_to_bottom_btn.setParent(self.chat_area)
        self.scroll_to_bottom_btn.setStyleSheet("background-color: #4caf50; color: white; border: none; border-radius: 15px; font-size: 14px;")
        self.scroll_to_bottom_btn.setFixedSize(30, 30)
        self.scroll_to_bottom_btn.clicked.connect(self.scroll_to_bottom)
        self.scroll_to_bottom_btn.hide()
        
        self.input_bar = QWidget()
        self.input_bar.setStyleSheet("background-color: white; border-top: 1px solid #ddd;")
        self.input_layout = QHBoxLayout(self.input_bar)
        self.input_layout.setContentsMargins(5, 5, 5, 5)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入消息...")
        self.input_field.returnPressed.connect(self.send_message)
        self.input_layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton("发送")
        self.send_btn.setStyleSheet("background-color: #4caf50; color: white; border: none; border-radius: 5px; padding: 5px 15px;")
        self.send_btn.clicked.connect(self.send_message)
        self.input_layout.addWidget(self.send_btn)
        self.layout.addWidget(self.input_bar)
    
    def load_history(self):
        messages = self.deepseek_client.get_history_messages()
        for msg in messages:
            align = "right" if msg["sender"] == "user" else "left"
            color = "#66bb6a" if msg["sender"] == "user" else "white"
            text_color = "white" if msg["sender"] == "user" else "#333"
            self.chat_area.append(f"<p style='text-align: {align};'><span style='background-color: {color}; color: {text_color}; padding: 5px 10px; border-radius: 10px;'>{'你' if msg['sender'] == 'user' else self.character_name}: {msg['content']}</span></p>")
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())
        self.is_at_bottom = True
    
    def add_message(self, sender, message, image_url=None):
        align = "right" if sender == "你" else "left"
        color = "#66bb6a" if sender == "你" else "white"
        text_color = "white" if sender == "你" else "#333"
        
        if image_url:
            img_html = f"<img src='{image_url}' style='max-width: 200px; max-height: 200px; border-radius: 10px; display: block; margin: 5px auto;'>"
            self.chat_area.append(f"<p style='text-align: {align};'><span style='background-color: {color}; color: {text_color}; padding: 5px 10px; border-radius: 10px;'>{sender}: {message}</span>{img_html}</p>")
        else:
            self.chat_area.append(f"<p style='text-align: {align};'><span style='background-color: {color}; color: {text_color}; padding: 5px 10px; border-radius: 10px;'>{sender}: {message}</span></p>")
        
        self.chat_area.repaint()
        
        if sender == "你":
            self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())
            self.is_at_bottom = True
        elif self.is_at_bottom:
            self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())
        else:
            self.scroll_to_bottom_btn.show()
            self.update_scroll_button_position()
    
    def on_scroll_changed(self, value):
        scroll_bar = self.chat_area.verticalScrollBar()
        max_value = scroll_bar.maximum()
        self.is_at_bottom = value >= max_value - 30
        if self.is_at_bottom:
            self.scroll_to_bottom_btn.hide()
    
    def scroll_to_bottom(self):
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())
        self.is_at_bottom = True
        self.scroll_to_bottom_btn.hide()
    
    def update_scroll_button_position(self):
        chat_rect = self.chat_area.geometry()
        btn_width = 30
        btn_height = 30
        x = chat_rect.right() - btn_width - 10
        y = chat_rect.bottom() - btn_height - 10
        self.scroll_to_bottom_btn.setGeometry(x, y, btn_width, btn_height)
    
    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, self.update_scroll_button_position)
    
    def on_response_ready(self, reply, emotion, image_url=None):
        self.add_message(self.character_name, reply, image_url)
        self.emotion_changed.emit(emotion)
        self.send_btn.setEnabled(True)
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        
        leveled_up = self.nurture_system.gain_exp(10)
        self.nurture_system.gain_intimacy(2)
        self.nurture_system.add_mood(5)
        self.nurture_updated.emit()
        
        if emotion == 'happy':
            self.avatar_widget.sound_player.play_random_happy_sound()
        
        if leveled_up:
            self.show_level_up_animation()
    
    def update_nurture_status(self):
        self.nurture_label.setText(self.nurture_system.get_status_text())
    
    def feed_pet(self):
        success, msg = self.nurture_system.feed()
        self.add_message("系统", msg)
        self.nurture_updated.emit()
    
    def show_game_menu(self):
        menu = QMenu(self)
        menu.addAction("猜谜语", self.start_riddle_game)
        menu.addAction("画画", self.start_drawing_game)
        menu.addAction("找不同", self.start_find_diff_game)
        menu.exec(self.game_btn.mapToGlobal(self.game_btn.rect().bottomLeft()))
    
    def start_riddle_game(self):
        self.riddle_window = RiddleGameWindow()
        self.riddle_window.game_finished.connect(self.on_riddle_finished)
        self.riddle_window.move(self.pos() + QPoint(50, 50))
        self.riddle_window.show()
    
    def on_riddle_finished(self, score):
        self.nurture_system.play()
        self.nurture_updated.emit()
        self.add_message("系统", f"猜谜语游戏结束！得分：{score}/3，心情+30 🎉")
    
    def start_drawing_game(self):
        self.drawing_window = DrawingGameWindow()
        self.drawing_window.game_finished.connect(self.on_drawing_finished)
        self.drawing_window.move(self.pos() + QPoint(50, 50))
        self.drawing_window.show()
    
    def on_drawing_finished(self, success):
        self.nurture_system.play()
        self.nurture_updated.emit()
        self.add_message("系统", "画画游戏结束！心情+30 🎉")
    
    def start_find_diff_game(self):
        self.find_diff_window = FindDiffGameWindow()
        self.find_diff_window.game_finished.connect(self.on_find_diff_finished)
        self.find_diff_window.move(self.pos() + QPoint(50, 50))
        self.find_diff_window.show()
    
    def on_find_diff_finished(self, score):
        self.nurture_system.play()
        self.nurture_updated.emit()
        self.add_message("系统", f"找不同游戏结束！得分：{score}/3，心情+30 🎉")
    
    def show_level_up_animation(self):
        level_up_widget = QWidget(self)
        level_up_widget.setStyleSheet("background-color: rgba(255, 215, 0, 0.9); border-radius: 20px;")
        level_up_widget.setGeometry(100, 150, 200, 100)
        layout = QVBoxLayout(level_up_widget)
        label = QLabel(f"🎉 升级啦！\nLv.{self.nurture_system.level}")
        label.setStyleSheet("font-size: 20px; font-weight: bold; color: white; text-align: center;")
        layout.addWidget(label)
        level_up_widget.show()
        QTimer.singleShot(2000, level_up_widget.deleteLater)
    
    def send_message(self):
        message = self.input_field.text().strip()
        if not message:
            return
            
        self.add_message("你", message)
        self.input_field.clear()
        
        self.send_btn.setEnabled(False)
        self.input_field.setEnabled(False)
        
        try:
            self.avatar_widget.parent().auto_sender.record_activity()
        except:
            pass
        
        def get_response():
            reply, emotion, image_url = self.deepseek_client.chat(message)
            self.response_ready.emit(reply, emotion, image_url)
            
        threading.Thread(target=get_response, daemon=True).start()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().y() < 30:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and event.position().y() < 30:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()