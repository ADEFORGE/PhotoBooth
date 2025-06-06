from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QLabel
import cv2
import os
from comfy_classes.comfy_class_API_test_GUI import ImageGeneratorAPIWrapper
import unicodedata
import re
import io
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QPen, QColor, QPainterPath
from constante import TITLE_LABEL_BORDER_COLOR, TITLE_LABEL_COLOR, TITLE_LABEL_BORDER_WIDTH, TITLE_LABEL_FONT_FAMILY, TITLE_LABEL_FONT_SIZE, TITLE_LABEL_BOLD, TITLE_LABEL_ITALIC
import numpy as np
from PIL import Image

class ImageUtils:
    @staticmethod
    def qimage_to_cv(qimg: QImage) -> np.ndarray:
        qimg = qimg.convertToFormat(QImage.Format_RGB888)
        w, h = qimg.width(), qimg.height()
        buffer = qimg.bits().tobytes()
        arr = np.frombuffer(buffer, np.uint8).reshape((h, w, 3))
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

    @staticmethod
    def cv_to_qimage(cv_img: np.ndarray) -> QImage:
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        return QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()

# Utility function for button name normalization (used in multiple dialogs)
def normalize_btn_name(btn_name):
    name = btn_name.lower()
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    name = re.sub(r'[^a-z0-9]+', '_', name)
    name = name.strip('_')
    return name

class QRCodeUtils:
    @staticmethod
    def generate_qrcode(data: str, box_size: int = 10, border: int = 4) -> Image.Image:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        return img

    @staticmethod
    def pil_to_qimage(pil_img) -> QImage:
        import io
        buf = io.BytesIO()
        pil_img.save(buf, format='PNG')
        return QImage.fromData(buf.getvalue())

    class Worker(QObject):
        finished = Signal(QImage)
        def __init__(self, data: str):
            super().__init__()
            self.data = data
        def run(self):
            img = QRCodeUtils.generate_qrcode(self.data)
            qimg = QRCodeUtils.pil_to_qimage(img)
            self.finished.emit(qimg)

    @staticmethod
    def show_qrcode_overlay(data: str = "https://youtu.be/xvFZjo5PgG0?si=pp6hBg7rL4zineRX"):
        from gui_classes.overlay import OverlayRules
        from PySide6.QtWidgets import QApplication
        pil_img = QRCodeUtils.generate_qrcode(data)
        qimg = QRCodeUtils.pil_to_qimage(pil_img)
        app = QApplication.instance()
        parent = app.activeWindow() if app else None
        overlay = OverlayRules(parent)
        overlay.show_overlay()
        overlay.display_qrcode(qimg)

class OutlinedLabel(QLabel):
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self.outline_color = QColor(TITLE_LABEL_BORDER_COLOR)
        self.text_color = QColor(TITLE_LABEL_COLOR)
        self.outline_width = TITLE_LABEL_BORDER_WIDTH
        font = QFont(TITLE_LABEL_FONT_FAMILY, TITLE_LABEL_FONT_SIZE)
        font.setBold(TITLE_LABEL_BOLD)
        font.setItalic(TITLE_LABEL_ITALIC)
        self.setFont(font)
        self.setAlignment(Qt.AlignCenter)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = self.font()
        painter.setFont(font)
        rect = self.rect()
        text = self.text()
        metrics = painter.fontMetrics()
        x = (rect.width() - metrics.horizontalAdvance(text)) // 2
        y = (rect.height() + metrics.ascent() - metrics.descent()) // 2
        path = QPainterPath()
        path.addText(x, y, font, text)
        pen = QPen(self.outline_color)
        pen.setWidth(self.outline_width)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.setPen(self.text_color)
        painter.drawText(rect, Qt.AlignCenter, text)

class GenerationWorker(QObject):
    finished = Signal(QImage)

    def __init__(self, style, input_image=None):
        super().__init__()
        self.style = style
        self.input_image = input_image
        self.generator = ImageGeneratorAPIWrapper()

    def run(self):
        try:
            if self.input_image is not None:
                arr = ImageUtils.qimage_to_cv(self.input_image)
                cv2.imwrite("../ComfyUI/input/input.png", arr)
            self.generator.set_style(self.style)
            self.generator.generate_image()
            images = self.generator.get_image_paths()
            if images and os.path.exists(images[0]):
                img = cv2.imread(images[0])
                if img is not None:
                    qimg = ImageUtils.cv_to_qimage(img)
                    self.finished.emit(qimg)
                    os.remove(images[0])
                    return
            self.finished.emit(QImage())
        except Exception as e:
            print(f"[ERROR] Erreur génération: {str(e)}")
            self.finished.emit(QImage())
