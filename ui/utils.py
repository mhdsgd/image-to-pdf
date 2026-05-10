# ui/utils.py
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image


def pil_to_qpixmap(pil_img: Image.Image) -> QPixmap:
    """将 PIL Image 转为 QPixmap"""
    if pil_img.mode == 'RGB':
        bpl = pil_img.width * 3
        qimg = QImage(pil_img.tobytes(), pil_img.width, pil_img.height, bpl, QImage.Format_RGB888)
    elif pil_img.mode == 'RGBA':
        bpl = pil_img.width * 4
        qimg = QImage(pil_img.tobytes(), pil_img.width, pil_img.height, bpl, QImage.Format_RGBA8888)
    else:
        pil_img = pil_img.convert('RGB')
        bpl = pil_img.width * 3
        qimg = QImage(pil_img.tobytes(), pil_img.width, pil_img.height, bpl, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg)
