import os
import sys
import time
import random
import threading

from PySide6.QtWidgets import QApplication, QWidget, QMenu, QFileDialog
from PySide6.QtCore import Qt, QTimer, QPoint, Signal
    
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CHARACTER_NAME, VOLUME, log_debug
from src.core.nurture_system import NurtureSystem
from src.core.game_system import GameSystem
from src.client.deepseek_client import DeepSeekClient
from src.client.camera_emotion_detector import CameraEmotionDetector
from src.client.news_fetcher import NewsFetcher
from src.ui.avatar_widget import AvatarWidget
from src.ui.chat_window import ChatWindow
from src.ui.pause_button import PauseButtonWidget


class AutoMessageSender(QWidget):
    auto_message = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.last_user_activity = time.time()
        self.auto_interval = random.randint(60, 300)
        self.last_auto_send = time.time()
        self.min_interval = 30
        self.news_fetcher = NewsFetcher()
        
    def start(self):
        self.running = True
        threading.Thread(target=self.check_loop, daemon=True).start()
    
    def stop(self):
        self.running = False
    
    def record_activity(self):
        self.last_user_activity = time.time()
    
    def can_send(self):
        return time.time() - self.last_auto_send >= self.min_interval
    
    def check_loop(self):
        while self.running:
            now = time.time()
            if now - self.last_user_activity >= 180 and now - self.last_auto_send >= self.auto_interval:
                self.send_news_message()
                self.last_auto_send = now
                self.auto_interval = random.randint(60, 300)
            time.sleep(30)
    
    def send_auto_message(self):
        self.auto_message.emit(random.choice([
            '你在忙什么呢？', '怎么不理我了？', '今天过得怎么样？', '要不要聊聊天？',
            '我在这里哦，随时等你！', '是不是累了？休息一下吧~', '天气真好，出去走走吧！',
            '有什么开心的事想分享吗？', '我猜你现在可能在工作？', '嘿，还记得我们之前聊过什么吗？'
        ]))
    
    def send_news_message(self):
        news_items = self.news_fetcher.fetch_news()
        if news_items:
            news_text = "我看到一些最新资讯，和你分享一下：\n\n"
            news_text += '\n'.join(f"{i}. {news}" for i, news in enumerate(news_items, 1))
            news_text += f"\n\n{self.news_fetcher.get_opinion(news_items[0])}"
            self.auto_message.emit(news_text)


class SettingsDialog(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("设置")
        self.setFixedSize(300, 350)
        
        from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("数字生命名字:"))
        
        self.name_input = QLineEdit()
        self.name_input.setText(CHARACTER_NAME)
        layout.addWidget(self.name_input)
        
        layout.addWidget(QLabel("DeepSeek API Key:"))
        self.api_input = QLineEdit()
        from config import DEEPSEEK_API_KEY
        self.api_input.setText(DEEPSEEK_API_KEY)
        layout.addWidget(self.api_input)
        
        layout.addWidget(QLabel("头像图片:"))
        avatar_layout = QHBoxLayout()
        self.avatar_path = QLineEdit()
        self.avatar_path.setReadOnly(True)
        avatar_layout.addWidget(self.avatar_path)
        
        self.browse_btn = QPushButton("浏览")
        self.browse_btn.clicked.connect(self.browse_avatar)
        avatar_layout.addWidget(self.browse_btn)
        layout.addLayout(avatar_layout)
        
        layout.addWidget(QLabel(f"音量: {VOLUME}%"))
        self.volume_slider = QLineEdit()
        self.volume_slider.setText(str(VOLUME))
        layout.addWidget(self.volume_slider)
        
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
    def browse_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择头像图片", "", "图片文件 (*.png *.jpg *.jpeg *.gif)")
        if file_path:
            self.avatar_path.setText(file_path)
            
    def save_settings(self):
        name = self.name_input.text().strip() or CHARACTER_NAME
        self.main_window.update_character_name(name)
        
        try:
            volume = int(self.volume_slider.text())
            self.main_window.avatar.sound_player.volume = volume
        except ValueError:
            pass
            
        if self.main_window.deepseek_client.initialize(self.api_input.text(), name):
            if self.avatar_path.text():
                self.main_window.avatar.set_emotion_avatar('calm')
            self.close()
        else:
            print("API密钥无效，请检查")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        log_debug("初始化养成系统...")
        self.nurture_system = NurtureSystem()
        
        log_debug("初始化 DeepSeekClient...")
        self.deepseek_client = DeepSeekClient(self.nurture_system)
        
        log_debug("创建头像窗口...")
        self.avatar = AvatarWidget(self.nurture_system)
        screen = QApplication.primaryScreen().geometry()
        self.avatar.move(screen.width() // 2 - 50, screen.height() // 2 - 50)
        
        QTimer.singleShot(1000, lambda: self.avatar.sound_player.play_sound('greeting'))
        
        log_debug("创建暂停按钮...")
        self.avatar.pause_button_widget = PauseButtonWidget(self.avatar)
        self.avatar.pause_button_widget.update_position()
        self.avatar.pause_button_widget.show()
        
        log_debug("初始化游戏系统...")
        self.game_system = GameSystem()
        
        log_debug("创建聊天窗口...")
        self.chat_window = ChatWindow(self.avatar, self.deepseek_client, self.nurture_system, self.game_system)
        self.chat_window.hide()
        self.avatar.clicked.connect(self.toggle_chat)
        self.avatar.set_chat_visibility_check(lambda: self.chat_window.isVisible())
        
        log_debug("启动养成属性定时衰减...")
        self.nurture_timer = QTimer()
        self.nurture_timer.timeout.connect(self.nurture_tick)
        self.nurture_timer.start(60000)
        
        log_debug("初始化摄像头情绪识别...")
        self.emotion_detector = CameraEmotionDetector()
        self.emotion_detector.emotion_detected.connect(self.on_camera_emotion_detected)
        self.emotion_detector.gaze_detected.connect(self.on_gaze_detected)
        log_debug("摄像头情绪识别启动" + ("成功" if self.emotion_detector.start() else "失败（可能没有摄像头或权限）"))
        
        log_debug("初始化自动消息发送...")
        self.auto_sender = AutoMessageSender()
        self.auto_sender.auto_message.connect(self.on_auto_message)
        self.auto_sender.start()
        log_debug("自动消息发送启动成功")
        
        self.settings_dialog = None
        self.setup_tray_menu()
        
        self.last_emotion = None
        self.emotion_change_time = 0
        self.emotion_change_interval = 3
        
        log_debug("程序启动完成！")
            
    def load_memory_on_startup(self):
        self.deepseek_client.load_memory()
        if self.deepseek_client.character_name != CHARACTER_NAME:
            self.avatar.character_name = self.deepseek_client.character_name
            self.chat_window.character_name = self.deepseek_client.character_name
            
    def toggle_chat(self):
        if self.chat_window.isVisible():
            self.chat_window.hide()
        else:
            self.chat_window.load_history()
            avatar_pos = self.avatar.pos()
            self.chat_window.move(avatar_pos.x() + 110, avatar_pos.y())
            self.chat_window.show()
            self.chat_window.activateWindow()
            
    def setup_tray_menu(self):
        self.avatar.setContextMenuPolicy(Qt.CustomContextMenu)
        self.avatar.customContextMenuRequested.connect(self.show_context_menu)
        
    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.addAction("设置", self.show_settings)
        menu.addAction("清除记忆", self.clear_memory)
        menu.addAction("退出", self.close_app)
        menu.exec(self.avatar.mapToGlobal(pos))
        
    def show_settings(self):
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.show()
        
    def update_character_name(self, name):
        self.avatar.character_name = name
        self.chat_window.character_name = name
        
    def clear_memory(self):
        self.deepseek_client.conversation_history = []
        self.deepseek_client.save_memory()
        self.chat_window.chat_area.clear()
        
    def on_camera_emotion_detected(self, emotion):
        log_debug(f"摄像头检测到情绪: {emotion}")
        now = time.time()
        if emotion != self.last_emotion and now - self.emotion_change_time >= self.emotion_change_interval:
            self.avatar.set_emotion_avatar(emotion)
            self.last_emotion = emotion
            self.emotion_change_time = now
        
        if not self.auto_sender.can_send():
            return
        
        emotion_messages = {
            'happy': ['你在笑什么呀？说出来让我也开心一下！', '看到你这么开心，我也很高兴！', '你在想什么好笑的事吗？'],
            'sad': ['怎么了？看起来有点难过...', '别难过，我会一直陪着你的。', '有什么不开心的事可以跟我说。'],
            'surprised': ['哇！发生了什么让你惊讶的事？', '看起来很惊讶呢，是什么惊喜吗？', '天哪，什么事情让你这么震惊？'],
            'calm': ['你看起来很平静，在想什么呢？', '安静的时光也很美好呢。', '需要我陪你聊聊天吗？']
        }
        
        if emotion in emotion_messages and self.chat_window.isVisible():
            self.chat_window.add_message(self.avatar.character_name, random.choice(emotion_messages[emotion]))
            self.auto_sender.last_auto_send = time.time()
        
    def on_auto_message(self, message):
        log_debug(f"自动发送消息: {message}")
        if self.chat_window.isVisible():
            self.chat_window.add_message(self.avatar.character_name, message)
        self.avatar.set_emotion_avatar('happy')
        
    def on_gaze_detected(self, gaze):
        log_debug(f"视线方向已接收: {gaze}")
        QTimer.singleShot(0, lambda: self.move_avatar_by_gaze(gaze))
        
    def move_avatar_by_gaze(self, gaze):
        screen = QApplication.primaryScreen().geometry()
        current_pos = self.avatar.pos()
        move_step = 100
        
        if gaze == 'left':
            new_x = max(0, current_pos.x() - move_step)
            self.avatar.move(new_x, current_pos.y())
        elif gaze == 'right':
            new_x = min(screen.width() - 100, current_pos.x() + move_step)
            self.avatar.move(new_x, current_pos.y())
            
        if self.chat_window.isVisible():
            avatar_pos = self.avatar.pos()
            self.chat_window.move(avatar_pos.x() + 110, avatar_pos.y())
        
    def nurture_tick(self):
        self.nurture_system.tick()
        if self.chat_window.isVisible():
            self.chat_window.nurture_updated.emit()
        
        issues, is_critical = self.nurture_system.check_critical_status()
        
        if is_critical:
            self.avatar.set_emotion_avatar('sad')
            for issue in issues:
                if self.chat_window.isVisible():
                    self.chat_window.add_message("系统", f"⚠️ {issue}")
            
            if self.nurture_system.mood <= 0 or self.nurture_system.hunger <= 0:
                QTimer.singleShot(1000, self.handle_pet_disappear)
        elif self.nurture_system.mood < 20 or (self.nurture_system.hunger > 0 and self.nurture_system.hunger < 1):
            self.avatar.set_emotion_avatar('sad')
            for issue in issues:
                if self.chat_window.isVisible():
                    self.chat_window.add_message("系统", f"⚠️ {issue}")
        elif self.nurture_system.mood < 60:
            self.avatar.set_emotion_avatar('calm')
    
    def handle_pet_disappear(self):
        self.avatar.set_emotion_avatar('sad')
        if self.chat_window.isVisible():
            self.chat_window.add_message("系统", "💔 乐乐消失了....")
        
        self.deepseek_client.conversation_history = []
        self.deepseek_client.save_memory()
        
        nurture_file = os.path.join(os.path.dirname(__file__), "nurture.json")
        if os.path.exists(nurture_file):
            os.remove(nurture_file)
        
        QTimer.singleShot(2000, QApplication.instance().quit)
        
    def close_app(self):
        self.nurture_timer.stop()
        self.emotion_detector.stop()
        self.auto_sender.stop()
        self.deepseek_client.save_memory()
        self.nurture_system.save_data()
        self.chat_window.close()
        self.avatar.close()
        QApplication.instance().quit()


if __name__ == "__main__":
    import traceback
    error_log = os.path.join(os.path.dirname(__file__), "error.log")
    try:
        app = QApplication(sys.argv)
        
        log_debug("创建主窗口...")
        window = MainWindow()
        window.load_memory_on_startup()
        
        log_debug("进入主事件循环...")
        sys.exit(app.exec())
    except KeyboardInterrupt:
        log_debug("程序被用户中断")
        print("程序已退出")
    except Exception as e:
        with open(error_log, 'a', encoding='utf-8') as f:
            f.write(f"\n{time.strftime('%Y-%m-%d %H:%M:%S')} - {str(e)}\n")
            f.write(traceback.format_exc())
        print(f"程序异常: {e}")
        traceback.print_exc()