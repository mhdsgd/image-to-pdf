from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QMessageBox, QStatusBar,
                             QProgressBar, QSplitter)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication
from pathlib import Path
from typing import List, Tuple

from core.image_processor import SUPPORTED_ARCHIVE_FORMATS
from ui.image_list import ImageListWidget
from ui.preview import PreviewWidget
from ui.settings_dialog import SettingsDialog
from core.image_processor import ImageProcessor
from core.pdf_generator import PDFGenerator
from core.sorter import Sorter


class PDFWorkerThread(QThread):
    """后台线程：生成PDF"""
    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, pdf_generator, images, output_path, parent=None):
        super().__init__(parent)
        self.pdf_generator = pdf_generator
        self.images = images
        self.output_path = output_path

    def run(self):
        try:
            success, msg = self.pdf_generator.generate_pdf(
                self.images, self.output_path,
                progress_callback=lambda c, t: self.progress.emit(c, t)
            )
            self.finished.emit(success, msg)
        except Exception as e:
            self.finished.emit(False, str(e))


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片合并PDF工具")
        self.setMinimumSize(1200, 800)

        # 初始化核心组件
        self.image_processor = ImageProcessor()
        self.pdf_generator = PDFGenerator()
        self.sorter = Sorter()
        self.images = []

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """设置界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 使用 QSplitter 实现左右可拖拽分隔
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(3)

        # 左侧面板 - 图片列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 工具栏 - 导入
        toolbar_layout = QHBoxLayout()
        self.import_button = QPushButton("导入图片")
        toolbar_layout.addWidget(self.import_button)

        self.archive_button = QPushButton("导入压缩包")
        toolbar_layout.addWidget(self.archive_button)

        self.clear_button = QPushButton("清空列表")
        toolbar_layout.addWidget(self.clear_button)

        self.thumbnail_toggle_button = QPushButton("仅名称")
        self.thumbnail_toggle_button.setToolTip("切换缩略图/仅名称显示模式")
        self.thumbnail_toggle_button.setCheckable(True)
        toolbar_layout.addWidget(self.thumbnail_toggle_button)

        left_layout.addLayout(toolbar_layout)

        # 工具栏 - 排序/删除
        sort_layout = QHBoxLayout()
        self.swap_button = QPushButton("交换位置")
        self.swap_button.setToolTip("选中2张图片后点击交换")
        sort_layout.addWidget(self.swap_button)

        self.front_button = QPushButton("置顶")
        self.front_button.setToolTip("选中图片后移到列表最前")
        sort_layout.addWidget(self.front_button)

        self.end_button = QPushButton("置底")
        self.end_button.setToolTip("选中图片后移到列表最后")
        sort_layout.addWidget(self.end_button)

        self.delete_selected_button = QPushButton("删除选中")
        self.delete_selected_button.setToolTip("删除选中的图片")
        sort_layout.addWidget(self.delete_selected_button)

        left_layout.addLayout(sort_layout)

        # 图片列表
        self.image_list = ImageListWidget()
        left_layout.addWidget(self.image_list)

        # 右侧面板 - 预览和控制
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 预览组件
        self.preview = PreviewWidget()
        right_layout.addWidget(self.preview)

        # 生成按钮
        self.generate_button = QPushButton("生成PDF")
        right_layout.addWidget(self.generate_button)

        # 设置按钮
        self.settings_button = QPushButton("设置")
        right_layout.addWidget(self.settings_button)

        # 进度条（默认隐藏）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        # 添加到 splitter，左侧固定窄列，右侧占剩余空间
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        left_panel.setMinimumWidth(150)
        main_layout.addWidget(splitter)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def setup_connections(self):
        """设置信号连接"""
        self.import_button.clicked.connect(self.on_import_clicked)
        self.archive_button.clicked.connect(self.on_archive_import_clicked)
        self.clear_button.clicked.connect(self.on_clear_clicked)
        self.generate_button.clicked.connect(self.on_generate_clicked)
        self.settings_button.clicked.connect(self.on_settings_clicked)

        self.swap_button.clicked.connect(self.on_swap_clicked)
        self.front_button.clicked.connect(self.on_move_front_clicked)
        self.end_button.clicked.connect(self.on_move_end_clicked)
        self.delete_selected_button.clicked.connect(self.on_delete_selected_clicked)
        self.thumbnail_toggle_button.clicked.connect(self.on_thumbnail_toggle)

        self.image_list.image_selected.connect(self.on_image_selected)
        self.image_list.image_deleted.connect(self.on_image_deleted)
        self.image_list.order_changed.connect(self.on_order_changed)

    def on_import_clicked(self):
        """导入按钮点击事件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "",
            "图片文件 (*.jpg *.jpeg *.png *.webp)"
        )

        if file_paths:
            if len(file_paths) > 1000:
                QMessageBox.warning(self, "警告", "一次最多导入1000张图片，当前选择了{}张".format(len(file_paths)))
                return
            total = len(self.images) + len(file_paths)
            if total > 1000:
                QMessageBox.warning(self, "警告", "导入后总数将超过1000张（当前{}张 + 新增{}张），请减少选择数量".format(len(self.images), len(file_paths)))
                return
            paths = [Path(fp) for fp in file_paths]
            self.import_images(paths)

    def import_images(self, image_paths):
        # type: (List[Path]) -> None
        """导入图片"""
        total = len(image_paths)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.generate_button.setEnabled(False)
        self.import_button.setEnabled(False)
        self.archive_button.setEnabled(False)

        def on_progress(current, total_count):
            self.progress_bar.setValue(current)
            self.status_bar.showMessage("正在导入图片... {}/{}".format(current, total_count))
            QApplication.processEvents()

        try:
            new_images = self.image_processor.load_images_from_files(
                image_paths, progress_callback=on_progress
            )
        finally:
            self.progress_bar.setVisible(False)
            self.generate_button.setEnabled(True)
            self.import_button.setEnabled(True)
            self.archive_button.setEnabled(True)

        if new_images:
            self.images.extend(new_images)

            for img_data in new_images:
                self.image_list.add_image(img_data)

            self.update_preview()
            self.status_bar.showMessage("已导入 {} 张图片".format(len(new_images)))

    def on_archive_import_clicked(self):
        """导入压缩包按钮点击事件"""
        # 构建文件过滤器
        archive_filter = "压缩包 ({})".format(" ".join("*" + ext for ext in SUPPORTED_ARCHIVE_FORMATS))
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择压缩包", "",
            archive_filter
        )

        if file_path:
            self.import_from_archive(Path(file_path))

    def import_from_archive(self, archive_path):
        # type: (Path) -> None
        """从压缩包导入图片"""
        import io
        import sys

        self.status_bar.showMessage("正在解压: {}".format(archive_path.name))
        self.progress_bar.setMaximum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.generate_button.setEnabled(False)
        self.import_button.setEnabled(False)
        self.archive_button.setEnabled(False)

        def on_progress(current, total_count):
            if self.progress_bar.maximum() != total_count:
                self.progress_bar.setMaximum(total_count)
            self.progress_bar.setValue(current)
            self.status_bar.showMessage("正在导入图片... {}/{}".format(current, total_count))
            QApplication.processEvents()

        # 捕获 print 输出用于调试
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        try:
            new_images = self.image_processor.load_images_from_archive(
                archive_path, progress_callback=on_progress
            )
        except MemoryError:
            sys.stdout = old_stdout
            self.progress_bar.setVisible(False)
            self.generate_button.setEnabled(True)
            self.import_button.setEnabled(True)
            self.archive_button.setEnabled(True)
            QMessageBox.critical(self, "错误", "内存不足，压缩包中的图片过多或分辨率过高，请减少图片数量或降低分辨率后重试")
            return
        finally:
            sys.stdout = old_stdout
            debug_output = buffer.getvalue()
            self.progress_bar.setVisible(False)
            self.generate_button.setEnabled(True)
            self.import_button.setEnabled(True)
            self.archive_button.setEnabled(True)

        if new_images:
            if len(new_images) > 1000:
                QMessageBox.warning(self, "警告", "压缩包中图片数量超过1000张（共{}张），请减少图片数量后重试".format(len(new_images)))
                return
            total = len(self.images) + len(new_images)
            if total > 1000:
                QMessageBox.warning(self, "警告", "导入后总数将超过1000张（当前{}张 + 压缩包{}张），请先清空列表或减少压缩包内图片数量".format(len(self.images), len(new_images)))
                return
            self.images.extend(new_images)

            for img_data in new_images:
                self.image_list.add_image(img_data)

            self.update_preview()
            self.status_bar.showMessage("从压缩包导入了 {} 张图片".format(len(new_images)))
        else:
            self.status_bar.showMessage("压缩包中未找到图片")
            detail = "压缩包中未找到支持的图片格式\n\n调试信息:\n{}".format(debug_output) if debug_output else "压缩包中未找到支持的图片格式"
            QMessageBox.warning(self, "警告", detail)

    def on_clear_clicked(self):
        """清空按钮点击事件"""
        for img_data in self.images:
            ImageProcessor.close_image(img_data)
        self.images.clear()
        self.image_list.clear_images()
        self.preview.set_images([])
        self.status_bar.showMessage("已清空图片列表")

    def on_generate_clicked(self):
        """生成按钮点击事件"""
        if not self.images:
            QMessageBox.warning(self, "警告", "请先导入图片")
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self, "保存PDF", "",
            "PDF文件 (*.pdf)"
        )

        if output_path:
            if not output_path.lower().endswith('.pdf'):
                output_path += '.pdf'
            self._start_pdf_generation(Path(output_path))

    def _start_pdf_generation(self, output_path):
        # type: (Path) -> None
        """启动后台线程生成PDF"""
        import math

        # 禁用左侧图片列表区域所有操作
        for btn in (self.import_button, self.archive_button, self.clear_button,
                    self.thumbnail_toggle_button, self.swap_button,
                    self.front_button, self.end_button, self.delete_selected_button):
            btn.setEnabled(False)
        self.image_list.setEnabled(False)
        self.generate_button.setEnabled(False)

        # 并行模式按chunk计数，串行模式按图片计数
        img_count = len(self.images)
        if img_count > self.pdf_generator.CHUNK_SIZE:
            progress_max = math.ceil(img_count / self.pdf_generator.CHUNK_SIZE)
        else:
            progress_max = img_count
        self.progress_bar.setMaximum(progress_max)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_bar.showMessage("正在生成 PDF...")

        self._pdf_worker = PDFWorkerThread(
            self.pdf_generator, self.images, output_path
        )
        self._pdf_worker.progress.connect(self._on_pdf_progress)
        self._pdf_worker.finished.connect(
            lambda success, msg: self._on_pdf_finished(success, msg, str(output_path))
        )
        self._pdf_worker.start()

    def _on_pdf_progress(self, current, total):
        """PDF生成进度回调（主线程）"""
        self.progress_bar.setValue(current)
        self.status_bar.showMessage("正在生成 PDF... {}/{}".format(current, total))

    def _on_pdf_finished(self, success, message, output_path):
        """PDF生成完成回调（主线程）"""
        self.progress_bar.setVisible(False)
        for btn in (self.import_button, self.archive_button, self.clear_button,
                    self.thumbnail_toggle_button, self.swap_button,
                    self.front_button, self.end_button, self.delete_selected_button):
            btn.setEnabled(True)
        self.image_list.setEnabled(True)
        self.generate_button.setEnabled(True)

        if success:
            if message:
                QMessageBox.warning(self, "部分完成", "PDF已生成，但有图片处理失败：\n{}".format(message))
            else:
                QMessageBox.information(self, "成功", "PDF已生成：{}".format(output_path))
        else:
            QMessageBox.critical(self, "错误", "PDF生成失败：\n{}".format(message))

        self.status_bar.showMessage("共 {} 张图片".format(len(self.images)))
        self._pdf_worker = None

    def generate_pdf(self, output_path):
        # type: (Path) -> Tuple[bool, str]
        """同步生成PDF（供测试调用，UI应使用_start_pdf_generation）"""
        return self.pdf_generator.generate_pdf(self.images, output_path)

    def on_settings_clicked(self):
        """设置按钮点击事件"""
        dialog = SettingsDialog(self)

        # 设置当前值
        dialog.set_page_settings(
            page_size=self.pdf_generator.page_size,
            orientation=self.pdf_generator.orientation,
            margin=self.pdf_generator.margin,
            quality=self.pdf_generator.quality
        )

        if dialog.exec_() == SettingsDialog.Accepted:
            settings = dialog.get_page_settings()
            self.pdf_generator.set_page_settings(
                page_size=settings['page_size'],
                orientation=settings['orientation'],
                margin=settings['margin'],
                quality=settings['quality']
            )

            theme = dialog.get_theme_settings()
            self.apply_theme(theme)

            self.status_bar.showMessage("设置已更新")

    def apply_theme(self, theme):
        # type: (str) -> None
        """应用主题"""
        try:
            base_dir = Path(__file__).parent.parent
            style_file = base_dir / "resources" / "styles" / "{}.qss".format(theme)
            with open(str(style_file), 'r', encoding='utf-8') as f:
                style = f.read()
                self.setStyleSheet(style)
        except (FileNotFoundError, PermissionError, OSError):
            self.status_bar.showMessage("主题文件不存在: {}".format(style_file))
            print("主题文件不存在: {}".format(style_file))

    def on_image_selected(self, index):
        # type: (int) -> None
        """图片选中事件"""
        if 0 <= index < len(self.images):
            self.preview.go_to_page(index)

    def on_image_deleted(self, index):
        # type: (int) -> None
        """图片删除事件"""
        if 0 <= index < len(self.images):
            removed = self.images.pop(index)
            ImageProcessor.close_image(removed)
            self.update_preview()

    def on_order_changed(self):
        """顺序改变事件"""
        # 更新内部图片列表顺序
        self.images = self.image_list.get_images()
        self.update_preview()

    def on_swap_clicked(self):
        """交换两张图片位置"""
        rows = self.image_list.get_selected_rows()
        if len(rows) != 2:
            QMessageBox.warning(self, "提示", "请选中恰好2张图片再交换")
            return
        self.image_list.swap_images(rows[0], rows[1])
        self.images = self.image_list.get_images()
        self.update_preview()

    def on_move_front_clicked(self):
        """选中图片置顶"""
        rows = self.image_list.get_selected_rows()
        if not rows:
            QMessageBox.warning(self, "提示", "请先选择至少1张图片")
            return
        self.image_list.move_to_front(rows)
        self.images = self.image_list.get_images()
        self.update_preview()

    def on_move_end_clicked(self):
        """选中图片置底"""
        rows = self.image_list.get_selected_rows()
        if not rows:
            QMessageBox.warning(self, "提示", "请先选择至少1张图片")
            return
        self.image_list.move_to_end(rows)
        self.images = self.image_list.get_images()
        self.update_preview()

    def on_delete_selected_clicked(self):
        """删除选中的图片"""
        rows = self.image_list.get_selected_rows()
        if not rows:
            QMessageBox.warning(self, "提示", "请先选择至少1张图片")
            return

        count = len(rows)
        self.status_bar.showMessage("正在移除选中图片... (共{}张)".format(count))
        QApplication.processEvents()

        # 从后往前删除，避免索引偏移
        for i in sorted(rows, reverse=True):
            removed = self.images.pop(i)
            ImageProcessor.close_image(removed)

        self.image_list.remove_images_by_rows(rows)
        self.update_preview()
        self.status_bar.showMessage("已移除 {} 张图片，剩余 {} 张".format(count, len(self.images)))

    def on_thumbnail_toggle(self, checked):
        """切换缩略图/仅名称显示"""
        self.image_list.set_show_thumbnail(not checked)
        if checked:
            self.thumbnail_toggle_button.setText("缩略图")
        else:
            self.thumbnail_toggle_button.setText("仅名称")

    def closeEvent(self, event):
        """窗口关闭时释放图片资源"""
        for img_data in self.images:
            ImageProcessor.close_image(img_data)
        self.images.clear()
        super().closeEvent(event)

    def update_preview(self):
        """更新预览"""
        self.preview.set_images(self.images)
        self.status_bar.showMessage("共 {} 张图片".format(len(self.images)))
