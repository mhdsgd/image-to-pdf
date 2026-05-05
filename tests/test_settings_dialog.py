# tests/test_settings_dialog.py
import pytest
from PyQt5.QtWidgets import QApplication
from ui.settings_dialog import SettingsDialog

@pytest.fixture
def app():
    """创建QApplication实例"""
    return QApplication([])

def test_settings_dialog_creation(app):
    """测试创建设置对话框"""
    dialog = SettingsDialog()
    assert dialog is not None

def test_get_page_settings(app):
    """测试获取页面设置"""
    dialog = SettingsDialog()

    settings = dialog.get_page_settings()
    assert 'page_size' in settings
    assert 'orientation' in settings
    assert 'margin' in settings
    assert 'quality' in settings

def test_set_page_settings(app):
    """测试设置页面参数"""
    dialog = SettingsDialog()

    dialog.set_page_settings(
        page_size='Letter',
        orientation='landscape',
        margin=36,
        quality='high'
    )

    settings = dialog.get_page_settings()
    assert settings['page_size'] == 'Letter'
    assert settings['orientation'] == 'landscape'
    assert settings['margin'] == 36
    assert settings['quality'] == 'high'

def test_get_theme_settings(app):
    """测试获取主题设置"""
    dialog = SettingsDialog()

    theme = dialog.get_theme_settings()
    assert theme in ['light', 'dark']

def test_set_theme_settings(app):
    """测试设置主题"""
    dialog = SettingsDialog()

    dialog.set_theme_settings('dark')
    theme = dialog.get_theme_settings()
    assert theme == 'dark'
