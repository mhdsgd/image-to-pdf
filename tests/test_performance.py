# tests/test_performance.py
import pytest
import time
import shutil
from pathlib import Path
from PIL import Image
from core.image_processor import ImageProcessor
from core.pdf_generator import PDFGenerator
from core.sorter import Sorter


@pytest.fixture
def test_images_dir(tmp_path):
    """创建测试图片目录"""
    return tmp_path


def create_test_images(directory, count, size=(200, 200)):
    """批量创建测试图片"""
    for i in range(count):
        img = Image.new('RGB', size, color=(i % 256, 100, 100))
        img.save(directory / "image_{:04d}.jpg".format(i))
    return sorted(directory.glob("*.jpg"))


def test_load_100_images(test_images_dir):
    """测试加载100张图片的性能"""
    processor = ImageProcessor()
    paths = create_test_images(test_images_dir, 100)

    start = time.time()
    images = processor.load_images_from_files(paths)
    elapsed = time.time() - start

    assert len(images) == 100
    assert elapsed < 30, "加载100张图片耗时过长: {:.2f}秒".format(elapsed)
    print("加载100张图片: {:.2f}秒".format(elapsed))


def test_load_500_images(test_images_dir):
    """测试加载500张图片的性能"""
    processor = ImageProcessor()
    paths = create_test_images(test_images_dir, 500)

    start = time.time()
    images = processor.load_images_from_files(paths)
    elapsed = time.time() - start

    assert len(images) == 500
    assert elapsed < 60, "加载500张图片耗时过长: {:.2f}秒".format(elapsed)
    print("加载500张图片: {:.2f}秒".format(elapsed))


def test_generate_pdf_100_images(test_images_dir):
    """测试生成100张图片PDF的性能"""
    processor = ImageProcessor()
    generator = PDFGenerator()
    paths = create_test_images(test_images_dir, 100)
    images = processor.load_images_from_files(paths)

    output_path = test_images_dir / "output_100.pdf"
    start = time.time()
    result = generator.generate_pdf(images, output_path)
    elapsed = time.time() - start

    assert result[0] is True
    assert output_path.exists()
    assert elapsed < 60, "生成100张图片PDF耗时过长: {:.2f}秒".format(elapsed)
    print("生成100张图片PDF: {:.2f}秒".format(elapsed))


def test_generate_pdf_500_images(test_images_dir):
    """测试生成500张图片PDF的性能"""
    processor = ImageProcessor()
    generator = PDFGenerator()
    paths = create_test_images(test_images_dir, 500)
    images = processor.load_images_from_files(paths)

    output_path = test_images_dir / "output_500.pdf"
    start = time.time()
    result = generator.generate_pdf(images, output_path)
    elapsed = time.time() - start

    assert result[0] is True
    assert output_path.exists()
    assert elapsed < 120, "生成500张图片PDF耗时过长: {:.2f}秒".format(elapsed)
    print("生成500张图片PDF: {:.2f}秒".format(elapsed))


def test_sort_100_images():
    """测试排序100张图片的性能"""
    sorter = Sorter()
    images = [{'filename': 'image_{:04d}.jpg'.format(i)} for i in range(100)]

    start = time.time()
    sorted_images = sorter.sort_by_filename(images)
    elapsed = time.time() - start

    assert len(sorted_images) == 100
    assert elapsed < 1, "排序100张图片耗时过长: {:.2f}秒".format(elapsed)
    print("排序100张图片: {:.4f}秒".format(elapsed))


def test_sort_1000_images():
    """测试排序1000张图片的性能"""
    sorter = Sorter()
    images = [{'filename': 'image_{:04d}.jpg'.format(i)} for i in range(1000)]

    start = time.time()
    sorted_images = sorter.sort_by_filename(images)
    elapsed = time.time() - start

    assert len(sorted_images) == 1000
    assert elapsed < 1, "排序1000张图片耗时过长: {:.2f}秒".format(elapsed)
    print("排序1000张图片: {:.4f}秒".format(elapsed))


def test_move_image_performance():
    """测试移动图片操作的性能"""
    sorter = Sorter()
    images = [{'filename': 'image_{:04d}.jpg'.format(i)} for i in range(1000)]

    start = time.time()
    for i in range(100):
        images = sorter.move_image(images, i, 999 - i)
    elapsed = time.time() - start

    assert len(images) == 1000
    assert elapsed < 1, "移动图片操作耗时过长: {:.2f}秒".format(elapsed)
    print("移动100次图片(1000张列表): {:.4f}秒".format(elapsed))
