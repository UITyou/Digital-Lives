from PySide6.QtWidgets import QWidget, QPushButton
from PySide6.QtCore import Qt, QTimer


class PauseButtonWidget(QWidget):
    def __init__(self, avatar_widget):
        super().__init__()
        self.avatar_widget = avatar_widget
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.pause_button = QPushButton("✋", self)
        self.pause_button.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.9);
            color: #66bb6a;
            border: 2px solid #66bb6a;
            border-radius: 16px;
            padding: 2px;
            font-size: 16px;
            font-weight: bold;
        """)
        self.pause_button.setFixedSize(34, 34)
        self.pause_button.clicked.connect(self.on_pause_click)
        
        self.resize(34, 34)
        self.show()
    
    def update_position(self):
        avatar_geometry = self.avatar_widget.geometry()
        x = avatar_geometry.center().x() - self.width() // 2
        y = avatar_geometry.top() - self.height() - 10
        self.move(x, y)
    
    def on_pause_click(self):
        self.avatar_widget.toggle_bounce()