import pytest
import tempfile
from pathlib import Path
from core.pdf_generator import PDFGenerator


def test_create_pdf_generator():
    """测试创建PDF生成器"""
    generator = PDFGenerator()
    assert generator is not None
    assert generator.page_size == 'A4'
    assert generator.orientation == 'portrait'
    assert generator.margin == 72


def test_set_page_settings():
    """测试设置页面参数"""
    generator = PDFGenerator()

    generator.set_page_settings(
        page_size='Letter',
        orientation='landscape',
        margin=36
    )

    assert generator.page_size == 'Letter'
    assert generator.orientation == 'landscape'
    assert generator.margin == 36


def test_calculate_page_dimensions():
    """测试计算页面尺寸"""
    generator = PDFGenerator()

    # A4 portrait
    width, height = generator.calculate_page_dimensions()
    assert width == 595  # A4宽度（点）
    assert height == 842  # A4高度（点）

    # A4 landscape
    generator.set_page_settings(orientation='landscape')
    width, height = generator.calculate_page_dimensions()
    assert width == 842
    assert height == 595


def test_calculate_image_position():
    """测试计算图片在页面中的位置"""
    generator = PDFGenerator()

    # 测试图片适应页面
    image_width = 1000
    image_height = 800
    page_width = 595
    page_height = 842
    margin = 72

    x, y, width, height = generator.calculate_image_position(
        image_width, image_height, page_width, page_height, margin
    )

    assert x == margin
    assert y > 0
    assert width <= page_width - 2 * margin
    assert height <= page_height - 2 * margin


def test_generate_pdf():
    """测试生成PDF文件"""
    generator = PDFGenerator()
    from PIL import Image
    from io import BytesIO

    # 创建测试图片（写入临时文件）
    test_images = []
    for i in range(3):
        buf = BytesIO()
        Image.new('RGB', (200, 200), color='red').save(buf, format='JPEG')
        suffix = '.jpg'
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix='img2pdf_')
        try:
            tmp.write(buf.getvalue())
            tmp.flush()
            temp_path = Path(tmp.name)
        finally:
            tmp.close()
        test_images.append({
            '_source_path': temp_path,
            '_temp_file': True,
            'filename': f'test_{i}.jpg'
        })

    output_path = Path("test_output.pdf")
    success, msg = generator.generate_pdf(test_images, output_path)

    assert success == True
    assert msg == ""
    assert output_path.exists()

    # 清理
    output_path.unlink()
    for img in test_images:
        from core.image_processor import ImageProcessor
        ImageProcessor.close_image(img)
