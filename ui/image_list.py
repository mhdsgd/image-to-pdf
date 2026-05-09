# ui/image_list.py
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon, QImage
from typing import List, Dict
from PIL import Image


def pil_to_qpixmap(pil_img):
    """将 PIL Image 转为 QPixmap"""
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


class ImageListWidget(QListWidget):
    """图片列表组件"""

    # 信号
    image_selected = pyqtSignal(int)  # 图片选中信号
    image_deleted = pyqtSignal(int)   # 图片删除信号
    order_changed = pyqtSignal()      # 顺序改变信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.images = []  # type: List[Dict]
        self.show_thumbnail = True  # 是否显示缩略图
        self.setup_ui()
        self.setup_context_menu()

    def setup_ui(self):
        """设置界面"""
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(QPixmap(100, 100).size())
        self.setSpacing(10)
        self.setResizeMode(QListWidget.Adjust)
        self.setWrapping(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.setDragDropMode(QListWidget.NoDragDrop)  # 禁用拖拽，使用按钮排序

        # 连接信号
        self.currentRowChanged.connect(self.on_row_changed)

    def setup_context_menu(self):
        """设置右键菜单"""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def set_show_thumbnail(self, show):
        # type: (bool) -> None
        """切换缩略图/仅名称显示模式"""
        self.show_thumbnail = show
        if show:
            self.setViewMode(QListWidget.IconMode)
            self.setIconSize(QPixmap(100, 100).size())
            self.setSpacing(10)
            self.setWrapping(True)
        else:
            self.setViewMode(QListWidget.ListMode)
            self.setIconSize(QPixmap(0, 0).size())
            self.setSpacing(2)
            self.setWrapping(False)
        self._rebuild_list()

    def get_selected_rows(self):
        """获取所有选中项的行号，按升序排列"""
        return sorted([self.row(item) for item in self.selectedItems()])

    def swap_images(self, row1, row2):
        """交换两张图片的位置"""
        if row1 == row2:
            return
        self.images[row1], self.images[row2] = self.images[row2], self.images[row1]
        item1 = self.item(row1)
        item2 = self.item(row2)
        icon1, icon2 = item1.icon(), item2.icon()
        text1, text2 = item1.text(), item2.text()
        item1.setIcon(icon2)
        item1.setText(text2)
        item2.setIcon(icon1)
        item2.setText(text1)
        self.update_indices()
        self.order_changed.emit()

    def move_to_front(self, rows):
        """将选中的图片移到列表最前，保持相对顺序"""
        if not rows:
            return
        moved = [self.images[i] for i in rows]
        remaining = [self.images[i] for i in range(len(self.images)) if i not in rows]
        self.images = moved + remaining
        self._rebuild_list()
        self.order_changed.emit()

    def move_to_end(self, rows):
        """将选中的图片移到列表最后，保持相对顺序"""
        if not rows:
            return
        moved = [self.images[i] for i in rows]
        remaining = [self.images[i] for i in range(len(self.images)) if i not in rows]
        self.images = remaining + moved
        self._rebuild_list()
        self.order_changed.emit()

    def _rebuild_list(self):
        """根据 self.images 重建列表 UI"""
        self.clear()
        for i, img_data in enumerate(self.images):
            item = QListWidgetItem()
            item.setText(img_data['filename'])
            item.setData(Qt.UserRole, i)
            if self.show_thumbnail:
                thumbnail = img_data.get('thumbnail')
                if thumbnail is not None:
                    if isinstance(thumbnail, Image.Image):
                        pixmap = pil_to_qpixmap(thumbnail)
                        item.setIcon(QIcon(pixmap))
                    else:
                        item.setIcon(QIcon(thumbnail))
            self.addItem(item)

    def add_image(self, image_data):
        # type: (Dict) -> None
        """添加图片到列表"""
        self.images.append(image_data)

        item = QListWidgetItem()
        item.setText(image_data['filename'])
        item.setData(Qt.UserRole, len(self.images) - 1)

        if self.show_thumbnail:
            thumbnail = image_data.get('thumbnail')
            if thumbnail is not None:
                if isinstance(thumbnail, Image.Image):
                    pixmap = pil_to_qpixmap(thumbnail)
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

    def remove_images_by_rows(self, rows):
        """批量删除指定行号的图片（rows 应为升序）"""
        for i in sorted(rows, reverse=True):
            if 0 <= i < len(self.images):
                self.images.pop(i)
                self.takeItem(i)
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
            self.update_indices()
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
            self.update_indices()
            self.order_changed.emit()
