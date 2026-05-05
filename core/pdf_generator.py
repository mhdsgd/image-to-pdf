from pathlib import Path
from PIL import Image
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from typing import List, Dict, Tuple


class PDFGenerator:
    """PDF生成器"""

    # 页面尺寸映射
    PAGE_SIZES = {
        'A4': A4,
        'Letter': letter
    }

    def __init__(self):
        self.page_size = 'A4'
        self.orientation = 'portrait'
        self.margin = 72  # 1英寸 = 72点

    def set_page_settings(self, page_size: str = None, orientation: str = None, margin: int = None):
        """设置页面参数"""
        if page_size is not None:
            self.page_size = page_size
        if orientation is not None:
            self.orientation = orientation
        if margin is not None:
            self.margin = margin

    def calculate_page_dimensions(self) -> Tuple[int, int]:
        """计算页面尺寸"""
        base_width, base_height = self.PAGE_SIZES.get(self.page_size, A4)

        if self.orientation == 'landscape':
            return round(base_height), round(base_width)
        else:
            return round(base_width), round(base_height)

    def calculate_image_position(self, image_width: int, image_height: int,
                                 page_width: int, page_height: int, margin: int) -> Tuple[int, int, int, int]:
        """计算图片在页面中的位置和尺寸"""
        available_width = page_width - 2 * margin
        available_height = page_height - 2 * margin

        # 计算缩放比例
        width_ratio = available_width / image_width
        height_ratio = available_height / image_height
        scale = min(width_ratio, height_ratio)

        # 计算缩放后的尺寸
        new_width = image_width * scale
        new_height = image_height * scale

        # 计算居中位置
        x = margin + (available_width - new_width) / 2
        y = margin + (available_height - new_height) / 2

        return x, y, new_width, new_height

    def generate_pdf(self, images: List[Dict], output_path: Path, quality: str = 'original') -> bool:
        """生成PDF文件"""
        try:
            page_width, page_height = self.calculate_page_dimensions()

            c = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))

            for img_data in images:
                img = img_data['image']

                # 根据质量设置调整图片
                if quality == 'high':
                    img = img.copy()
                    img.thumbnail((1500, 1500), Image.Resampling.LANCZOS)
                elif quality == 'medium':
                    img = img.copy()
                    img.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
                elif quality == 'low':
                    img = img.copy()
                    img.thumbnail((500, 500), Image.Resampling.LANCZOS)

                # 计算图片位置
                x, y, width, height = self.calculate_image_position(
                    img.width, img.height, page_width, page_height, self.margin
                )

                # 保存临时图片
                temp_path = Path("temp_image.png")
                img.save(temp_path)

                # 绘制图片
                c.drawImage(str(temp_path), x, y, width, height)

                # 删除临时文件
                temp_path.unlink()

                # 新建页面
                c.showPage()

            c.save()
            return True

        except Exception as e:
            print(f"生成PDF失败: {e}")
            return False
