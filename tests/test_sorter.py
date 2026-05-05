import pytest
from core.sorter import Sorter


def test_sort_by_filename():
    """测试按文件名排序"""
    sorter = Sorter()

    images = [
        {'filename': 'image_3.jpg'},
        {'filename': 'image_1.jpg'},
        {'filename': 'image_2.jpg'}
    ]

    sorted_images = sorter.sort_by_filename(images)
    assert sorted_images[0]['filename'] == 'image_1.jpg'
    assert sorted_images[1]['filename'] == 'image_2.jpg'
    assert sorted_images[2]['filename'] == 'image_3.jpg'


def test_move_image_up():
    """测试上移图片"""
    sorter = Sorter()

    images = [
        {'filename': 'image_1.jpg'},
        {'filename': 'image_2.jpg'},
        {'filename': 'image_3.jpg'}
    ]

    result = sorter.move_image(images, 1, 0)
    assert result[0]['filename'] == 'image_2.jpg'
    assert result[1]['filename'] == 'image_1.jpg'
    assert result[2]['filename'] == 'image_3.jpg'


def test_move_image_down():
    """测试下移图片"""
    sorter = Sorter()

    images = [
        {'filename': 'image_1.jpg'},
        {'filename': 'image_2.jpg'},
        {'filename': 'image_3.jpg'}
    ]

    result = sorter.move_image(images, 0, 2)
    assert result[0]['filename'] == 'image_2.jpg'
    assert result[1]['filename'] == 'image_3.jpg'
    assert result[2]['filename'] == 'image_1.jpg'


def test_swap_images():
    """测试交换图片位置"""
    sorter = Sorter()

    images = [
        {'filename': 'image_1.jpg'},
        {'filename': 'image_2.jpg'},
        {'filename': 'image_3.jpg'}
    ]

    result = sorter.swap_images(images, 0, 2)
    assert result[0]['filename'] == 'image_3.jpg'
    assert result[1]['filename'] == 'image_2.jpg'
    assert result[2]['filename'] == 'image_1.jpg'


def test_remove_image():
    """测试删除图片"""
    sorter = Sorter()

    images = [
        {'filename': 'image_1.jpg'},
        {'filename': 'image_2.jpg'},
        {'filename': 'image_3.jpg'}
    ]

    result = sorter.remove_image(images, 1)
    assert len(result) == 2
    assert result[0]['filename'] == 'image_1.jpg'
    assert result[1]['filename'] == 'image_3.jpg'
