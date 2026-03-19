import sys
import queue
import datetime
from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout,
    QProgressBar, QLineEdit, QPushButton, QFrame, QListWidget,
    QListWidgetItem, QCheckBox, QGroupBox, QScrollArea, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QImage, QColor, QPainter, QPen, QFont
from PyQt5.QtCore import Qt, QTimer, QSize

# Hàng đợi giao tiếp (Giữ nguyên logic cũ)
frontend_queue = queue.Queue()

# --- CẤU HÌNH GIAO DIỆN (COLORS & STYLES) ---
class StyleConfig:
    BG_MAIN = "#1e1e2e"      # Màu nền chính (Dark Blue-Grey)
    BG_PANEL = "#252535"     # Màu nền các khối
    ACCENT = "#89b4fa"       # Màu nhấn (Xanh dương sáng)
    TEXT_MAIN = "#cdd6f4"    # Màu chữ chính
    TEXT_SUB = "#a6adc8"     # Màu chữ phụ
    BORDER = "#313244"       # Màu viền
    SUCCESS = "#a6e3a1"      # Màu xanh lá (An toàn)
    DANGER = "#f38ba8"       # Màu đỏ (Cảnh báo)
    
    # CSS chung cho toàn app
    STYLESHEET = f"""
        QWidget {{
            background-color: {BG_MAIN};
            color: {TEXT_MAIN};
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
        }}
        QFrame {{
            border: none;
        }}
        /* Image Display Area */
        QLabel#ImageLabel {{
            background-color: #11111b;
            border-radius: 12px;
            border: 2px solid {BORDER};
        }}
        /* Inputs */
        QLineEdit {{
            background-color: {BG_PANEL};
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 8px;
            color: {TEXT_MAIN};
        }}
        QLineEdit:focus {{
            border: 1px solid {ACCENT};
        }}
        /* Buttons */
        QPushButton {{
            background-color: {BG_PANEL};
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #313244;
            border-color: {ACCENT};
        }}
        QPushButton#DangerBtn {{
            background-color: #451a1a;
            border-color: {DANGER};
            color: {DANGER};
        }}
        /* List Widget (Logs) */
        QListWidget {{
            background-color: {BG_PANEL};
            border-radius: 8px;
            border: 1px solid {BORDER};
            outline: none;
        }}
        QListWidget::item {{
            padding: 10px;
            border-bottom: 1px solid {BORDER};
        }}
        /* Group Box */
        QGroupBox {{
            border: 1px solid {BORDER};
            border-radius: 8px;
            margin-top: 20px;
            font-weight: bold;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }}
    """

class FaceViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ thống nhận diện khuôn mặt thông minh")
        self.resize(1280, 760)
        self.setStyleSheet(StyleConfig.STYLESHEET)
        
        # Layout chính là Horizontal: [Sidebar] - [Main Content] - [Right Panel]
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ===========================
        # 1. LEFT SIDEBAR (Bộ lọc & Cài đặt)
        # ===========================
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)

        # Logo / Title nhỏ
        lbl_brand = QLabel("🛡️ BẢN THỬ NGHIỆM")
        lbl_brand.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {StyleConfig.ACCENT}; margin-bottom: 20px;")
        sidebar_layout.addWidget(lbl_brand)

        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Tìm kiếm ...")
        sidebar_layout.addWidget(self.search_bar)

        # Filters Group
        grp_filter = QGroupBox("BỘ LỌC HIỂN THỊ")
        filter_layout = QVBoxLayout()
        self.chk_names = QCheckBox("Hiển thị Tên")
        self.chk_names.setChecked(True)
        self.chk_boxes = QCheckBox("Hiển thị Khung")
        self.chk_boxes.setChecked(True)
        self.chk_unknown = QCheckBox("Cảnh báo người lạ")
        self.chk_unknown.setStyleSheet(f"color: {StyleConfig.DANGER}")
        
        filter_layout.addWidget(self.chk_names)
        filter_layout.addWidget(self.chk_boxes)
        filter_layout.addWidget(self.chk_unknown)
        grp_filter.setLayout(filter_layout)
        sidebar_layout.addWidget(grp_filter)

        # Settings Group
        grp_settings = QGroupBox("HỆ THỐNG")
        settings_layout = QVBoxLayout()
        
        btn_settings = QPushButton("⚙️ Cài đặt Camera")
        btn_report = QPushButton(" Xuất báo cáo")
        btn_clear = QPushButton(" Xóa Log")
        btn_clear.clicked.connect(lambda: self.log_list.clear())

        settings_layout.addWidget(btn_settings)
        settings_layout.addWidget(btn_report)
        settings_layout.addWidget(btn_clear)
        grp_settings.setLayout(settings_layout)
        sidebar_layout.addWidget(grp_settings)

        sidebar_layout.addStretch() # Đẩy mọi thứ lên trên
        
        # Nút thoát khẩn cấp
        btn_exit = QPushButton("🚪 THOÁT ỨNG DỤNG")
        btn_exit.setObjectName("DangerBtn")
        btn_exit.clicked.connect(self.close)
        sidebar_layout.addWidget(btn_exit)

        main_layout.addWidget(sidebar)

        # ===========================
        # 2. CENTER AREA (Image & Status)
        # ===========================
        center_area = QFrame()
        center_layout = QVBoxLayout(center_area)
        center_layout.setContentsMargins(0, 0, 0, 0)

        # Header thông tin trạng thái
        header_layout = QHBoxLayout()
        self.lbl_status = QLabel("🟢 Hệ thống đang hoạt động")
        self.lbl_status.setStyleSheet(f"color: {StyleConfig.SUCCESS}; font-weight: bold;")
        header_layout.addWidget(self.lbl_status)
        header_layout.addStretch()
        
        # Các nút công cụ nhanh phía trên ảnh
        btn_snap = QPushButton("📷 Chụp ảnh")
        btn_pause = QPushButton("⏸️ Tạm dừng")
        header_layout.addWidget(btn_snap)
        header_layout.addWidget(btn_pause)
        
        center_layout.addLayout(header_layout)

        # Image Area (Quan trọng nhất)
        self.image_label = QLabel("Đang chờ tín hiệu Camera...")
        self.image_label.setObjectName("ImageLabel")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(580, 432)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        center_layout.addWidget(self.image_label)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {StyleConfig.BG_PANEL};
                border-radius: 4px;
                height: 8px;
            }}
            QProgressBar::chunk {{
                background-color: {StyleConfig.ACCENT};
                border-radius: 4px;
            }}
        """)
        center_layout.addWidget(self.progress)

        main_layout.addWidget(center_area, stretch=1) # Stretch=1 để chiếm phần lớn

        # ===========================
        # 3. RIGHT PANEL (Logs & Notifications)
        # ===========================
        right_panel = QFrame()
        right_panel.setFixedWidth(300)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        lbl_log_title = QLabel("LỊCH SỬ NHẬN DIỆN")
        lbl_log_title.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        right_layout.addWidget(lbl_log_title)

        # List Widget để hiển thị log đẹp hơn
        self.log_list = QListWidget()
        right_layout.addWidget(self.log_list)

        # Bảng chi tiết nhỏ (Info Box)
        self.info_box = QLabel("Chọn một mục log để xem chi tiết...")
        self.info_box.setWordWrap(True)
        self.info_box.setStyleSheet(f"""
            background-color: {StyleConfig.BG_PANEL};
            padding: 10px;
            border-radius: 8px;
            color: {StyleConfig.TEXT_SUB};
        """)
        self.info_box.setFixedHeight(150)
        right_layout.addWidget(self.info_box)

        main_layout.addWidget(right_panel)

        self.setLayout(main_layout)

        # --- LOGIC TIMER ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(50) # Tăng tốc độ refresh lên 50ms mượt hơn

    def add_log(self, name, time_str):
        """Thêm log vào list widget với icon và màu sắc"""
        name = name.split('_', 1)[0] 
        item = QListWidgetItem()
        is_unknown = name == "Unknown" or name == "Alvaro" # Giả sử Alvaro là người lạ cần cảnh báo
        
        msg = f"{time_str} - {name}"
        item.setText(msg)
        
        if is_unknown:
            item.setForeground(QColor(StyleConfig.DANGER))
            item.setIcon(self.style().standardIcon(self.style().SP_MessageBoxWarning))
        else:
            item.setForeground(QColor(StyleConfig.SUCCESS))
            item.setIcon(self.style().standardIcon(self.style().SP_DialogApplyButton))
            
        self.log_list.insertItem(0, item) # Thêm vào đầu danh sách
        
        # Giới hạn số lượng log để không bị lag
        if self.log_list.count() > 50:
            self.log_list.takeItem(50)

    def check_queue(self):
        try:
            # Dùng get_nowait để không chặn UI
            data = frontend_queue.get_nowait()

            if "progress" in data:
                self.progress.setValue(data["progress"])
                return

            image = data["image"]
            boxes = data["boxes"]
            names = data["names"]
            text_info = data["info"]

            # Cập nhật Info Box (nếu có data mới)
            if text_info and text_info != self.info_box.text():
                self.info_box.setText(f"📝 INFO:\n{text_info}")
                # Giả lập thêm log nếu có người được nhận diện
                if names:
                    now = datetime.datetime.now().strftime("%H:%M:%S")
                    for n in names:
                        # Chỉ thêm log nếu danh sách chưa đầy cái mới nhất (tránh spam log)
                        if self.log_list.count() == 0 or n not in self.log_list.item(0).text():
                             self.add_log(n, now)

            # === Xử lý ảnh ===
            h, w, ch = image.shape
            bytes_per_line = ch * w
            qimg = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)

            # === Vẽ đè lên ảnh (Overlay) ===
            # if self.chk_boxes.isChecked():
            #     painter = QPainter(pixmap)
            #     painter.setRenderHint(QPainter.Antialiasing)
                
            #     # Font chữ vẽ lên ảnh
            #     font = QFont("Arial", 12, QFont.Bold)
            #     painter.setFont(font)

                # for _, name in zip(boxes, names):
                #     # Logic màu sắc
                #     color = QColor(StyleConfig.SUCCESS) 
                #     if name == "Alvaro_Uribe" or name == "Unknown":
                #         color = QColor(StyleConfig.DANGER) # Đỏ cho cảnh báo

                #     pen = QPen(color, 0) # Viền dày 3px
                #     pen.setJoinStyle(Qt.RoundJoin)
                #     painter.setPen(pen)
                    
                #     # Giả lập vẽ box. 
                #     # LƯU Ý: 'box' ở đây trong code cũ bạn không dùng.
                #     # Ở đây tôi giả sử 'box' là tuple (x, y, w, h) hoặc tương tự.
                #     # Vì code cũ bạn vẽ bao quanh Label, code này tôi sẽ vẽ đè lên Pixmap cho chuẩn.
                #     # Nếu box rỗng, tôi vẽ demo một khung giữa hình để bạn thấy hiệu ứng
                    
                #     # --- DEMO BOX (Thay bằng tọa độ thật của bạn) ---
                #     # Giả sử box là [top, right, bottom, left] hoặc [x, y, w, h]
                #     # Vì không biết format backend, tôi vẽ tạm khung hình chữ nhật ở giữa
                #     # Để code thực tế chạy, bạn cần parse biến 'box' chính xác
                    
                #     # Kích thước của QPixmap (kích thước gốc của ảnh video)
                #     pixmap_w = pixmap.width()
                #     pixmap_h = pixmap.height()
                #     margin = 0 # Khoảng cách lề 20px
                    
                #     # Vẽ khung hình chữ nhật cố định, cách lề 20px
                #     rect_x = margin
                #     rect_y = margin
                #     rect_w = pixmap_w - (2 * margin)
                #     rect_h = pixmap_h - (2 * margin)
                    
                #     painter.drawRect(rect_x, rect_y, rect_w, rect_h)
                #     # --- KẾT THÚC VẼ KHUNG CỐ ĐỊNH ---
                    
                #     # if self.chk_names.isChecked():
                #     #     # Vẽ nền đen mờ dưới chữ
                #     #     fm = painter.fontMetrics()
                #     #     text_w = fm.width(name) + 20
                #     #     painter.fillRect(10, 10 - 25, text_w, 25, color)
                        
                #     #     # Vẽ chữ
                #     #     painter.setPen(QColor("black") if name == "Unknown" else QColor("black"))
                #     #     painter.drawText(15, 10 - 7, name)

                # painter.end()

            # Scale ảnh giữ tỷ lệ
            scaled = pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)

        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error in UI: {e}")

# --- HELPER FUNCTIONS (Giữ nguyên để backend gọi) ---
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
    
    # Thiết lập font hệ thống
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    viewer = FaceViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    # Code test chạy thử giao diện (giả lập) nếu chạy trực tiếp file này
    import numpy as np
    print("Đang chạy chế độ Test UI...")
    
    # Tạo thread giả lập gửi dữ liệu
    import threading
    import time
    
    def mock_backend():
        while True:
            # Tạo ảnh nhiễu giả lập camera
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            # Vẽ màu ngẫu nhiên để thấy update
            img[:] = np.random.randint(0, 50, (1, 1, 3)) 
            
            update_image(img, [[0,0,100,100]], ["Alvaro_Uribe"], "Phát hiện đối tượng nghi vấn")
            time.sleep(0.1)
            
    t = threading.Thread(target=mock_backend, daemon=True)
    t.start()
    
    start_frontend()