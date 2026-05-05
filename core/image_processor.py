from pathlib import Path
from PIL import Image
from typing import List, Dict, Optional


class ImageProcessor:
    """图片处理器"""

    def __init__(self, thumbnail_size: tuple = (100, 100)):
        self.thumbnail_size = thumbnail_size

    def load_image(self, image_path: Path) -> Optional[Dict]:
        """加载单张图片"""
        try:
            if not image_path.exists():
                return None

            img = Image.open(image_path)
            thumbnail = self.generate_thumbnail(img)

            return {
                'path': image_path,
                'filename': image_path.name,
                'image': img,
                'thumbnail': thumbnail
            }
        except Exception as e:
            print(f"加载图片失败: {image_path}, 错误: {e}")
            return None

    def generate_thumbnail(self, image: Image.Image) -> Image.Image:
        """生成缩略图"""
        thumbnail = image.copy()
        thumbnail.thumbnail(self.thumbnail_size)
        return thumbnail

    def load_images_from_directory(self, directory: Path) -> List[Dict]:
        """从目录加载所有图片"""
        images = []
        supported_formats = {'.jpg', '.jpeg', '.png', '.webp'}

        for file_path in sorted(directory.iterdir()):
            if file_path.suffix.lower() in supported_formats:
                img_data = self.load_image(file_path)
                if img_data:
                    images.append(img_data)

        return images

    def load_images_from_files(self, file_paths: List[Path]) -> List[Dict]:
        """从文件列表加载图片"""
        images = []

        for file_path in file_paths:
            img_data = self.load_image(file_path)
            if img_data:
                images.append(img_data)

        return images
