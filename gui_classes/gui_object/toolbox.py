from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QLabel
import cv2
import os
from comfy_classes.comfy_class_API import ImageGeneratorAPIWrapper
import unicodedata
import re
import io
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QPen, QColor, QPainterPath
from gui_classes.gui_object.constante import TITLE_LABEL_BORDER_COLOR, TITLE_LABEL_COLOR, TITLE_LABEL_BORDER_WIDTH, TITLE_LABEL_FONT_FAMILY, TITLE_LABEL_FONT_SIZE, TITLE_LABEL_BOLD, TITLE_LABEL_ITALIC, DEBUG
import numpy as np
from PIL import Image

from PySide6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QFrame, QApplication
from PySide6.QtCore import Qt, QTimer
import sys


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



class LoadingBar(QWidget):
    def __init__(self, width_percent=0.5, height_percent=0.1, border_thickness=8, parent=None):
        super().__init__(parent)
        # Retrieve screen size and compute widget dimensions
        screen_size = QApplication.primaryScreen().size()
        w = int(screen_size.width() * width_percent)
        h = int(screen_size.height() * height_percent)
        self.setFixedSize(w, h)

        # Transparent window settings
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Dynamic styling values based on widget size
        corner_radius = int(h * 0.25)
        bar_height = int(h * 0.4)

        # Outer frame: transparent fill, white border, rounded corners
        frame = QFrame(self)
        frame.setObjectName("frame")
        frame.setGeometry(0, 0, w, h)
        frame.setStyleSheet(
            f"#frame {{"
            f"    background-color: transparent;"
            f"    border: {border_thickness}px solid rgba(200, 200, 200, 255);"
            f"    border-radius: {corner_radius}px;"
            f"}}"
        )

        # Calculate margins to center the bar vertically
        vertical_margin = max(0, (h - 2 * border_thickness - bar_height) // 2)
        main_layout = QVBoxLayout(frame)
        main_layout.setContentsMargins(border_thickness, vertical_margin, border_thickness, vertical_margin)
        main_layout.setSpacing(0)

        # Progress bar: transparent background, no border, rounded chunk
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(bar_height)
        self.progress.setStyleSheet(
            "QProgressBar {"
            "    background-color: transparent;"
            "    border: none;"
            f"    border-radius: {corner_radius // 2}px;"
            "}"
            "QProgressBar::chunk {"
            "    background-color: rgba(200, 200, 200, 255);" 
            f"    border-radius: {corner_radius // 2}px;"
            "}"
        )
        main_layout.addWidget(self.progress)

        # Timer for animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_progress)
        self._duration_ms = 2000

    def setDuration(self, seconds: float):
        """Set the fill duration in seconds."""
        self._duration_ms = int(seconds * 1000)
        # 100 steps => interval
        self.timer.setInterval(max(1, self._duration_ms // 100))

    def start(self):
        """Show the bar and start filling."""
        self.progress.setValue(0)
        # Ensure timer interval matches duration
        self.setDuration(self._duration_ms / 1000)
        self.show()
        self.timer.start()

    def _update_progress(self):
        val = self.progress.value() + 1
        if val > self.progress.maximum():
            self.timer.stop()
            self.close()
        else:
            self.progress.setValue(val)