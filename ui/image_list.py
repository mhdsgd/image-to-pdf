# ui/image_list.py
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon, QImage
from typing import List, Dict
from PIL import Image


class ImageListWidget(QListWidget):
    """图片列表组件"""

    # 信号
    image_selected = pyqtSignal(int)  # 图片选中信号
    image_deleted = pyqtSignal(int)   # 图片删除信号
    order_changed = pyqtSignal()      # 顺序改变信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.images = []  # type: List[Dict]
        self.setup_ui()
        self.setup_context_menu()
        self.setup_drag_drop()

    def setup_ui(self):
        """设置界面"""
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(QPixmap(100, 100).size())
        self.setSpacing(10)
        self.setResizeMode(QListWidget.Adjust)
        self.setWrapping(True)
        self.setSelectionMode(QListWidget.SingleSelection)

        # 连接信号
        self.currentRowChanged.connect(self.on_row_changed)

    def setup_context_menu(self):
        """设置右键菜单"""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def setup_drag_drop(self):
        """设置拖拽功能"""
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QListWidget.InternalMove)

    def add_image(self, image_data):
        # type: (Dict) -> None
        """添加图片到列表"""
        self.images.append(image_data)

        item = QListWidgetItem()
        item.setText(image_data['filename'])
        item.setData(Qt.UserRole, len(self.images) - 1)

        thumbnail = image_data.get('thumbnail')
        if thumbnail is not None:
            if isinstance(thumbnail, Image.Image):
                # Convert PIL Image to QPixmap
                if thumbnail.mode == 'RGB':
                    qimg = QImage(thumbnail.tobytes(), thumbnail.width, thumbnail.height, QImage.Format_RGB888)
                elif thumbnail.mode == 'RGBA':
                    qimg = QImage(thumbnail.tobytes(), thumbnail.width, thumbnail.height, QImage.Format_RGBA8888)
                else:
                    thumbnail = thumbnail.convert('RGB')
                    qimg = QImage(thumbnail.tobytes(), thumbnail.width, thumbnail.height, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)
                item.setIcon(QIcon(pixmap))
            else:
                item.setIcon(QIcon(thumbnail))

        self.addItem(item)

    def remove_image(self, index):
        # type: (int) -> None
        """删除指定位置的图片"""
        if 0 <= index < len(self.images):
            self.images.pop(index)
            self.takeItem(index)
            self.update_indices()

    def update_indices(self):
        """更新所有项目的索引数据"""
        for i in range(self.count()):
            item = self.item(i)
            item.setData(Qt.UserRole, i)

    def get_image_count(self):
        # type: () -> int
        """获取图片数量"""
        return len(self.images)

    def clear_images(self):
        """清空图片列表"""
        self.images.clear()
        self.clear()

    def get_images(self):
        # type: () -> List[Dict]
        """获取所有图片数据"""
        return self.images.copy()

    def on_row_changed(self, row):
        # type: (int) -> None
        """行改变事件"""
        if 0 <= row < len(self.images):
            self.image_selected.emit(row)

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.itemAt(position)
        if item is None:
            return

        menu = QMenu(self)

        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_selected_image())

        move_up_action = QAction("上移", self)
        move_up_action.triggered.connect(lambda: self.move_image_up())

        move_down_action = QAction("下移", self)
        move_down_action.triggered.connect(lambda: self.move_image_down())

        menu.addAction(delete_action)
        menu.addAction(move_up_action)
        menu.addAction(move_down_action)

        menu.exec_(self.mapToGlobal(position))

    def delete_selected_image(self):
        """删除选中的图片"""
        current_row = self.currentRow()
        if current_row >= 0:
            self.remove_image(current_row)
            self.image_deleted.emit(current_row)

    def move_image_up(self):
        """上移图片"""
        current_row = self.currentRow()
        if current_row > 0:
            self.images[current_row], self.images[current_row - 1] = \
                self.images[current_row - 1], self.images[current_row]

            item = self.takeItem(current_row)
            self.insertItem(current_row - 1, item)
            self.setCurrentRow(current_row - 1)
            self.order_changed.emit()

    def move_image_down(self):
        """下移图片"""
        current_row = self.currentRow()
        if current_row < self.count() - 1:
            self.images[current_row], self.images[current_row + 1] = \
                self.images[current_row + 1], self.images[current_row]

            item = self.takeItem(current_row)
            self.insertItem(current_row + 1, item)
            self.setCurrentRow(current_row + 1)
            self.order_changed.emit()
