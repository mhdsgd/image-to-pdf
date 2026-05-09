import pytest
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow


@pytest.fixture
def app():
    """创建QApplication实例"""
    return QApplication([])


def test_main_window_creation(app):
    """测试创建主窗口"""
    window = MainWindow()
    assert window is not None
    assert window.windowTitle() == "图片合并PDF工具"


def test_main_window_components(app):
    """测试主窗口组件"""
    window = MainWindow()

    # 检查组件是否存在
    assert hasattr(window, 'image_list')
    assert hasattr(window, 'preview')
    assert hasattr(window, 'import_button')
    assert hasattr(window, 'generate_button')
    assert hasattr(window, 'settings_button')


def test_import_images(app):
    """测试导入图片功能"""
    window = MainWindow()

    # 模拟导入图片
    from pathlib import Path
    from PIL import Image

    # 创建测试图片
    test_dir = Path("test_images")
    test_dir.mkdir(exist_ok=True)

    for i in range(3):
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_dir / "image_{}.jpg".format(i))

    # 测试导入
    image_paths = list(test_dir.glob("*.jpg"))
    window.import_images(image_paths)

    assert window.image_list.get_image_count() == 3

    # 清理
    import shutil
    shutil.rmtree(test_dir)


def test_generate_pdf(app):
    """测试生成功能"""
    window = MainWindow()

    # 模拟图片数据（使用 raw_data 代替 image）
    from PIL import Image
    from io import BytesIO
    images = []
    for i in range(3):
        buf = BytesIO()
        Image.new('RGB', (100, 100), color='red').save(buf, format='JPEG')
        images.append({
            'raw_data': buf.getvalue(),
            'filename': 'test_{}.jpg'.format(i)
        })

    window.images = images

    # 测试生成
    from pathlib import Path
    output_path = Path("test_output.pdf")
    success, msg = window.generate_pdf(output_path)

    assert success == True
    assert msg == ""
    assert output_path.exists()

    # 清理
    output_path.unlink()


def test_apply_theme_light(app):
    """测试应用浅色主题"""
    window = MainWindow()
    window.apply_theme('light')
    assert len(window.styleSheet()) > 0


def test_apply_theme_dark(app):
    """测试应用深色主题"""
    window = MainWindow()
    window.apply_theme('dark')
    assert len(window.styleSheet()) > 0


def test_apply_theme_nonexistent(app):
    """测试应用不存在的主题"""
    window = MainWindow()
    # 应不会抛出异常
    window.apply_theme('nonexistent')
    assert "主题文件不存在" in window.status_bar.currentMessage()
