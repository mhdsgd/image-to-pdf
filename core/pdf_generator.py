from io import BytesIO
from PIL import Image
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from typing import List, Dict, Tuple
from core.image_processor import ImageProcessor


def _calculate_image_position(image_width, image_height, page_width, page_height, margin):
    """计算图片在页面中的位置和尺寸（静态工具函数，供worker调用）"""
    available_width = page_width - 2 * margin
    available_height = page_height - 2 * margin

    width_ratio = available_width / image_width
    height_ratio = available_height / image_height
    scale = min(width_ratio, height_ratio)

    new_width = image_width * scale
    new_height = image_height * scale

    x = margin + (available_width - new_width) / 2
    y = margin + (available_height - new_height) / 2

    return x, y, new_width, new_height


def _generate_chunk_pdf(args):
    """多进程worker：生成单个chunk的中间PDF，返回 (chunk_index, temp_path, failed_list)"""
    chunk_index, chunk_images, page_size, orientation, margin, quality, temp_dir = args

    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas as rl_canvas

    PAGE_SIZES = {'A4': A4, 'Letter': letter}
    base_width, base_height = PAGE_SIZES.get(page_size, A4)
    if orientation == 'landscape':
        page_width, page_height = round(base_height), round(base_width)
    else:
        page_width, page_height = round(base_width), round(base_height)

    import os
    temp_path = os.path.join(temp_dir, "chunk_{}.pdf".format(chunk_index))
    failed = []

    try:
        c = rl_canvas.Canvas(temp_path, pagesize=(page_width, page_height))

        for global_idx, img_data in chunk_images:
            reduced = None
            try:
                img = ImageProcessor.get_image(img_data)
                if img is None:
                    failed.append(img_data.get('filename', '第{}张'.format(global_idx + 1)))
                    continue

                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')

                if quality != 'original':
                    target = {'high': 1500, 'medium': 1000, 'low': 500}[quality]
                    w, h = img.size
                    factor = max(1, min(w // target, h // target))
                    if factor > 1:
                        reduced = img.reduce(factor)
                        img = reduced

                x, y, width, height = _calculate_image_position(
                    img.width, img.height, page_width, page_height, margin
                )

                buf = BytesIO()
                try:
                    img.save(buf, format='PNG')
                    buf.seek(0)
                    c.drawImage(ImageReader(buf), x, y, width, height)
                finally:
                    buf.close()

                c.showPage()

            except Exception as e:
                name = img_data.get('filename', '第{}张'.format(global_idx + 1))
                failed.append("{}: {}".format(name, e))
            finally:
                if reduced is not None:
                    reduced.close()
                ImageProcessor.close_image(img_data)

        c.save()
        return chunk_index, temp_path, failed

    except Exception as e:
        failed.append("chunk_{} 整体失败: {}".format(chunk_index, e))
        return chunk_index, temp_path, failed


class PDFGenerator:
    """PDF生成器"""

    PAGE_SIZES = {
        'A4': A4,
        'Letter': letter
    }

    CHUNK_SIZE = 30  # 每chunk图片数，低于此值走串行路径

    def __init__(self):
        self.page_size = 'A4'
        self.orientation = 'portrait'
        self.margin = 72
        self.quality = 'original'

    def set_page_settings(self, page_size=None, orientation=None, margin=None, quality=None):
        if page_size is not None:
            self.page_size = page_size
        if orientation is not None:
            self.orientation = orientation
        if margin is not None:
            self.margin = margin
        if quality is not None:
            self.quality = quality

    def calculate_page_dimensions(self):
        base_width, base_height = self.PAGE_SIZES.get(self.page_size, A4)
        if self.orientation == 'landscape':
            return round(base_height), round(base_width)
        else:
            return round(base_width), round(base_height)

    def calculate_image_position(self, image_width, image_height, page_width, page_height, margin):
        return _calculate_image_position(image_width, image_height, page_width, page_height, margin)

    def generate_pdf(self, images, output_path, quality=None, progress_callback=None):
        # type: (List[Dict], any, str, any) -> Tuple[bool, str]
        """生成PDF文件，返回 (成功与否, 错误信息)"""
        import os

        if quality is None:
            quality = self.quality

        total = len(images)

        # 小批量走串行路径
        if total <= self.CHUNK_SIZE:
            return self._generate_sequential(images, output_path, quality, progress_callback)

        return self._generate_parallel(images, output_path, quality, progress_callback)

    def _generate_sequential(self, images, output_path, quality, progress_callback):
        """串行生成PDF（原有逻辑）"""
        import os

        page_width, page_height = self.calculate_page_dimensions()
        total = len(images)
        output_path = str(output_path)
        failed = []

        try:
            c = canvas.Canvas(output_path, pagesize=(page_width, page_height))

            for i, img_data in enumerate(images):
                reduced = None
                try:
                    img = ImageProcessor.get_image(img_data)

                    if img is None:
                        failed.append(img_data.get('filename', '第{}张'.format(i + 1)))
                        continue

                    if img.mode not in ('RGB', 'L'):
                        img = img.convert('RGB')

                    if quality == 'original':
                        pass
                    else:
                        target = {'high': 1500, 'medium': 1000, 'low': 500}[quality]
                        w, h = img.size
                        factor = max(1, min(w // target, h // target))
                        if factor > 1:
                            reduced = img.reduce(factor)
                            img = reduced

                    x, y, width, height = self.calculate_image_position(
                        img.width, img.height, page_width, page_height, self.margin
                    )

                    buf = BytesIO()
                    try:
                        img.save(buf, format='PNG')
                        buf.seek(0)
                        c.drawImage(ImageReader(buf), x, y, width, height)
                    finally:
                        buf.close()

                    c.showPage()

                except Exception as e:
                    name = img_data.get('filename', '第{}张'.format(i + 1))
                    failed.append("{}: {}".format(name, e))
                    print("处理图片失败: {}, 错误: {}".format(name, e))
                finally:
                    if reduced is not None:
                        reduced.close()
                    ImageProcessor.close_image(img_data)

                if progress_callback:
                    progress_callback(i + 1, total)

            if failed and len(failed) < total:
                c.save()
                msg = "{}张图片处理失败:\n{}".format(len(failed), "\n".join(failed[:10]))
                if len(failed) > 10:
                    msg += "\n...等共{}张".format(len(failed))
                return True, msg

            if failed and len(failed) == total:
                try:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                except Exception:
                    pass
                return False, "所有图片处理失败:\n{}".format("\n".join(failed[:10]))

            c.save()
            return True, ""

        except Exception as e:
            print("生成PDF失败: {}".format(e))
            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
            except Exception:
                pass
            return False, str(e)

    def _generate_parallel(self, images, output_path, quality, progress_callback):
        """并行生成PDF：分块 → 多进程生成中间PDF → 合并"""
        import os
        import math
        import tempfile
        import multiprocessing

        output_path = str(output_path)
        total = len(images)
        chunk_size = self.CHUNK_SIZE
        chunk_count = math.ceil(total / chunk_size)

        # 构建chunks，附带全局索引
        chunks = []
        for ci in range(chunk_count):
            start = ci * chunk_size
            end = min(start + chunk_size, total)
            chunk_images = [(start + j, images[start + j]) for j in range(end - start)]
            chunks.append(chunk_images)

        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="img2pdf_")

        # 构建worker参数
        worker_args = [
            (ci, chunk, self.page_size, self.orientation, self.margin, quality, temp_dir)
            for ci, chunk in enumerate(chunks)
        ]

        failed = []
        temp_paths = [None] * chunk_count
        completed = [0]

        # 使用 apply_async 收集结果，完成后回调进度
        def on_result(result):
            chunk_idx, temp_path, chunk_failed = result
            temp_paths[chunk_idx] = temp_path
            failed.extend(chunk_failed)
            completed[0] += 1
            if progress_callback:
                progress_callback(completed[0], chunk_count)

        def on_error(exc):
            failed.append("进程异常: {}".format(exc))
            completed[0] += 1
            if progress_callback:
                progress_callback(completed[0], chunk_count)

        num_processes = min(multiprocessing.cpu_count(), chunk_count)

        try:
            pool = multiprocessing.Pool(processes=num_processes)

            for args in worker_args:
                pool.apply_async(_generate_chunk_pdf, args=(args,),
                                 callback=on_result, error_callback=on_error)

            pool.close()
            pool.join()

            # 检查是否所有chunk都成功返回了临时文件
            valid_paths = [p for p in temp_paths if p is not None and os.path.exists(p)]

            if not valid_paths:
                # 所有chunk都失败
                try:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                except Exception:
                    pass
                return False, "所有图片处理失败:\n{}".format("\n".join(failed[:10]))

            # 合并临时PDF
            try:
                from PyPDF2 import PdfWriter, PdfReader
                writer = PdfWriter()
                for tp in valid_paths:
                    reader = PdfReader(tp)
                    writer.append_pages_from_reader(reader)
                with open(output_path, 'wb') as f:
                    writer.write(f)
            except Exception as e:
                try:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                except Exception:
                    pass
                return False, "PDF合并失败: {}".format(e)

            # 清理临时文件
            for tp in temp_paths:
                if tp is not None:
                    try:
                        os.remove(tp)
                    except Exception:
                        pass
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass

            # 返回结果
            if failed and len(failed) < total:
                msg = "{}张图片处理失败:\n{}".format(len(failed), "\n".join(failed[:10]))
                if len(failed) > 10:
                    msg += "\n...等共{}张".format(len(failed))
                return True, msg

            if failed and len(failed) == total:
                try:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                except Exception:
                    pass
                return False, "所有图片处理失败:\n{}".format("\n".join(failed[:10]))

            return True, ""

        except Exception as e:
            # 清理临时文件
            for tp in temp_paths:
                if tp is not None:
                    try:
                        os.remove(tp)
                    except Exception:
                        pass
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass
            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
            except Exception:
                pass
            return False, str(e)
