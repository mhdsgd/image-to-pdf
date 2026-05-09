# tests/test_error_handling.py
import pytest
import shutil
from pathlib import Path
from PIL import Image
from core.image_processor import ImageProcessor
from core.pdf_generator import PDFGenerator
from core.sorter import Sorter


def test_load_corrupted_image(tmp_path):
    """测试加载损坏的图片文件"""
    processor = ImageProcessor()

    # 创建一个损坏的图片文件（写入随机字节）
    corrupted_path = tmp_path / "corrupted.jpg"
    corrupted_path.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)

    result = processor.load_image(corrupted_path)
    assert result is None


def test_load_empty_file(tmp_path):
    """测试加载空文件"""
    processor = ImageProcessor()

    empty_path = tmp_path / "empty.jpg"
    empty_path.write_bytes(b'')

    result = processor.load_image(empty_path)
    assert result is None


def test_load_nonexistent_file():
    """测试加载不存在的文件"""
    processor = ImageProcessor()

    result = processor.load_image(Path("nonexistent_image.jpg"))
    assert result is None


def test_load_nonexistent_directory():
    """测试从不存在的目录加载图片"""
    processor = ImageProcessor()

    result = processor.load_images_from_directory(Path("nonexistent_directory"))
    assert result == []


def test_load_empty_directory(tmp_path):
    """测试从空目录加载图片"""
    processor = ImageProcessor()

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    result = processor.load_images_from_directory(empty_dir)
    assert result == []


def test_load_unsupported_formats(tmp_path):
    """测试加载不支持的文件格式"""
    processor = ImageProcessor()

    # 创建不支持格式的文件
    (tmp_path / "document.txt").write_text("not an image")
    (tmp_path / "data.json").write_text('{"key": "value"}')
    (tmp_path / "video.mp4").write_bytes(b'\x00' * 100)

    result = processor.load_images_from_directory(tmp_path)
    assert result == []


def test_generate_pdf_to_invalid_path():
    """测试生成PDF到无效路径"""
    generator = PDFGenerator()

    images = [_make_image_data((100, 100))]
    output_path = Path("/nonexistent_dir/output.pdf")

    success, msg = generator.generate_pdf(images, output_path)
    assert success is False
    assert len(msg) > 0


def test_generate_pdf_empty_images():
    """测试空图片列表生成PDF"""
    generator = PDFGenerator()

    output_path = Path("test_empty.pdf")
    success, msg = generator.generate_pdf([], output_path)

    # 空列表应成功创建空PDF
    assert success is True
    assert msg == ""
    assert output_path.exists()

    # 清理
    output_path.unlink()


def test_move_image_invalid_indices():
    """测试使用无效索引移动图片"""
    sorter = Sorter()

    images = [
        {'filename': 'a.jpg'},
        {'filename': 'b.jpg'},
        {'filename': 'c.jpg'}
    ]

    # 负索引
    result = sorter.move_image(images, -1, 0)
    assert result == images

    # 超出范围索引
    result = sorter.move_image(images, 0, 10)
    assert result == images

    # 目标负索引
    result = sorter.move_image(images, 0, -1)
    assert result == images


def test_swap_images_invalid_indices():
    """测试使用无效索引交换图片"""
    sorter = Sorter()

    images = [
        {'filename': 'a.jpg'},
        {'filename': 'b.jpg'},
    ]

    # 负索引
    result = sorter.swap_images(images, -1, 0)
    assert result == images

    # 超出范围索引
    result = sorter.swap_images(images, 0, 10)
    assert result == images


def test_remove_image_invalid_index():
    """测试使用无效索引删除图片"""
    sorter = Sorter()

    images = [
        {'filename': 'a.jpg'},
        {'filename': 'b.jpg'},
    ]

    # 负索引
    result = sorter.remove_image(images, -1)
    assert result == images

    # 超出范围索引
    result = sorter.remove_image(images, 10)
    assert result == images


def _make_image_data(size, filename='test.jpg'):
    """创建测试用图片数据字典（使用 raw_data）"""
    from io import BytesIO
    buf = BytesIO()
    Image.new('RGB', size).save(buf, format='JPEG')
    return {'raw_data': buf.getvalue(), 'filename': filename}


def test_generate_pdf_with_different_qualities(tmp_path):
    """测试不同质量设置生成PDF"""
    generator = PDFGenerator()

    images = [_make_image_data((2000, 2000))]

    for quality in ['original', 'high', 'medium', 'low']:
        output_path = tmp_path / "test_{}.pdf".format(quality)
        success, msg = generator.generate_pdf(images, output_path, quality=quality)
        assert success is True, "质量设置 '{}' 生成PDF失败: {}".format(quality, msg)
        assert output_path.exists()


def test_generate_pdf_with_page_settings(tmp_path):
    """测试不同页面设置生成PDF"""
    generator = PDFGenerator()

    images = [_make_image_data((200, 200))]

    # 测试A4竖向
    generator.set_page_settings(page_size='A4', orientation='portrait')
    output_path = tmp_path / "a4_portrait.pdf"
    success, _ = generator.generate_pdf(images, output_path)
    assert success is True

    # 测试A4横向
    generator.set_page_settings(page_size='A4', orientation='landscape')
    output_path = tmp_path / "a4_landscape.pdf"
    success, _ = generator.generate_pdf(images, output_path)
    assert success is True

    # 测试Letter竖向
    generator.set_page_settings(page_size='Letter', orientation='portrait')
    output_path = tmp_path / "letter_portrait.pdf"
    success, _ = generator.generate_pdf(images, output_path)
    assert success is True

    # 测试Letter横向
    generator.set_page_settings(page_size='Letter', orientation='landscape')
    output_path = tmp_path / "letter_landscape.pdf"
    success, _ = generator.generate_pdf(images, output_path)
    assert success is True


def test_image_with_mode_conversion(tmp_path):
    """测试不同颜色模式的图片处理"""
    processor = ImageProcessor()

    # RGBA模式
    img_rgba = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
    img_rgba.save(tmp_path / "rgba.png")
    result = processor.load_image(tmp_path / "rgba.png")
    assert result is not None

    # L模式（灰度）
    img_l = Image.new('L', (100, 100), color=128)
    img_l.save(tmp_path / "grayscale.png")
    result = processor.load_image(tmp_path / "grayscale.png")
    assert result is not None


def test_load_images_from_files_mixed(tmp_path):
    """测试从混合文件列表加载（有效和无效混合）"""
    processor = ImageProcessor()

    # 创建一个有效图片
    valid_img = Image.new('RGB', (100, 100))
    valid_path = tmp_path / "valid.jpg"
    valid_img.save(valid_path)

    # 无效路径
    invalid_path = tmp_path / "invalid.jpg"

    # 混合加载
    paths = [valid_path, invalid_path]
    result = processor.load_images_from_files(paths)

    # 只有有效图片被加载
    assert len(result) == 1
    assert result[0]['filename'] == 'valid.jpg'


def test_generate_pdf_partial_failure(tmp_path):
    """测试部分图片失败时仍能生成PDF"""
    generator = PDFGenerator()

    # 混合有效和无效图片
    images = [
        _make_image_data((200, 200), 'valid1.jpg'),
        {'raw_data': b'not an image', 'filename': 'corrupt.jpg'},
        _make_image_data((200, 200), 'valid2.jpg'),
    ]

    output_path = tmp_path / "partial.pdf"
    success, msg = generator.generate_pdf(images, output_path)

    # 应部分成功
    assert success is True
    assert '1张图片处理失败' in msg
    assert 'corrupt.jpg' in msg
    assert output_path.exists()


def test_generate_pdf_all_fail(tmp_path):
    """测试所有图片失败时返回失败"""
    generator = PDFGenerator()

    images = [
        {'raw_data': b'bad1', 'filename': 'bad1.jpg'},
        {'raw_data': b'bad2', 'filename': 'bad2.jpg'},
    ]

    output_path = tmp_path / "all_fail.pdf"
    success, msg = generator.generate_pdf(images, output_path)

    assert success is False
    assert '所有图片处理失败' in msg
    assert not output_path.exists()


def test_generate_pdf_parallel_path(tmp_path):
    """测试并行路径：35张图片触发分块并行生成"""
    generator = PDFGenerator()
    generator.CHUNK_SIZE = 10  # 降低阈值方便测试

    images = [_make_image_data((100, 100), 'img_{}.jpg'.format(i)) for i in range(35)]

    output_path = tmp_path / "parallel.pdf"
    success, msg = generator.generate_pdf(images, output_path)

    assert success is True
    assert msg == ""
    assert output_path.exists()
    assert output_path.stat().st_size > 0

    # 验证PDF文件头
    with open(str(output_path), 'rb') as f:
        header = f.read(5)
    assert header == b'%PDF-'


def test_generate_pdf_parallel_with_progress(tmp_path):
    """测试并行路径进度回调"""
    generator = PDFGenerator()
    generator.CHUNK_SIZE = 10

    images = [_make_image_data((100, 100), 'img_{}.jpg'.format(i)) for i in range(25)]

    progress_calls = []

    def on_progress(current, total):
        progress_calls.append((current, total))

    output_path = tmp_path / "parallel_progress.pdf"
    success, msg = generator.generate_pdf(images, output_path, progress_callback=on_progress)

    assert success is True
    assert len(progress_calls) > 0
    # 最后一次回调应为 (chunk_count, chunk_count)
    assert progress_calls[-1][0] == progress_calls[-1][1]


def test_generate_pdf_parallel_partial_failure(tmp_path):
    """测试并行路径部分图片失败"""
    generator = PDFGenerator()
    generator.CHUNK_SIZE = 5

    images = [_make_image_data((100, 100), 'valid_{}.jpg'.format(i)) for i in range(12)]
    # 在中间插入损坏图片
    images.insert(3, {'raw_data': b'corrupt', 'filename': 'bad1.jpg'})
    images.insert(8, {'raw_data': b'corrupt', 'filename': 'bad2.jpg'})

    output_path = tmp_path / "parallel_partial.pdf"
    success, msg = generator.generate_pdf(images, output_path)

    assert success is True
    assert '2张图片处理失败' in msg
    assert 'bad1.jpg' in msg
    assert 'bad2.jpg' in msg
    assert output_path.exists()


def test_generate_pdf_parallel_all_fail(tmp_path):
    """测试并行路径全部失败"""
    generator = PDFGenerator()
    generator.CHUNK_SIZE = 5

    images = [{'raw_data': b'bad', 'filename': 'bad_{}.jpg'.format(i)} for i in range(12)]

    output_path = tmp_path / "parallel_all_fail.pdf"
    success, msg = generator.generate_pdf(images, output_path)

    assert success is False
    assert '所有图片处理失败' in msg
    assert not output_path.exists()
