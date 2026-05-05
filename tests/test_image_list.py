# tests/test_image_list.py
import pytest
from PyQt5.QtWidgets import QApplication
from ui.image_list import ImageListWidget

@pytest.fixture
def app():
    """创建QApplication实例"""
    return QApplication([])

def test_image_list_creation(app):
    """测试创建图片列表组件"""
    widget = ImageListWidget()
    assert widget is not None
    assert widget.count() == 0

def test_add_image(app):
    """测试添加图片"""
    widget = ImageListWidget()

    image_data = {
        'path': 'test.jpg',
        'filename': 'test.jpg',
        'thumbnail': None
    }

    widget.add_image(image_data)
    assert widget.count() == 1

def test_remove_image(app):
    """测试删除图片"""
    widget = ImageListWidget()

    image_data = {
        'path': 'test.jpg',
        'filename': 'test.jpg',
        'thumbnail': None
    }

    widget.add_image(image_data)
    widget.remove_image(0)
    assert widget.count() == 0

def test_get_image_count(app):
    """测试获取图片数量"""
    widget = ImageListWidget()

    for i in range(5):
        image_data = {
            'path': f'test_{i}.jpg',
            'filename': f'test_{i}.jpg',
            'thumbnail': None
        }
        widget.add_image(image_data)

    assert widget.get_image_count() == 5

def test_clear_images(app):
    """测试清空图片列表"""
    widget = ImageListWidget()

    for i in range(5):
        image_data = {
            'path': f'test_{i}.jpg',
            'filename': f'test_{i}.jpg',
            'thumbnail': None
        }
        widget.add_image(image_data)

    widget.clear_images()
    assert widget.count() == 0
