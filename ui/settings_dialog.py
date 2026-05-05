# ui/settings_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QSpinBox, QPushButton, QGroupBox)
from PyQt5.QtCore import Qt

class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)

        # 页面设置组
        page_group = QGroupBox("页面设置")
        page_layout = QVBoxLayout(page_group)

        # 页面大小
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("页面大小:"))
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["A4", "Letter"])
        size_layout.addWidget(self.page_size_combo)
        page_layout.addLayout(size_layout)

        # 页面方向
        orientation_layout = QHBoxLayout()
        orientation_layout.addWidget(QLabel("页面方向:"))
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItems(["portrait", "landscape"])
        orientation_layout.addWidget(self.orientation_combo)
        page_layout.addLayout(orientation_layout)

        # 页边距
        margin_layout = QHBoxLayout()
        margin_layout.addWidget(QLabel("页边距 (点):"))
        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 200)
        self.margin_spin.setValue(72)
        margin_layout.addWidget(self.margin_spin)
        page_layout.addLayout(margin_layout)

        # 压缩质量
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("压缩质量:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["original", "high", "medium", "low"])
        quality_layout.addWidget(self.quality_combo)
        page_layout.addLayout(quality_layout)

        layout.addWidget(page_group)

        # 主题设置组
        theme_group = QGroupBox("主题设置")
        theme_layout = QVBoxLayout(theme_group)

        theme_select_layout = QHBoxLayout()
        theme_select_layout.addWidget(QLabel("界面主题:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        theme_select_layout.addWidget(self.theme_combo)
        theme_layout.addLayout(theme_select_layout)

        layout.addWidget(theme_group)

        # 按钮
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def get_page_settings(self):
        # type: () -> dict
        """获取页面设置"""
        return {
            'page_size': self.page_size_combo.currentText(),
            'orientation': self.orientation_combo.currentText(),
            'margin': self.margin_spin.value(),
            'quality': self.quality_combo.currentText()
        }

    def set_page_settings(self, page_size=None, orientation=None,
                         margin=None, quality=None):
        # type: (str, str, int, str) -> None
        """设置页面参数"""
        if page_size is not None:
            index = self.page_size_combo.findText(page_size)
            if index >= 0:
                self.page_size_combo.setCurrentIndex(index)

        if orientation is not None:
            index = self.orientation_combo.findText(orientation)
            if index >= 0:
                self.orientation_combo.setCurrentIndex(index)

        if margin is not None:
            self.margin_spin.setValue(margin)

        if quality is not None:
            index = self.quality_combo.findText(quality)
            if index >= 0:
                self.quality_combo.setCurrentIndex(index)

    def get_theme_settings(self):
        # type: () -> str
        """获取主题设置"""
        return self.theme_combo.currentText()

    def set_theme_settings(self, theme):
        # type: (str) -> None
        """设置主题"""
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
