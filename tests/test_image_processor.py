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


def test_load_image_from_bytes_jpg():
    """测试从字节加载 JPG 图片"""
    processor = ImageProcessor()
    from PIL import Image
    from io import BytesIO

    # 创建测试图片并转为字节
    test_img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    test_img.save(buffer, format='JPEG')
    data = buffer.getvalue()

    result = processor.load_image_from_bytes(data, "test.jpg")
    assert result is not None
    assert result['filename'] == "test.jpg"
    assert result['image'].size == (100, 100)
    assert 'thumbnail' in result


def test_load_image_from_bytes_png():
    """测试从字节加载 PNG 图片"""
    processor = ImageProcessor()
    from PIL import Image
    from io import BytesIO

    test_img = Image.new('RGBA', (100, 100), color='blue')
    buffer = BytesIO()
    test_img.save(buffer, format='PNG')
    data = buffer.getvalue()

    result = processor.load_image_from_bytes(data, "test.png")
    assert result is not None
    assert result['filename'] == "test.png"
    assert result['image'].size == (100, 100)


def test_load_image_from_bytes_invalid():
    """测试从字节加载无效数据"""
    processor = ImageProcessor()

    result = processor.load_image_from_bytes(b"not an image", "test.jpg")
    assert result is None


def test_load_images_from_zip():
    """测试从 zip 压缩包加载图片"""
    processor = ImageProcessor()
    from PIL import Image
    from io import BytesIO
    import zipfile

    # 创建包含图片的 zip 文件
    zip_path = Path("test_archive.zip")
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for i in range(3):
            img = Image.new('RGB', (100, 100), color='red')
            buffer = BytesIO()
            img.save(buffer, format='JPEG')
            zf.writestr(f"image_{i}.jpg", buffer.getvalue())

    images = processor.load_images_from_archive(zip_path)
    assert len(images) == 3
    # 验证自然排序
    assert images[0]['filename'] == "image_0.jpg"
    assert images[1]['filename'] == "image_1.jpg"
    assert images[2]['filename'] == "image_2.jpg"

    # 清理
    zip_path.unlink()


def test_load_images_from_zip_with_subdirectory():
    """测试从包含子目录的 zip 加载图片"""
    processor = ImageProcessor()
    from PIL import Image
    from io import BytesIO
    import zipfile

    zip_path = Path("test_archive_subdir.zip")
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # 在子目录中创建图片
        for i in range(2):
            img = Image.new('RGB', (100, 100), color='green')
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            zf.writestr(f"subfolder/image_{i}.png", buffer.getvalue())

    images = processor.load_images_from_archive(zip_path)
    assert len(images) == 2
    # 文件名应该是不含路径的
    assert images[0]['filename'] == "image_0.png"

    # 清理
    zip_path.unlink()


def test_load_images_from_zip_natural_sort():
    """测试 zip 中图片的自然排序"""
    processor = ImageProcessor()
    from PIL import Image
    from io import BytesIO
    import zipfile

    zip_path = Path("test_natural_sort.zip")
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # 创建故意乱序的文件名
        filenames = ["img10.jpg", "img2.jpg", "img1.jpg", "img20.jpg"]
        for name in filenames:
            img = Image.new('RGB', (50, 50), color='yellow')
            buffer = BytesIO()
            img.save(buffer, format='JPEG')
            zf.writestr(name, buffer.getvalue())

    images = processor.load_images_from_archive(zip_path)
    assert len(images) == 4
    # 自然排序: img1, img2, img10, img20
    assert images[0]['filename'] == "img1.jpg"
    assert images[1]['filename'] == "img2.jpg"
    assert images[2]['filename'] == "img10.jpg"
    assert images[3]['filename'] == "img20.jpg"

    # 清理
    zip_path.unlink()


def test_load_images_from_nonexistent_archive():
    """测试加载不存在的压缩包"""
    processor = ImageProcessor()

    images = processor.load_images_from_archive(Path("nonexistent.zip"))
    assert len(images) == 0
