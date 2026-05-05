import pytest
from pathlib import Path
from core.image_processor import ImageProcessor


def test_load_image_valid():
    """测试加载有效图片"""
    processor = ImageProcessor()
    # 创建测试图片
    from PIL import Image
    test_img = Image.new('RGB', (100, 100), color='red')
    test_path = Path("test_image.jpg")
    test_img.save(test_path)

    result = processor.load_image(test_path)
    assert result is not None
    assert result['path'] == test_path
    assert result['filename'] == "test_image.jpg"
    assert 'thumbnail' in result

    # 清理
    test_path.unlink()


def test_load_image_invalid():
    """测试加载无效图片"""
    processor = ImageProcessor()
    result = processor.load_image(Path("nonexistent.jpg"))
    assert result is None


def test_generate_thumbnail():
    """测试生成缩略图"""
    processor = ImageProcessor()
    from PIL import Image
    test_img = Image.new('RGB', (200, 200), color='blue')

    thumbnail = processor.generate_thumbnail(test_img)
    assert thumbnail.size == (100, 100)


def test_load_images_from_directory():
    """测试从目录加载多张图片"""
    processor = ImageProcessor()
    from PIL import Image

    # 创建测试目录和图片
    test_dir = Path("test_images")
    test_dir.mkdir(exist_ok=True)

    for i in range(3):
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_dir / f"image_{i}.jpg")

    images = processor.load_images_from_directory(test_dir)
    assert len(images) == 3

    # 清理
    import shutil
    shutil.rmtree(test_dir)
