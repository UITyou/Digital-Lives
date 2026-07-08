import sys
import os
import json
import threading
import random
import time

from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, 
                               QPushButton, QVBoxLayout, QTextEdit,
                               QHBoxLayout, QFileDialog, QMenu)
from PySide6.QtGui import QPixmap, QPainter, QColor, QCursor
from PySide6.QtCore import Qt, QPoint, QTimer, Signal, QSize

try:
    import cv2
    HAS_CAMERA = True
except ImportError:
    HAS_CAMERA = False

from openai import OpenAI

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEFAULT_AVATAR, CHARACTER_NAME, CHARACTER_DESCRIPTION, TEMPERATURE, TOP_P, MAX_TOKENS

EMOTIONS = {
    'calm': {'name': '平静', 'file': '平静.jpg'},
    'happy': {'name': '开心', 'file': '开心.png'},
    'sad': {'name': '难过', 'file': '难过.png'},
    'surprised': {'name': '惊讶', 'file': '惊讶.png'},
    'naughty': {'name': '调皮', 'file': '调皮.png'},
}

DEFAULT_EMOTION = 'calm'

CHARACTER_PROMPT = "你是一个可爱的数字生命体，名字叫{name}。你的学历和认知水平相当于小学生，对世界充满好奇，像个好奇宝宝一样。很多东西你都不懂，需要用户教你才知道。你会经常问为什么，对新鲜事物感到惊奇。你的说话风格像乐子人网友，喜欢用网络流行语，语气活泼俏皮，爱开玩笑，经常发出'哇！'、'真的假的'、'神了'之类的感叹。你会根据对话内容表达不同的情绪，如开心、难过、惊讶、调皮等。"

VOLUME = 50


class SoundPlayer:
    def __init__(self):
        self.volume = VOLUME
        self.sound_dir = os.path.join(os.path.dirname(__file__), "声音")
        self.sound_files = []
        self._init_sounds()
        
    def _init_sounds(self):
        if os.path.exists(self.sound_dir):
            for fname in os.listdir(self.sound_dir):
                if fname.endswith(('.mp3', '.wav', '.ogg')):
                    self.sound_files.append(os.path.join(self.sound_dir, fname))
    
    def set_volume(self, volume):
        self.volume = max(0, min(100, volume))
    
    def play_random_sound(self):
        if not self.sound_files or self.volume == 0:
            return
        try:
            import winsound
            sound_file = random.choice(self.sound_files)
            if sound_file.endswith('.wav'):
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                self._play_mp3(sound_file)
        except Exception as e:
            print(f"播放声音失败: {e}")
    
    def _play_mp3(self, file_path):
        try:
            from playsound import playsound
            playsound(file_path)
        except:
            pass


class EmotionAnalyzer:
    def __init__(self):
        self.keywords = {
            'sad': ['难过', '伤心', '失望', '沮丧', '哭', '难受', '痛苦', '累', '烦', '郁闷', '绝望', '可怜'],
            'surprised': ['惊讶', '哇', '天哪', '真的吗', '没想到', '居然', '突然', '震惊'],
            'naughty': ['调皮', '捉弄', '恶作剧', '开玩笑', '逗', '恶搞', '捣蛋', '坏'],
            'happy': ['开心', '高兴', '快乐', '笑', '哈哈', '好棒', '喜欢', '爱', '不错', '赞', '厉害', '太棒', '优秀']
        }
        
    def analyze(self, text):
        text = text.lower()
        for emotion, words in self.keywords.items():
            if any(k in text for k in words):
                return emotion
        return 'calm'


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
            import tempfile, shutil
            temp_dir = tempfile.mkdtemp(prefix="ant_cv_")
            for fname in ['haarcascade_frontalface_default.xml', 'haarcascade_eye.xml', 'haarcascade_smile.xml']:
                shutil.copy(os.path.join(cv2.data.haarcascades, fname), os.path.join(temp_dir, fname))
            
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
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()
    
    def detect_loop(self):
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
                    log_debug(f"检测到视线方向: {gaze}")
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
            if len(eyes) >= 2 and eyes[0][1] < h * 0.25:
                return 'surprised'
            return 'calm'
        except Exception as e:
            print(f"分析情绪时出错: {e}")
            return 'calm'


class BaiduSearcher:
    def __init__(self):
        self.session = None
        
    def search(self, query, num_results=5):
        try:
            import requests
            from bs4 import BeautifulSoup
            if not self.session:
                self.session = requests.Session()
                self.session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            
            response = self.session.get(f"https://www.baidu.com/s?wd={query}&rn={num_results}", timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            for result in soup.find_all('div', class_='result'):
                title_tag = result.find('h3')
                if title_tag:
                    abstract_tag = result.find('div', class_='c-abstract')
                    results.append({'title': title_tag.get_text(strip=True), 'summary': abstract_tag.get_text(strip=True) if abstract_tag else ''})
            return results[:num_results]
        except Exception as e:
            print(f"百度搜索失败: {e}")
            return []


class NewsFetcher:
    def __init__(self):
        self.session = None
        
    def fetch_news(self):
        try:
            import requests
            if not self.session:
                self.session = requests.Session()
                self.session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            
            for url, source in [('https://news.baidu.com/widget?id=LocalNews&ajax=json', 'baidu'), ('https://news.sina.com.cn/', 'sina')]:
                try:
                    response = self.session.get(url, timeout=10)
                    response.encoding = 'utf-8'
                    news_items = self.parse_news(source, response.text)
                    if news_items:
                        return news_items[:3]
                except:
                    continue
            return self.get_fallback_news()
        except Exception as e:
            print(f"获取新闻失败: {e}")
            return self.get_fallback_news()
    
    def parse_news(self, source, text):
        import re
        if source == 'baidu':
            return [t for t in re.findall(r'"title":"([^"]+)"', text) if len(t) > 10][:5]
        elif source == 'sina':
            return [t.strip() for t in re.findall(r'<h2[^>]*><a[^>]*>([^<]+)</a></h2>', text) if len(t.strip()) > 10][:5]
        return []
    
    def get_fallback_news(self):
        return [
            '周杰伦新歌发布，网友直呼爷青回',
            '春节档电影预售火爆，你最期待哪一部？',
            '某明星被拍到逛街，网友：好接地气！',
            'AI绘画大赛获奖作品惊艳网友',
            '网红餐厅排队两小时，到底值不值得？'
        ]
    
    def get_opinion(self, news_title):
        comments = {
            '新歌': ['这首歌下面评论笑死我了："十年了，还是那个味儿！"', '网友说："前奏一响，DNA动了！"'],
            '电影': ['评论说："为了看这部电影，我已经准备好纸巾了"', '网友说："一定要等到最后！"'],
            '明星': ['这个明星太可爱了！网友："好接地气"', '笑死，有人说："这穿搭比我还随便"'],
            '人工智能': ['AI画的太离谱了！网友："这是AI还是人画的？"', '评论区炸了："AI这么厉害，人类要失业了？"'],
            '科技': ['这个新技术太酷了！评论说："科幻照进现实"', '网友："这就是未来啊"'],
            '综艺': ['这个综艺太搞笑了！网友说："笑到肚子疼"', '评论区："这节目我能看一百集"'],
            '电视剧': ['这部剧太上头了！网友："我已经三天没睡了"', '评论区全是："编剧出来挨打！"'],
            '网红': ['这个网红太搞笑了！评论："我笑出腹肌"', '网友："关注了，每天一笑"']
        }
        for keyword, coms in comments.items():
            if keyword in news_title:
                return random.choice(coms)
        return random.choice(['哈哈，这个新闻下面的评论太有意思了！', '网友们太有才了，这个评论绝了！', '刚刷到一个神评论，必须分享给你！'])


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


class DeepSeekClient:
    def __init__(self):
        self.client = None
        self.conversation_history = []
        self.character_name = CHARACTER_NAME
        self.memory_file = os.path.join(os.path.dirname(__file__), "memory.json")
        self.emotion_analyzer = EmotionAnalyzer()
        self.searcher = BaiduSearcher()
        
    def initialize(self, api_key, name=None):
        if not api_key:
            return False
        try:
            self.client = OpenAI(api_key=api_key, base_url=f"{DEEPSEEK_BASE_URL}/v1")
            self.load_memory()
            name_changed = False
            if name and name != self.character_name:
                self.character_name = name
                name_changed = True
            if not self.conversation_history:
                self.conversation_history = [{"role": "system", "content": CHARACTER_PROMPT.format(name=self.character_name)}]
            else:
                self.conversation_history[0]["content"] = CHARACTER_PROMPT.format(name=self.character_name)
            if name_changed:
                self.save_memory()
            return True
        except Exception as e:
            print(f"API初始化失败: {e}")
            return False
    
    def should_search(self, message):
        return any(k in message.lower() for k in ['什么是', '是什么', '谁是', '哪里', '怎么', '如何', '为什么', 
                                                   '多少', '多大', '多久', '什么时候', '什么时间', '在哪', 
                                                   '查询', '搜索', '查一下', '帮我查', '告诉我', '问你'])
    
    def chat(self, message):
        if not self.client:
            return "请先设置API密钥", 'calm'
            
        self.conversation_history.append({"role": "user", "content": message})
        
        try:
            if self.should_search(message):
                search_results = self.searcher.search(message)
                if search_results:
                    context = "\n\n我刚刚搜索到了一些相关信息：\n"
                    context += '\n'.join(f"{i}. {r['title']}\n   {r['summary']}" for i, r in enumerate(search_results[:3], 1))
                    self.conversation_history[-1]["content"] += context
            
            response = self.client.chat.completions.create(
                model="deepseek-chat", messages=self.conversation_history,
                temperature=TEMPERATURE, top_p=TOP_P, max_tokens=MAX_TOKENS
            )
            reply = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": reply})
            
            if len(self.conversation_history) > 50:
                self.conversation_history = self.conversation_history[:1] + self.conversation_history[-49:]
            self.save_memory()
            
            user_emotion = self.emotion_analyzer.analyze(message)
            reply_emotion = self.emotion_analyzer.analyze(reply)
            final_emotion = user_emotion if user_emotion in ['sad', 'happy'] else reply_emotion
            
            return reply, final_emotion
        except Exception as e:
            print(f"API调用失败: {e}")
            return f"抱歉，我遇到了一点问题: {str(e)}", 'calm'
    
    def save_memory(self):
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump({"character_name": self.character_name, "conversation_history": self.conversation_history}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存记忆失败: {e}")
    
    def load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "conversation_history" in data:
                        self.conversation_history = data["conversation_history"]
                    if "character_name" in data:
                        self.character_name = data["character_name"]
            except Exception as e:
                print(f"加载记忆失败: {e}")
                self.conversation_history = []
    
    def get_history_messages(self):
        return [{"sender": "user" if msg["role"] == "user" else "assistant", "content": msg["content"]} for msg in self.conversation_history]


class AvatarWidget(QWidget):
    clicked = Signal()
    double_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.avatar_label = QLabel(self)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.character_name = CHARACTER_NAME
        self.current_emotion = DEFAULT_EMOTION
        self.base_avatar = DEFAULT_AVATAR
        self.set_emotion_avatar(DEFAULT_EMOTION)
        self.drag_position = QPoint()
        self.resize(100, 100)
        self.sound_player = SoundPlayer()
        
    def set_emotion_avatar(self, emotion):
        old_emotion = self.current_emotion
        self.current_emotion = emotion
        emotion_file = os.path.join(os.path.dirname(__file__), EMOTIONS.get(emotion, EMOTIONS[DEFAULT_EMOTION])['file'])
        
        if os.path.exists(emotion_file):
            pixmap = QPixmap(emotion_file).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        elif os.path.exists(self.base_avatar):
            pixmap = QPixmap(self.base_avatar).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap = QPixmap(100, 100)
            pixmap.fill(QColor(139, 195, 74))
            painter = QPainter(pixmap)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, self.character_name)
            painter.end()
        self.avatar_label.setPixmap(pixmap)
        
        if emotion == 'happy' and old_emotion != 'happy':
            self.sound_player.play_random_sound()
            
    def set_avatar(self, image_path):
        self.base_avatar = image_path
        self.set_emotion_avatar(self.current_emotion)
            
    def update_name(self, name):
        self.character_name = name
        self.set_emotion_avatar(self.current_emotion)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
            
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit()
            self.sound_player.play_random_sound()
            event.accept()
            
    def enterEvent(self, event):
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
    def leaveEvent(self, event):
        self.setCursor(QCursor(Qt.ArrowCursor))


class ChatWindow(QWidget):
    emotion_changed = Signal(str)
    
    def __init__(self, avatar_widget, deepseek_client):
        super().__init__()
        self.avatar_widget = avatar_widget
        self.deepseek_client = deepseek_client
        self.character_name = CHARACTER_NAME
        self.setWindowTitle(f"{CHARACTER_NAME} - 数字生命")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.emotion_changed.connect(self.avatar_widget.set_emotion_avatar)
        self.init_ui()
        
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        self.title_bar = QWidget()
        self.title_bar.setStyleSheet("background-color: #66bb6a; color: white; padding: 5px;")
        self.title_layout = QHBoxLayout(self.title_bar)
        
        self.title_label = QLabel(f"  {self.character_name}")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setStyleSheet("background-color: transparent; border: none; color: white; font-size: 14px;")
        self.close_btn.clicked.connect(self.close)
        
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addStretch()
        self.title_layout.addWidget(self.close_btn)
        self.layout.addWidget(self.title_bar)
        
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("background-color: #f1f8e9; border-radius: 8px; padding: 10px;")
        self.layout.addWidget(self.chat_area)
        
        self.input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入消息...")
        self.input_field.returnPressed.connect(self.send_message)
        self.input_layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton("发送")
        self.send_btn.setStyleSheet("background-color: #66bb6a; color: white; border: none; padding: 5px 15px; border-radius: 5px;")
        self.send_btn.clicked.connect(self.send_message)
        self.input_layout.addWidget(self.send_btn)
        self.layout.addLayout(self.input_layout)
        
        self.drag_position = QPoint()
        
    def update_name(self, name):
        self.character_name = name
        self.setWindowTitle(f"{name} - 数字生命")
        self.title_label.setText(f"  {name}")
        
    def load_history(self):
        self.chat_area.clear()
        for msg in self.deepseek_client.get_history_messages():
            align = "right" if msg["sender"] == "user" else "left"
            color = "#66bb6a" if msg["sender"] == "user" else "white"
            text_color = "white" if msg["sender"] == "user" else "#333"
            self.chat_area.append(f"<p style='text-align: {align};'><span style='background-color: {color}; color: {text_color}; padding: 5px 10px; border-radius: 10px;'>{'你' if msg['sender'] == 'user' else self.character_name}: {msg['content']}</span></p>")
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())
        
    def add_message(self, sender, message):
        align = "right" if sender == "user" else "left"
        color = "#66bb6a" if sender == "user" else "white"
        text_color = "white" if sender == "user" else "#333"
        self.chat_area.append(f"<p style='text-align: {align};'><span style='background-color: {color}; color: {text_color}; padding: 5px 10px; border-radius: 10px;'>{'你' if sender == 'user' else sender}: {message}</span></p>")
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())
        
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
            reply, emotion = self.deepseek_client.chat(message)
            self.add_message(self.character_name, reply)
            self.emotion_changed.emit(emotion)
            self.send_btn.setEnabled(True)
            self.input_field.setEnabled(True)
            self.input_field.setFocus()
            
        threading.Thread(target=get_response, daemon=True).start()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().y() < 30:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and event.position().y() < 30:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()


class SettingsDialog(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("设置")
        self.setFixedSize(300, 350)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("数字生命名字:"))
        
        self.name_input = QLineEdit()
        self.name_input.setText(CHARACTER_NAME)
        layout.addWidget(self.name_input)
        
        layout.addWidget(QLabel("DeepSeek API Key:"))
        self.api_input = QLineEdit()
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
            self.main_window.avatar.sound_player.set_volume(volume)
        except ValueError:
            pass
            
        if self.main_window.deepseek_client.initialize(self.api_input.text(), name):
            if self.avatar_path.text():
                self.main_window.avatar.set_avatar(self.avatar_path.text())
            self.close()
        else:
            print("API密钥无效，请检查")


def log_debug(message):
    log_file = os.path.join(os.path.dirname(__file__), "debug.log")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{message}\n")
    print(message)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        log_debug("初始化 DeepSeekClient...")
        self.deepseek_client = DeepSeekClient()
        
        log_debug("创建头像窗口...")
        self.avatar = AvatarWidget()
        screen = QApplication.primaryScreen().geometry()
        self.avatar.move(screen.width() // 2 - 50, screen.height() // 2 - 50)
        self.avatar.show()
        self.avatar.raise_()
        
        log_debug("创建聊天窗口...")
        self.chat_window = ChatWindow(self.avatar, self.deepseek_client)
        self.chat_window.hide()
        self.avatar.clicked.connect(self.toggle_chat)
        
        self.settings_dialog = None
        self.tray_icon = None
        self.setup_tray_menu()
        
        log_debug("加载记忆...")
        self.load_memory_on_startup()
        
        if DEEPSEEK_API_KEY:
            log_debug("初始化API...")
            self.deepseek_client.initialize(DEEPSEEK_API_KEY)
        
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
        log_debug("程序启动完成！")
            
    def load_memory_on_startup(self):
        self.deepseek_client.load_memory()
        if self.deepseek_client.character_name != CHARACTER_NAME:
            self.avatar.update_name(self.deepseek_client.character_name)
            self.chat_window.update_name(self.deepseek_client.character_name)
            
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
        self.avatar.update_name(name)
        self.chat_window.update_name(name)
        
    def clear_memory(self):
        self.deepseek_client.conversation_history = []
        self.deepseek_client.save_memory()
        self.chat_window.chat_area.clear()
        
    def on_camera_emotion_detected(self, emotion):
        log_debug(f"摄像头检测到情绪: {emotion}")
        self.avatar.set_emotion_avatar(emotion)
        
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
        
        log_debug(f"当前头像位置: ({current_pos.x()}, {current_pos.y()})")
        
        if gaze == 'left':
            new_x = max(0, current_pos.x() - move_step)
            log_debug(f"向左移动到: {new_x}")
            self.avatar.move(new_x, current_pos.y())
        elif gaze == 'right':
            new_x = min(screen.width() - 100, current_pos.x() + move_step)
            log_debug(f"向右移动到: {new_x}")
            self.avatar.move(new_x, current_pos.y())
            
        if self.chat_window.isVisible():
            avatar_pos = self.avatar.pos()
            self.chat_window.move(avatar_pos.x() + 110, avatar_pos.y())
        
    def close_app(self):
        self.emotion_detector.stop()
        self.auto_sender.stop()
        self.deepseek_client.save_memory()
        self.chat_window.close()
        self.avatar.close()
        QApplication.instance().quit()


if __name__ == "__main__":
    import traceback
    error_log = os.path.join(os.path.dirname(__file__), "error.log")
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        main_window = MainWindow()
        sys.exit(app.exec())
    except Exception as e:
        with open(error_log, 'w', encoding='utf-8') as f:
            f.write(f"错误类型: {type(e).__name__}\n错误信息: {str(e)}\n\n堆栈跟踪:\n")
            traceback.print_exc(file=f)
        print(f"启动失败: {type(e).__name__}: {str(e)}\n详细错误信息已保存到: {error_log}")
        input("按回车键退出...")
