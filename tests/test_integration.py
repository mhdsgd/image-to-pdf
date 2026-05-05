# tests/test_integration.py
import pytest
import shutil
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow


@pytest.fixture
def app():
    """创建QApplication实例"""
    return QApplication([])


def test_full_workflow(app):
    """测试完整工作流程: 导入图片 -> 验证排序 -> 预览导航 -> 生成PDF"""
    window = MainWindow()
    test_dir = Path("test_integration_images")
    output_path = Path("test_integration_output.pdf")

    try:
        # 创建测试图片
        test_dir.mkdir(exist_ok=True)

        from PIL import Image
        for i in range(5):
            img = Image.new('RGB', (200, 200), color='red')
            img.save(test_dir / "image_{:03d}.jpg".format(i))

        # 1. 导入图片
        image_paths = sorted(test_dir.glob("*.jpg"))
        window.import_images(image_paths)
        assert window.image_list.get_image_count() == 5

        # 2. 验证排序（按文件名）
        images = window.image_list.get_images()
        assert images[0]['filename'] == 'image_000.jpg'
        assert images[1]['filename'] == 'image_001.jpg'
        assert images[4]['filename'] == 'image_004.jpg'

        # 3. 测试预览导航
        assert window.preview.current_page == 0
        assert window.preview.total_pages == 5

        window.preview.go_to_page(2)
        assert window.preview.current_page == 2

        window.preview.next_page()
        assert window.preview.current_page == 3

        window.preview.previous_page()
        assert window.preview.current_page == 2

        # 跳转到无效页应不改变当前页
        window.preview.go_to_page(99)
        assert window.preview.current_page == 2

        # 4. 测试生成PDF
        result = window.generate_pdf(output_path)
        assert result is True
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    finally:
        # 清理
        if output_path.exists():
            output_path.unlink()
        if test_dir.exists():
            shutil.rmtree(test_dir)


def test_error_handling_invalid_image(app):
    """测试导入无效图片路径的错误处理"""
    window = MainWindow()

    invalid_path = Path("nonexistent_file_that_does_not_exist.jpg")
    window.import_images([invalid_path])
    assert window.image_list.get_image_count() == 0


def test_error_handling_empty_pdf(app):
    """测试空图片列表时生成PDF的行为"""
    window = MainWindow()
    output_path = Path("test_error_output.pdf")

    try:
        # 当前实现中，空列表仍会创建一个空PDF并返回True
        result = window.generate_pdf(output_path)
        # generate_pdf creates an empty PDF even with no images
        assert result is True
        assert output_path.exists()

    finally:
        if output_path.exists():
            output_path.unlink()


def test_incremental_import(app):
    """测试分批导入图片"""
    window = MainWindow()
    test_dir = Path("test_incremental_images")

    try:
        test_dir.mkdir(exist_ok=True)
        from PIL import Image

        # 第一批导入
        for i in range(3):
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(test_dir / "batch1_{}.jpg".format(i))

        paths1 = sorted(test_dir.glob("batch1_*.jpg"))
        window.import_images(paths1)
        assert window.image_list.get_image_count() == 3

        # 第二批导入
        for i in range(2):
            img = Image.new('RGB', (100, 100), color='green')
            img.save(test_dir / "batch2_{}.jpg".format(i))

        paths2 = sorted(test_dir.glob("batch2_*.jpg"))
        window.import_images(paths2)
        assert window.image_list.get_image_count() == 5

    finally:
        if test_dir.exists():
            shutil.rmtree(test_dir)


def test_clear_and_reimport(app):
    """测试清空后重新导入"""
    window = MainWindow()
    test_dir = Path("test_clear_images")

    try:
        test_dir.mkdir(exist_ok=True)
        from PIL import Image

        for i in range(3):
            img = Image.new('RGB', (100, 100), color='yellow')
            img.save(test_dir / "img_{}.jpg".format(i))

        # 导入
        paths = sorted(test_dir.glob("*.jpg"))
        window.import_images(paths)
        assert window.image_list.get_image_count() == 3

        # 清空
        window.on_clear_clicked()
        assert window.image_list.get_image_count() == 0
        assert len(window.images) == 0

        # 重新导入
        window.import_images(paths)
        assert window.image_list.get_image_count() == 3

    finally:
        if test_dir.exists():
            shutil.rmtree(test_dir)


def test_generate_pdf_with_multiple_images(app):
    """测试多张图片生成PDF，验证PDF文件正确生成"""
    window = MainWindow()
    test_dir = Path("test_multi_images")
    output_path = Path("test_multi_output.pdf")

    try:
        test_dir.mkdir(exist_ok=True)
        from PIL import Image

        colors = ['red', 'green', 'blue']
        for i, color in enumerate(colors):
            img = Image.new('RGB', (300, 300), color=color)
            img.save(test_dir / "page_{}.jpg".format(i))

        paths = sorted(test_dir.glob("*.jpg"))
        window.import_images(paths)
        assert window.image_list.get_image_count() == 3

        result = window.generate_pdf(output_path)
        assert result is True
        assert output_path.exists()

        # 验证PDF文件非空且包含有效内容
        pdf_size = output_path.stat().st_size
        assert pdf_size > 0

        # 验证PDF文件头（以%PDF开头）
        with open(str(output_path), 'rb') as f:
            header = f.read(5)
        assert header == b'%PDF-'

    finally:
        if output_path.exists():
            output_path.unlink()
        if test_dir.exists():
            shutil.rmtree(test_dir)
