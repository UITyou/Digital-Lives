import random
import threading
import re

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMenu
from PySide6.QtCore import Qt, QTimer, QPoint, Signal
from PySide6.QtGui import QColor, QPixmap, QPainter, QPen


class GameSystem:
    def __init__(self):
        self.riddles = [
            {"question": "什么东西越洗越脏？", "answer": "水"},
            {"question": "什么东西你越给它，它就越少？", "answer": "洞"},
            {"question": "什么东西有头却没有脖子？", "answer": "瓶子"},
            {"question": "什么东西打破了才能用？", "answer": "鸡蛋"},
            {"question": "什么东西早上四条腿，中午两条腿，晚上三条腿？", "answer": "人"},
            {"question": "什么东西看不见摸不着，但能让你感到温暖？", "answer": "阳光"},
            {"question": "什么东西没有翅膀却能飞？", "answer": "气球"},
            {"question": "什么东西有眼睛却看不见？", "answer": "土豆"},
            {"question": "什么东西越冷越硬？", "answer": "冰棍"},
            {"question": "什么东西你有，别人也有，但不能交换？", "answer": "名字"}
        ]
        
        self.drawings = [
            {"topic": "画一个太阳", "hints": ["圆圆的", "有光芒", "黄色的"]},
            {"topic": "画一只小猫", "hints": ["尖尖的耳朵", "长长的尾巴", "有胡须"]},
            {"topic": "画一棵树", "hints": ["高高的树干", "绿色的树叶", "有树枝"]},
            {"topic": "画一栋房子", "hints": ["有屋顶", "有窗户", "有门"]},
            {"topic": "画一朵花", "hints": ["有花瓣", "有花蕊", "绿色的茎"]},
            {"topic": "画一辆汽车", "hints": ["有四个轮子", "有车窗", "有车头"]},
            {"topic": "画一个笑脸", "hints": ["圆圆的脸", "弯弯的眼睛", "微笑的嘴巴"]},
            {"topic": "画一只小鸟", "hints": ["有翅膀", "尖尖的嘴", "有尾巴"]}
        ]
        
        self.find_diff_pairs = [
            {
                "desc": "两幅苹果的图片",
                "diffs": ["一个苹果有叶子，一个没有", "一个苹果是红色，一个是绿色", "一个苹果有果柄，一个没有"]
            },
            {
                "desc": "两幅小猫的图片",
                "diffs": ["一只猫有蝴蝶结，一只没有", "一只猫的眼睛是蓝色，一只黄色", "一只猫有尾巴，一只没有"]
            },
            {
                "desc": "两幅房子的图片",
                "diffs": ["一栋房子有烟囱，一栋没有", "一栋房子的门是红色，一栋是蓝色", "一栋房子有花园，一栋没有"]
            },
            {
                "desc": "两幅花朵的图片",
                "diffs": ["一朵花有五瓣，一朵有六瓣", "一朵花是粉色，一朵是黄色", "一朵花有蜜蜂，一朵没有"]
            },
            {
                "desc": "两幅汽车的图片",
                "diffs": ["一辆车有天窗，一辆没有", "一辆车的颜色是蓝色，一辆是白色", "一辆车有后备箱，一辆没有"]
            }
        ]
        
        self.current_game = None
        self.current_riddle = None
        self.current_drawing = None
        self.current_diff = None
    
    def get_game_list(self):
        return ["猜谜语", "画画", "找不同"]
    
    def is_playing(self):
        return self.current_game is not None


class RiddleGameWindow(QWidget):
    game_finished = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎮 猜谜语游戏")
        self.setFixedSize(400, 350)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        self.riddles = []
        self.current_index = 0
        self.score = 0
        
        self.init_ui()
        self.search_riddles()
    
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        self.title_label = QLabel("猜谜语挑战")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; text-align: center;")
        self.layout.addWidget(self.title_label)
        
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("font-size: 12px; text-align: center; color: #666;")
        self.layout.addWidget(self.progress_label)
        
        self.riddle_label = QLabel("")
        self.riddle_label.setStyleSheet("font-size: 14px; text-align: center; padding: 10px; background-color: #f1f8e9; border-radius: 8px;")
        self.riddle_label.setWordWrap(True)
        self.layout.addWidget(self.riddle_label)
        
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("输入你的答案...")
        self.answer_input.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 5px;")
        self.answer_input.returnPressed.connect(self.submit_answer)
        self.layout.addWidget(self.answer_input)
        
        self.submit_btn = QPushButton("提交答案")
        self.submit_btn.setStyleSheet("background-color: #66bb6a; color: white; border: none; padding: 8px 15px; border-radius: 5px;")
        self.submit_btn.clicked.connect(self.submit_answer)
        self.layout.addWidget(self.submit_btn)
        
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("font-size: 12px; text-align: center; padding: 5px;")
        self.layout.addWidget(self.result_label)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.setStyleSheet("background-color: #ccc; color: white; border: none; padding: 5px 15px; border-radius: 5px;")
        self.close_btn.clicked.connect(self.close)
        self.layout.addWidget(self.close_btn)
    
    def search_riddles(self):
        self.riddle_label.setText("正在搜索谜语...")
        self.submit_btn.setEnabled(False)
        
        def do_search():
            try:
                url = "https://www.baidu.com/s?wd=有趣的谜语大全及答案"
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                search_results = []
                for item in soup.select('.result')[:10]:
                    title = item.find('h3')
                    content = item.find('div', class_='c-abstract')
                    if title and content:
                        search_results.append({
                            'title': title.get_text(),
                            'summary': content.get_text()
                        })
                
                self.riddles = []
                for result in search_results:
                    text = result['summary']
                    if '？' in text or '?' in text:
                        parts = text.split('？') if '？' in text else text.split('?')
                        if len(parts) >= 2:
                            question = parts[0] + '？'
                            answer_part = parts[1]
                            answer = answer_part[:20].replace('。', '').replace('答案：', '').replace('谜底：', '').strip()
                            if len(question) > 5 and len(answer) > 1:
                                self.riddles.append({'question': question, 'answer': answer})
                
                if len(self.riddles) < 3:
                    self.riddles = [
                        {"question": "什么东西越洗越脏？", "answer": "水"},
                        {"question": "什么东西你越给它，它就越少？", "answer": "洞"},
                        {"question": "什么东西有头却没有脖子？", "answer": "瓶子"}
                    ]
                
                self.riddles = self.riddles[:3]
                QTimer.singleShot(0, self.start_game)
            except Exception as e:
                print(f"搜索谜语失败: {e}")
                self.riddles = [
                    {"question": "什么东西越洗越脏？", "answer": "水"},
                    {"question": "什么东西你越给它，它就越少？", "answer": "洞"},
                    {"question": "什么东西有头却没有脖子？", "answer": "瓶子"}
                ]
                QTimer.singleShot(0, self.start_game)
        
        threading.Thread(target=do_search, daemon=True).start()
    
    def start_game(self):
        self.current_index = 0
        self.score = 0
        self.show_riddle()
        self.submit_btn.setEnabled(True)
    
    def show_riddle(self):
        if self.current_index < len(self.riddles):
            riddle = self.riddles[self.current_index]
            self.progress_label.setText(f"第 {self.current_index + 1}/{len(self.riddles)} 题")
            self.riddle_label.setText(f"题目：{riddle['question']}")
            self.answer_input.clear()
            self.result_label.setText("")
            self.answer_input.setFocus()
        else:
            self.finish_game()
    
    def submit_answer(self):
        answer = self.answer_input.text().strip()
        if not answer:
            return
        
        riddle = self.riddles[self.current_index]
        correct_answer = riddle['answer']
        
        if answer in correct_answer or correct_answer in answer:
            self.score += 1
            self.result_label.setText(f"🎉 答对了！答案是：{correct_answer}")
            self.result_label.setStyleSheet("font-size: 12px; text-align: center; padding: 5px; color: green;")
        else:
            self.result_label.setText(f"😅 答错了！正确答案是：{correct_answer}")
            self.result_label.setStyleSheet("font-size: 12px; text-align: center; padding: 5px; color: red;")
        
        self.current_index += 1
        QTimer.singleShot(1500, self.show_riddle)
    
    def finish_game(self):
        self.riddle_label.setText(f"游戏结束！\n得分：{self.score}/{len(self.riddles)}")
        self.answer_input.setEnabled(False)
        self.submit_btn.setEnabled(False)
        self.game_finished.emit(self.score)


class DrawingGameWindow(QWidget):
    game_finished = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎨 画画游戏")
        self.setFixedSize(500, 450)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        self.is_drawing = False
        self.last_point = QPoint()
        self.pen_color = QColor(0, 0, 0)
        self.pen_width = 3
        
        self.topics = [
            "画一个太阳", "画一只小猫", "画一棵树", "画一栋房子", 
            "画一朵花", "画一辆汽车", "画一个笑脸", "画一只小鸟"
        ]
        self.current_topic = random.choice(self.topics)
        
        self.init_ui()
    
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        self.title_label = QLabel(f"主题：{self.current_topic}")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; text-align: center;")
        self.layout.addWidget(self.title_label)
        
        self.canvas = QLabel()
        self.canvas.setStyleSheet("background-color: white; border: 2px solid #ccc;")
        self.canvas.setFixedSize(450, 300)
        self.canvas.mousePressEvent = self.on_mouse_press
        self.canvas.mouseMoveEvent = self.on_mouse_move
        self.canvas.mouseReleaseEvent = self.on_mouse_release
        
        self.pixmap = QPixmap(450, 300)
        self.pixmap.fill(Qt.white)
        self.canvas.setPixmap(self.pixmap)
        
        self.layout.addWidget(self.canvas)
        
        self.tool_bar = QWidget()
        self.tool_layout = QHBoxLayout(self.tool_bar)
        
        colors = [QColor(0, 0, 0), QColor(255, 0, 0), QColor(0, 255, 0), 
                  QColor(0, 0, 255), QColor(255, 255, 0), QColor(255, 165, 0)]
        for color in colors:
            btn = QPushButton()
            btn.setFixedSize(30, 30)
            btn.setStyleSheet(f"background-color: {color.name()}; border-radius: 15px; border: 2px solid #ccc;")
            btn.clicked.connect(lambda checked, c=color: self.set_color(c))
            self.tool_layout.addWidget(btn)
        
        self.tool_layout.addStretch()
        
        self.clear_btn = QPushButton("清除")
        self.clear_btn.setStyleSheet("background-color: #ff9800; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
        self.clear_btn.clicked.connect(self.clear_canvas)
        self.tool_layout.addWidget(self.clear_btn)
        
        self.finish_btn = QPushButton("完成")
        self.finish_btn.setStyleSheet("background-color: #66bb6a; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
        self.finish_btn.clicked.connect(self.finish_drawing)
        self.tool_layout.addWidget(self.finish_btn)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.setStyleSheet("background-color: #ccc; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
        self.close_btn.clicked.connect(self.close)
        self.tool_layout.addWidget(self.close_btn)
        
        self.layout.addWidget(self.tool_bar)
    
    def set_color(self, color):
        self.pen_color = color
    
    def clear_canvas(self):
        self.pixmap.fill(Qt.white)
        self.canvas.setPixmap(self.pixmap)
    
    def on_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.is_drawing = True
            self.last_point = event.pos()
    
    def on_mouse_move(self, event):
        if self.is_drawing and event.buttons() == Qt.LeftButton:
            painter = QPainter(self.pixmap)
            painter.setPen(QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(self.last_point, event.pos())
            painter.end()
            self.canvas.setPixmap(self.pixmap)
            self.last_point = event.pos()
    
    def on_mouse_release(self, event):
        if event.button() == Qt.LeftButton:
            self.is_drawing = False
    
    def finish_drawing(self):
        self.game_finished.emit(True)
        self.close()


class FindDiffGameWindow(QWidget):
    game_finished = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔍 找不同游戏")
        self.setFixedSize(500, 400)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        self.diffs = []
        self.found_count = 0
        
        self.diff_pairs = [
            {
                "desc": "两幅苹果的图片",
                "diffs": ["一个苹果有叶子，一个没有", "一个苹果是红色，一个是绿色", "一个苹果有果柄，一个没有"]
            },
            {
                "desc": "两幅小猫的图片",
                "diffs": ["一只猫有蝴蝶结，一只没有", "一只猫的眼睛是蓝色，一只黄色", "一只猫有尾巴，一只没有"]
            },
            {
                "desc": "两幅房子的图片",
                "diffs": ["一栋房子有烟囱，一栋没有", "一栋房子的门是红色，一栋是蓝色", "一栋房子有花园，一栋没有"]
            },
            {
                "desc": "两幅花朵的图片",
                "diffs": ["一朵花有五瓣，一朵有六瓣", "一朵花是粉色，一朵是黄色", "一朵花有蜜蜂，一朵没有"]
            },
            {
                "desc": "两幅汽车的图片",
                "diffs": ["一辆车有天窗，一辆没有", "一辆车的颜色是蓝色，一辆是白色", "一辆车有后备箱，一辆没有"]
            }
        ]
        
        self.init_ui()
        self.start_game()
    
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        self.title_label = QLabel("找不同挑战")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; text-align: center;")
        self.layout.addWidget(self.title_label)
        
        self.desc_label = QLabel("")
        self.desc_label.setStyleSheet("font-size: 12px; text-align: center; color: #666;")
        self.layout.addWidget(self.desc_label)
        
        self.image_area = QWidget()
        self.image_area.setStyleSheet("background-color: #f5f5f5; border: 2px dashed #ccc; border-radius: 10px;")
        self.image_area.setFixedSize(450, 200)
        
        self.image_layout = QHBoxLayout(self.image_area)
        self.image_layout.setAlignment(Qt.AlignCenter)
        
        self.img1_label = QLabel("图片1")
        self.img1_label.setStyleSheet("font-size: 14px; color: #999; padding: 20px;")
        self.img1_label.setAlignment(Qt.AlignCenter)
        
        self.img2_label = QLabel("图片2")
        self.img2_label.setStyleSheet("font-size: 14px; color: #999; padding: 20px;")
        self.img2_label.setAlignment(Qt.AlignCenter)
        
        self.image_layout.addWidget(self.img1_label)
        self.image_layout.addWidget(self.img2_label)
        
        self.layout.addWidget(self.image_area)
        
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("font-size: 12px; text-align: center;")
        self.layout.addWidget(self.progress_label)
        
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("输入你找到的不同点...")
        self.answer_input.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 5px;")
        self.answer_input.returnPressed.connect(self.submit_answer)
        self.layout.addWidget(self.answer_input)
        
        self.submit_btn = QPushButton("提交答案")
        self.submit_btn.setStyleSheet("background-color: #66bb6a; color: white; border: none; padding: 8px 15px; border-radius: 5px;")
        self.submit_btn.clicked.connect(self.submit_answer)
        self.layout.addWidget(self.submit_btn)
        
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("font-size: 12px; text-align: center; padding: 5px;")
        self.layout.addWidget(self.result_label)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.setStyleSheet("background-color: #ccc; color: white; border: none; padding: 5px 15px; border-radius: 5px;")
        self.close_btn.clicked.connect(self.close)
        self.layout.addWidget(self.close_btn)
    
    def start_game(self):
        self.current_diff = random.choice(self.diff_pairs)
        self.diffs = self.current_diff['diffs'].copy()
        self.found_count = 0
        
        self.desc_label.setText(f"描述：{self.current_diff['desc']}")
        self.progress_label.setText(f"已找到：{self.found_count}/{len(self.diffs)}")
        self.answer_input.clear()
        self.result_label.setText("")
        self.answer_input.setFocus()
    
    def submit_answer(self):
        answer = self.answer_input.text().strip()
        if not answer:
            return
        
        found = False
        for diff in self.diffs[:]:
            if answer in diff or diff in answer:
                self.diffs.remove(diff)
                self.found_count += 1
                found = True
                break
        
        if found:
            self.result_label.setText("✅ 正确！继续找！")
            self.result_label.setStyleSheet("font-size: 12px; text-align: center; padding: 5px; color: green;")
            self.progress_label.setText(f"已找到：{self.found_count}/{len(self.current_diff['diffs'])}")
            
            if len(self.diffs) == 0:
                QTimer.singleShot(1000, self.finish_game)
        else:
            self.result_label.setText("😅 不对哦，再仔细看看！")
            self.result_label.setStyleSheet("font-size: 12px; text-align: center; padding: 5px; color: red;")
        
        self.answer_input.clear()
    
    def finish_game(self):
        self.result_label.setText(f"🎉 恭喜你找到了所有不同！")
        self.answer_input.setEnabled(False)
        self.submit_btn.setEnabled(False)
        self.game_finished.emit(self.found_count)