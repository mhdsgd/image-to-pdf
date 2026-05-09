from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QMessageBox, QStatusBar,
                             QProgressBar)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from pathlib import Path
from typing import List

from core.image_processor import SUPPORTED_ARCHIVE_FORMATS
from ui.image_list import ImageListWidget
from ui.preview import PreviewWidget
from ui.settings_dialog import SettingsDialog
from core.image_processor import ImageProcessor
from core.pdf_generator import PDFGenerator
from core.sorter import Sorter


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

        main_layout = QHBoxLayout(central_widget)

        # 左侧面板 - 图片列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # 工具栏
        toolbar_layout = QHBoxLayout()
        self.import_button = QPushButton("导入图片")
        toolbar_layout.addWidget(self.import_button)

        self.archive_button = QPushButton("导入压缩包")
        toolbar_layout.addWidget(self.archive_button)

        self.clear_button = QPushButton("清空列表")
        toolbar_layout.addWidget(self.clear_button)

        left_layout.addLayout(toolbar_layout)

        # 图片列表
        self.image_list = ImageListWidget()
        left_layout.addWidget(self.image_list)

        main_layout.addWidget(left_panel)

        # 右侧面板 - 预览和控制
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

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

        main_layout.addWidget(right_panel)

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

        self.image_list.image_selected.connect(self.on_image_selected)
        self.image_list.image_deleted.connect(self.on_image_deleted)
        self.image_list.order_changed.connect(self.on_order_changed)

    def on_import_clicked(self):
        """导入按钮点击事件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "",
            "图片文件 (*.jpg *.jpeg *.png *.webp)",
            options=QFileDialog.DontUseNativeDialog
        )

        if file_paths:
            paths = [Path(fp) for fp in file_paths]
            self.import_images(paths)

    def import_images(self, image_paths):
        # type: (List[Path]) -> None
        """导入图片"""
        new_images = self.image_processor.load_images_from_files(image_paths)

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
            archive_filter,
            options=QFileDialog.DontUseNativeDialog
        )

        if file_path:
            self.import_from_archive(Path(file_path))

    def import_from_archive(self, archive_path):
        # type: (Path) -> None
        """从压缩包导入图片"""
        import io
        import sys

        self.status_bar.showMessage("正在解压: {}".format(archive_path.name))

        # 捕获 print 输出用于调试
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()

        new_images = self.image_processor.load_images_from_archive(archive_path)

        sys.stdout = old_stdout
        debug_output = buffer.getvalue()

        if new_images:
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
            "PDF文件 (*.pdf)",
            options=QFileDialog.DontUseNativeDialog
        )

        if output_path:
            if not output_path.lower().endswith('.pdf'):
                output_path += '.pdf'
            result = self.generate_pdf(Path(output_path))
            if result:
                QMessageBox.information(self, "成功", "PDF已生成：{}".format(output_path))
            else:
                QMessageBox.critical(self, "错误", "PDF生成失败")

    def generate_pdf(self, output_path):
        # type: (Path) -> bool
        """生成PDF"""
        def on_progress(current, total):
            self.progress_bar.setValue(current)
            self.status_bar.showMessage("正在生成 PDF... {}/{}".format(current, total))
            QApplication.processEvents()

        self.progress_bar.setMaximum(len(self.images))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        result = self.pdf_generator.generate_pdf(
            self.images, output_path,
            progress_callback=on_progress
        )

        self.progress_bar.setVisible(False)
        return result

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
        except FileNotFoundError:
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
            self.images.pop(index)
            self.update_preview()

    def on_order_changed(self):
        """顺序改变事件"""
        # 更新内部图片列表顺序
        self.images = self.image_list.get_images()
        self.update_preview()

    def update_preview(self):
        """更新预览"""
        self.preview.set_images(self.images)
        self.status_bar.showMessage("共 {} 张图片".format(len(self.images)))
