# frontend.py
import sys
import queue
from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout,
    QProgressBar)

from PyQt5.QtGui import QPixmap, QImage, QColor, QPainter, QPen, QIcon
from PyQt5.QtCore import Qt, QTimer

frontend_queue = queue.Queue()


class FaceViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Face Recognition Viewer")
        self.setWindowIcon(QIcon("D:/Majors document/wallpaper/wc3717134-tiktok-wallpapers.jpg"))
        self.setStyleSheet("background-color: #1f1f1f; color: white;")

        layout = QVBoxLayout()

        # ==== IMAGE AREA ====
        self.image_label = QLabel("No Image")
        self.image_label.setFixedSize(600, 500)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            background-color: #141414;
            padding: 12px;
            border-radius: 10px;
            border: 1px solid #333;
        """)

        layout.addWidget(self.image_label)

        # ==== TEXT INFO ====
        self.text_label = QLabel("")
        self.text_label.setStyleSheet("""
            color: #dddddd;
            font-size: 15px;
            padding: 12px;
            background-color: #202020;
            border-radius: 6px;
            border: 1px solid #333;
        """)

        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(self.text_label)

        # ==== PROGRESS BAR ====
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 6px;
                text-align: center;
                color: white;
                font-size: 14px;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #0099ff;
                border-radius: 6px;
            }
        """)

        layout.addWidget(self.progress)

        self.setLayout(layout)
        self.resize(900, 600)

        # Timer đọc queue mỗi 100 ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(100)

    def check_queue(self):
        try:
            data = frontend_queue.get_nowait()

            if "progress" in data:
                self.progress.setValue(data["progress"])
                return

            image = data["image"]
            boxes = data["boxes"]
            names = data["names"]
            text_info = data["info"]

            self.text_label.setText(text_info)

            # === Convert image ===
            h, w, ch = image.shape
            bytes_per_line = ch * w
            qimg = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888)

            pixmap = QPixmap.fromImage(qimg)

            # === Draw bounding boxes ===
            painter = QPainter(pixmap)
            for _, name in zip(boxes, names):  # _ vì chúng ta bỏ boxes, chỉ dùng name
                # Chọn màu theo tên
                pen = QPen(QColor(0, 255, 0), 1) if name != "Alvaro_Uribe" else QPen(QColor(255, 70, 70), 1)
                pen.setJoinStyle(Qt.RoundJoin)
                painter.setPen(pen)

                # Lấy kích thước hiển thị thực tế của QLabel
                label_w = self.image_label.width()
                label_h = self.image_label.height()

                # Tạo bounding box ôm sát khung QLabel
                margin = 0  # khoảng cách giữa ảnh và bounding box
                painter.drawRect(margin, margin, label_w + 20*margin, label_h + 20*margin)
            painter.end()

            scaled = pixmap.scaled(
                self.image_label.width(),
                self.image_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)


        except Exception:
            pass


def update_image(image, boxes, names, text_info):
    frontend_queue.put({
        "image": image,
        "boxes": boxes,
        "names": names,
        "info": text_info
    })

def update_progress_bar(value):
    frontend_queue.put({"progress": value})

def start_frontend():
    app = QApplication(sys.argv)
    viewer = FaceViewer()
    viewer.show()
    sys.exit(app.exec_())
