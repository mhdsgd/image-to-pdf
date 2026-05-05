# ui/preview.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from typing import List, Dict
from PIL import Image


class PreviewWidget(QWidget):
    """PDF预览组件"""

    # 信号
    page_changed = pyqtSignal(int)    # 页面改变信号
    zoom_changed = pyqtSignal(float)  # 缩放改变信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.images = []          # type: List[Dict]
        self.current_page = 0     # type: int
        self.total_pages = 0      # type: int
        self.zoom_level = 1.0     # type: float
        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)

        # 预览区域
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        layout.addWidget(self.preview_label)

        # 控制栏
        control_layout = QHBoxLayout()

        # 页面导航
        self.prev_button = QPushButton("上一页")
        self.prev_button.clicked.connect(self.previous_page)
        control_layout.addWidget(self.prev_button)

        self.page_label = QLabel("0 / 0")
        self.page_label.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(self.page_label)

        self.next_button = QPushButton("下一页")
        self.next_button.clicked.connect(self.next_page)
        control_layout.addWidget(self.next_button)

        # 缩放控制
        self.zoom_out_button = QPushButton("缩小")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        control_layout.addWidget(self.zoom_out_button)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(self.zoom_label)

        self.zoom_in_button = QPushButton("放大")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        control_layout.addWidget(self.zoom_in_button)

        self.reset_zoom_button = QPushButton("重置")
        self.reset_zoom_button.clicked.connect(self.reset_zoom)
        control_layout.addWidget(self.reset_zoom_button)

        layout.addLayout(control_layout)

    def set_images(self, images):
        # type: (List[Dict]) -> None
        """设置图片列表"""
        self.images = images
        self.total_pages = len(images)
        self.current_page = 0
        self.update_preview()
        self.update_page_label()

    def update_preview(self):
        """更新预览显示"""
        if not self.images or self.current_page >= len(self.images):
            self.preview_label.clear()
            return

        img_data = self.images[self.current_page]
        img = img_data.get('image')

        if img is None:
            self.preview_label.setText("无法预览")
            return

        # 转换PIL Image为QPixmap
        if img.mode == 'RGB':
            qimg = QImage(img.tobytes(), img.width, img.height, QImage.Format_RGB888)
        elif img.mode == 'RGBA':
            qimg = QImage(img.tobytes(), img.width, img.height, QImage.Format_RGBA8888)
        else:
            img = img.convert('RGB')
            qimg = QImage(img.tobytes(), img.width, img.height, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(qimg)

        # 应用缩放
        scaled_width = int(pixmap.width() * self.zoom_level)
        scaled_height = int(pixmap.height() * self.zoom_level)
        scaled_pixmap = pixmap.scaled(
            scaled_width, scaled_height,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        self.preview_label.setPixmap(scaled_pixmap)

    def update_page_label(self):
        """更新页面标签"""
        self.page_label.setText("{0} / {1}".format(self.current_page + 1, self.total_pages))

    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_preview()
            self.update_page_label()
            self.page_changed.emit(self.current_page)

    def previous_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_preview()
            self.update_page_label()
            self.page_changed.emit(self.current_page)

    def go_to_page(self, page):
        # type: (int) -> None
        """跳转到指定页"""
        if 0 <= page < self.total_pages:
            self.current_page = page
            self.update_preview()
            self.update_page_label()
            self.page_changed.emit(self.current_page)

    def zoom_in(self):
        """放大"""
        if self.zoom_level < 2.0:
            self.zoom_level += 0.1
            self.update_preview()
            self.update_zoom_label()
            self.zoom_changed.emit(self.zoom_level)

    def zoom_out(self):
        """缩小"""
        if self.zoom_level > 0.5:
            self.zoom_level -= 0.1
            self.update_preview()
            self.update_zoom_label()
            self.zoom_changed.emit(self.zoom_level)

    def reset_zoom(self):
        """重置缩放"""
        self.zoom_level = 1.0
        self.update_preview()
        self.update_zoom_label()
        self.zoom_changed.emit(self.zoom_level)

    def update_zoom_label(self):
        """更新缩放标签"""
        self.zoom_label.setText("{0}%".format(int(self.zoom_level * 100)))

    def get_page_info(self):
        # type: () -> Dict
        """获取页面信息"""
        return {
            'current_page': self.current_page,
            'total_pages': self.total_pages,
            'zoom_level': self.zoom_level
        }
