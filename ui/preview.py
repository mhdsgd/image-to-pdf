# ui/preview.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QTimer
from PyQt5.QtGui import QPixmap, QImage, QCursor
from typing import List, Dict
from PIL import Image
from core.image_processor import ImageProcessor


def _pil_to_qpixmap(pil_img):
    """PIL Image -> QPixmap"""
    if pil_img.mode == 'RGB':
        bpl = pil_img.width * 3
        qimg = QImage(pil_img.tobytes(), pil_img.width, pil_img.height, bpl, QImage.Format_RGB888)
    elif pil_img.mode == 'RGBA':
        bpl = pil_img.width * 4
        qimg = QImage(pil_img.tobytes(), pil_img.width, pil_img.height, bpl, QImage.Format_RGBA8888)
    else:
        pil_img = pil_img.convert('RGB')
        bpl = pil_img.width * 3
        qimg = QImage(pil_img.tobytes(), pil_img.width, pil_img.height, bpl, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg)


class PreviewWidget(QWidget):
    """PDF预览组件"""

    page_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.images = []
        self.current_page = 0
        self.total_pages = 0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._dragging = False
        self._drag_start = None
        self._pan_start_x = 0.0
        self._pan_start_y = 0.0
        self._zoom = 1.0
        self._zoom_min = 0.0
        self._zoom_max = 5.0
        # 原始 QPixmap（页面切换时创建一次）
        self._orig_pixmap = None
        self._orig_pixmap_page = -1
        # 缩放后的 QPixmap 缓存
        self._scaled_pixmap = None
        self._scaled_key = None
        # 系统 pixmap 尺寸上限（保守估计，避免 scaled() 返回空 pixmap）
        self._pix_limit = 16384
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(1, 1)
        self.preview_label.setMouseTracking(True)
        self.preview_label.setCursor(QCursor(Qt.OpenHandCursor))
        self.preview_label.installEventFilter(self)
        layout.addWidget(self.preview_label)

        control_layout = QHBoxLayout()

        self.prev_button = QPushButton("上一页")
        self.prev_button.clicked.connect(self.previous_page)
        control_layout.addWidget(self.prev_button)

        self.page_label = QLabel("0 / 0")
        self.page_label.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(self.page_label)

        self.next_button = QPushButton("下一页")
        self.next_button.clicked.connect(self.next_page)
        control_layout.addWidget(self.next_button)

        self.reset_button = QPushButton("重置")
        self.reset_button.setToolTip("缩放到完整显示")
        self.reset_button.clicked.connect(self.reset_zoom)
        control_layout.addWidget(self.reset_button)

        layout.addLayout(control_layout)

    def _release_cached_image(self, page_index):
        """释放指定页面的缓存 PIL 图片"""
        if 0 <= page_index < len(self.images):
            ImageProcessor.close_image(self.images[page_index])

    def _ensure_orig_pixmap(self):
        """确保当前页的原始 QPixmap 已创建（每页只创建一次）"""
        if self._orig_pixmap is not None and self._orig_pixmap_page == self.current_page:
            return True
        if not self.images or self.current_page >= len(self.images):
            return False
        img_data = self.images[self.current_page]
        img = ImageProcessor.get_image(img_data)
        if img is None:
            return False
        # 释放上一页的缓存（保留当前页供 _restore_cursor / _handle_wheel 使用）
        if self._orig_pixmap_page >= 0 and self._orig_pixmap_page != self.current_page:
            self._release_cached_image(self._orig_pixmap_page)
        self._orig_pixmap = _pil_to_qpixmap(img)
        self._orig_pixmap_page = self.current_page
        self._scaled_pixmap = None
        self._scaled_key = None
        return True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.images:
            self._scaled_pixmap = None
            self._scaled_key = None
            self.update_preview()

    def set_images(self, images):
        # 释放旧列表中所有缓存的 PIL 图片
        for old_data in self.images:
            ImageProcessor.close_image(old_data)
        self.images = images
        self.total_pages = len(images)
        self.current_page = 0
        self._pan_x = 0
        self._pan_y = 0
        self._zoom = 1.0
        self._orig_pixmap = None
        self._orig_pixmap_page = -1
        self._scaled_pixmap = None
        self._scaled_key = None
        self.update_preview()
        self.update_page_label()

    def update_preview(self):
        """更新预览显示"""
        if not self.images or self.current_page >= len(self.images):
            self.preview_label.clear()
            self._orig_pixmap = None
            self._scaled_pixmap = None
            return

        img_data = self.images[self.current_page]
        img = ImageProcessor.get_image(img_data)
        if img is None:
            self.preview_label.setText("无法预览")
            self._orig_pixmap = None
            self._scaled_pixmap = None
            return

        if not self._ensure_orig_pixmap():
            return

        lw = max(1, self.preview_label.width())
        lh = max(1, self.preview_label.height())
        w, h = img.size

        # 计算缩放参数
        cover_scale = max(lw / w, lh / h)
        fit_scale = min(lw / w, lh / h)
        self._zoom_min = fit_scale / cover_scale if cover_scale > 0 else 0.1
        self._zoom = max(self._zoom_min, min(self._zoom, self._zoom_max))

        scale = cover_scale * self._zoom
        sw = max(1, int(w * scale))
        sh = max(1, int(h * scale))

        # 限制 pixmap 尺寸，避免超过系统上限导致 scaled() 返回空 pixmap
        limit = self._pix_limit
        if sw > limit or sh > limit:
            ratio = min(limit / sw, limit / sh)
            sw = max(1, int(sw * ratio))
            sh = max(1, int(sh * ratio))

        cache_key = (self.current_page, self._zoom, lw, lh)
        if self._scaled_key != cache_key:
            transform_mode = Qt.FastTransformation
            self._scaled_pixmap = self._orig_pixmap.scaled(
                sw, sh, Qt.IgnoreAspectRatio, transform_mode
            )
            if self._scaled_pixmap.isNull():
                self._scaled_pixmap = None
                return
            self._scaled_key = cache_key

        self._display(sw, sh, lw, lh)

    def _display(self, sw, sh, lw, lh):
        """裁剪可见区域并显示"""
        if self._scaled_pixmap is None:
            return

        # 使用 pixmap 的实际尺寸（可能被 cap 过）
        pw = self._scaled_pixmap.width()
        ph = self._scaled_pixmap.height()

        # 用实际 pixmap 尺寸限制平移
        max_pan_x = max(0.0, pw - lw)
        max_pan_y = max(0.0, ph - lh)
        self._pan_x = max(0.0, min(self._pan_x, max_pan_x))
        self._pan_y = max(0.0, min(self._pan_y, max_pan_y))

        # 按比例转换 pan 坐系到实际 pixmap 坐标
        # pan 在"完整缩放"坐标系中，pixmap 可能被 cap 过
        if sw > 0 and sh > 0 and (pw != sw or ph != sh):
            rx, ry = pw / sw, ph / sh
            x = int(self._pan_x * rx)
            y = int(self._pan_y * ry)
        else:
            x, y = int(self._pan_x), int(self._pan_y)

        cw = min(lw, pw - x)
        ch = min(lh, ph - y)
        if cw <= 0 or ch <= 0:
            return
        visible = self._scaled_pixmap.copy(x, y, cw, ch)

        self.preview_label.setPixmap(visible)

        if max_pan_x > 0 or max_pan_y > 0:
            self.preview_label.setCursor(QCursor(Qt.OpenHandCursor))
        else:
            self.preview_label.setCursor(QCursor(Qt.ArrowCursor))

    # ── 交互 ──

    def eventFilter(self, obj, event):
        if obj is self.preview_label:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._dragging = True
                self._drag_start = event.globalPos()
                self._pan_start_x = self._pan_x
                self._pan_start_y = self._pan_y
                self.preview_label.setCursor(QCursor(Qt.ClosedHandCursor))
                return True
            elif event.type() == QEvent.MouseMove and self._dragging:
                delta = event.globalPos() - self._drag_start
                self._pan_x = self._pan_start_x - delta.x()
                self._pan_y = self._pan_start_y - delta.y()
                self._fast_pan()
                return True
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                self._dragging = False
                self._restore_cursor()
                return True
            elif event.type() == QEvent.Wheel:
                self._handle_wheel(event)
                return True
        return super().eventFilter(obj, event)

    def _fast_pan(self):
        """拖拽时快速刷新（复用已缩放的 QPixmap，仅裁剪）"""
        if self._scaled_pixmap is None:
            return
        lw = max(1, self.preview_label.width())
        lh = max(1, self.preview_label.height())
        sw, sh = self._scaled_pixmap.width(), self._scaled_pixmap.height()
        self._display(sw, sh, lw, lh)

    def _restore_cursor(self):
        if self.images and 0 <= self.current_page < len(self.images):
            img = ImageProcessor.get_image(self.images[self.current_page])
            if img is not None:
                lw = self.preview_label.width()
                lh = self.preview_label.height()
                w, h = img.size
                scale = max(lw / w, lh / h) * self._zoom
                sw, sh = int(w * scale), int(h * scale)
                if sw > lw or sh > lh:
                    self.preview_label.setCursor(QCursor(Qt.OpenHandCursor))
                    return
        self.preview_label.setCursor(QCursor(Qt.ArrowCursor))

    def _handle_wheel(self, event):
        if not self.images or self.current_page >= len(self.images):
            return
        img = ImageProcessor.get_image(self.images[self.current_page])
        if img is None:
            return

        delta = event.angleDelta().y()
        if delta == 0:
            return
        factor = 1.1 if delta > 0 else 1.0 / 1.1

        old_zoom = self._zoom
        new_zoom = max(self._zoom_min, min(old_zoom * factor, self._zoom_max))
        if new_zoom == old_zoom:
            return

        mx, my = event.pos().x(), event.pos().y()
        ratio = new_zoom / old_zoom
        self._pan_x = (self._pan_x + mx) * ratio - mx
        self._pan_y = (self._pan_y + my) * ratio - my

        self._zoom = new_zoom
        self.update_preview()

    # ── 导航 ──

    def update_page_label(self):
        self.page_label.setText("{0} / {1}".format(self.current_page + 1, self.total_pages))

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._pan_x = 0
            self._pan_y = 0
            self.update_preview()
            self.update_page_label()
            self.page_changed.emit(self.current_page)

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._pan_x = 0
            self._pan_y = 0
            self.update_preview()
            self.update_page_label()
            self.page_changed.emit(self.current_page)

    def go_to_page(self, page):
        if 0 <= page < self.total_pages:
            self.current_page = page
            self._pan_x = 0
            self._pan_y = 0
            self.update_preview()
            self.update_page_label()
            self.page_changed.emit(self.current_page)

    def reset_zoom(self):
        if self.images and 0 <= self.current_page < len(self.images):
            img = ImageProcessor.get_image(self.images[self.current_page])
            if img is not None:
                lw = max(1, self.preview_label.width())
                lh = max(1, self.preview_label.height())
                w, h = img.size
                cover_scale = max(lw / w, lh / h)
                fit_scale = min(lw / w, lh / h)
                self._zoom = fit_scale / cover_scale if cover_scale > 0 else 0.1
        self._pan_x = 0
        self._pan_y = 0
        self._scaled_pixmap = None
        self._scaled_key = None
        self.update_preview()

    def get_page_info(self):
        return {
            'current_page': self.current_page,
            'total_pages': self.total_pages
        }
