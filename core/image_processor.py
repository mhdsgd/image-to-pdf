from pathlib import Path
from PIL import Image
from typing import List, Dict, Optional
from io import BytesIO
import tempfile
import zipfile
import re

try:
    import py7zr
    HAS_PY7ZR = True
except ImportError:
    HAS_PY7ZR = False

SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}
SUPPORTED_ARCHIVE_FORMATS = {'.zip', '.7z'}


def natural_sort_key(s):
    """自然排序键函数，使 'img2' 排在 'img10' 前面"""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', str(s))]


def _decode_zip_name(raw_name: str) -> str:
    """解码 zip 文件名（处理 CP437 → GBK 中文编码问题）"""
    try:
        return raw_name.encode('cp437').decode('gbk')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return raw_name


class ImageProcessor:
    """图片处理器"""

    def __init__(self, thumbnail_size: tuple = (100, 100)):
        self.thumbnail_size = thumbnail_size

    @staticmethod
    def get_image(img_data: Dict) -> Optional[Image.Image]:
        """按需解压图片（带缓存），从磁盘按需读取原始数据"""
        if '_cached_image' in img_data:
            return img_data['_cached_image']
        source_path = img_data.get('_source_path')
        if source_path is None:
            return None
        try:
            data = Path(source_path).read_bytes()
        except (FileNotFoundError, OSError):
            return None
        img = Image.open(BytesIO(data))
        img.load()
        img_data['_cached_image'] = img
        return img

    @staticmethod
    def close_image(img_data: Dict):
        """释放缓存的 PIL 图片，并清理临时文件（如果有）"""
        cached = img_data.pop('_cached_image', None)
        if cached is not None:
            try:
                cached.close()
            except Exception:
                pass
        if img_data.pop('_temp_file', False):
            source = img_data.get('_source_path')
            if source is not None:
                try:
                    Path(source).unlink(missing_ok=True)
                except Exception:
                    pass

    def load_image(self, image_path: Path) -> Optional[Dict]:
        """加载单张图片（仅存储文件路径和缩略图，原始数据按需从磁盘读取）"""
        try:
            if not image_path.exists():
                return None

            img = Image.open(image_path)
            img.load()
            thumbnail = self.generate_thumbnail(img)
            img.close()

            return {
                'path': image_path,
                'filename': image_path.name,
                '_source_path': image_path,
                'thumbnail': thumbnail
            }
        except Exception as e:
            print(f"加载图片失败: {image_path}, 错误: {e}")
            return None

    def generate_thumbnail(self, image: Image.Image) -> Image.Image:
        """生成缩略图"""
        w, h = image.size
        tw, th = self.thumbnail_size
        factor = max(1, min(w // tw, h // th))
        thumbnail = image.reduce(factor)
        return thumbnail

    def load_images_from_directory(self, directory: Path) -> List[Dict]:
        """从目录加载所有图片"""
        images = []

        if not directory.exists() or not directory.is_dir():
            return images

        for file_path in sorted(directory.iterdir()):
            if file_path.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
                img_data = self.load_image(file_path)
                if img_data:
                    images.append(img_data)

        return images

    def load_images_from_files(self, file_paths: List[Path], progress_callback=None) -> List[Dict]:
        """从文件列表加载图片"""
        images = []
        total = len(file_paths)

        for i, file_path in enumerate(file_paths):
            img_data = self.load_image(file_path)
            if img_data:
                images.append(img_data)
            if progress_callback:
                progress_callback(i + 1, total)

        return images

    def load_image_from_bytes(self, data: bytes, filename: str) -> Optional[Dict]:
        """从字节数据加载单张图片（写入临时文件，按需从磁盘读取）"""
        try:
            img = Image.open(BytesIO(data))
            img.load()
            thumbnail = self.generate_thumbnail(img)
            img.close()

            # 将原始数据写入临时文件，释放内存
            suffix = Path(filename).suffix or '.img'
            tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix=suffix, prefix='img2pdf_'
            )
            try:
                tmp.write(data)
                tmp.flush()
                temp_path = Path(tmp.name)
            finally:
                tmp.close()

            return {
                'path': Path(filename),
                'filename': filename,
                '_source_path': temp_path,
                '_temp_file': True,
                'thumbnail': thumbnail
            }
        except Exception as e:
            print(f"从字节加载图片失败: {filename}, 错误: {e}")
            return None

    def load_images_from_archive(self, archive_path: Path, progress_callback=None) -> List[Dict]:
        """从压缩包加载所有图片"""
        images = []
        suffix = archive_path.suffix.lower()

        if suffix == '.zip':
            images = self._load_from_zip(archive_path, progress_callback)
        elif suffix == '.7z':
            if not HAS_PY7ZR:
                print("未安装 py7zr，无法处理 7z 文件")
                return images
            images = self._load_from_7z(archive_path, progress_callback)
        else:
            print(f"不支持的压缩格式: {suffix}")
            return images

        return images

    def _load_from_zip(self, archive_path: Path, progress_callback=None) -> List[Dict]:
        """从 zip 文件加载图片"""
        images = []
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                all_files = zf.namelist()

                # 获取所有图片文件并自然排序
                image_files = []
                for f in all_files:
                    if f.endswith('/'):
                        continue
                    decoded_name = _decode_zip_name(f)
                    suffix = Path(decoded_name).suffix.lower()
                    if suffix in SUPPORTED_IMAGE_FORMATS:
                        image_files.append(f)

                image_files.sort(key=natural_sort_key)
                total = len(image_files)

                for i, filename in enumerate(image_files):
                    data = zf.read(filename)
                    display_name = Path(_decode_zip_name(filename)).name
                    img_data = self.load_image_from_bytes(data, display_name)
                    if img_data:
                        images.append(img_data)
                    if progress_callback:
                        progress_callback(i + 1, total)
        except Exception as e:
            print(f"读取 zip 文件失败: {archive_path}, 错误: {e}")

        return images

    def _load_from_7z(self, archive_path: Path, progress_callback=None) -> List[Dict]:
        """从 7z 文件加载图片"""
        images = []
        try:
            with py7zr.SevenZipFile(archive_path, 'r') as sz:
                # 先获取文件列表，只读取图片文件
                file_list = sz.list()
                image_names = []
                for info in file_list:
                    if info.is_directory:
                        continue
                    if Path(info.filename).suffix.lower() in SUPPORTED_IMAGE_FORMATS:
                        image_names.append(info.filename)

                image_names.sort(key=natural_sort_key)

                if not image_names:
                    return images

                # 只解压图片文件
                result = sz.read(image_names)
                total = len(image_names)
                for i, filename in enumerate(image_names):
                    bio = result.get(filename)
                    if bio is None:
                        continue
                    data = bio.read()
                    bio.close()
                    display_name = Path(filename).name
                    img_data = self.load_image_from_bytes(data, display_name)
                    if img_data:
                        images.append(img_data)
                    if progress_callback:
                        progress_callback(i + 1, total)
        except Exception as e:
            print(f"读取 7z 文件失败: {archive_path}, 错误: {e}")

        return images
