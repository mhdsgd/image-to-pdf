# tests/test_preview.py
import pytest
from PyQt5.QtWidgets import QApplication
from ui.preview import PreviewWidget

@pytest.fixture
def app():
    """创建QApplication实例"""
    return QApplication([])

def test_preview_creation(app):
    """测试创建预览组件"""
    widget = PreviewWidget()
    assert widget is not None
    assert widget.current_page == 0
    assert widget.total_pages == 0
    assert widget.zoom_level == 1.0

def test_set_images(app):
    """测试设置图片列表"""
    widget = PreviewWidget()

    images = [
        {'image': None, 'filename': 'test1.jpg'},
        {'image': None, 'filename': 'test2.jpg'}
    ]

    widget.set_images(images)
    assert widget.total_pages == 2
    assert widget.current_page == 0

def test_navigate_pages(app):
    """测试页面导航"""
    widget = PreviewWidget()

    images = [
        {'image': None, 'filename': 'test1.jpg'},
        {'image': None, 'filename': 'test2.jpg'},
        {'image': None, 'filename': 'test3.jpg'}
    ]

    widget.set_images(images)

    # 测试下一页
    widget.next_page()
    assert widget.current_page == 1

    # 测试上一页
    widget.previous_page()
    assert widget.current_page == 0

    # 测试跳转到指定页
    widget.go_to_page(2)
    assert widget.current_page == 2

def test_zoom_controls(app):
    """测试缩放控制"""
    widget = PreviewWidget()

    # 测试放大
    widget.zoom_in()
    assert widget.zoom_level == 1.1

    # 测试缩小
    widget.zoom_out()
    assert widget.zoom_level == 1.0

    # 测试重置缩放
    widget.reset_zoom()
    assert widget.zoom_level == 1.0

def test_page_info(app):
    """测试获取页面信息"""
    widget = PreviewWidget()

    images = [
        {'image': None, 'filename': 'test1.jpg'},
        {'image': None, 'filename': 'test2.jpg'}
    ]

    widget.set_images(images)

    page_info = widget.get_page_info()
    assert page_info['current_page'] == 0
    assert page_info['total_pages'] == 2
    assert page_info['zoom_level'] == 1.0
