from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QFont
import cv2


class VideoWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setText("Камера не подключена")
        self.setMinimumSize(1280, 720)
        self.setStyleSheet("""
            QLabel {
                background-color: #0d1117;
                color: #8b949e;
                border: 2px dashed #30363d;
                border-radius: 8px;
            }
        """)
        
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.setFont(font)
    
    def display_frame(self, frame):
        if frame is None:
            return
        
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scaled_pixmap)
    
    def show_message(self, message):
        self.setText(message)
        self.setPixmap(QPixmap())
