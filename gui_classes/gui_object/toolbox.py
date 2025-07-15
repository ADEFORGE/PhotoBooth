from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QProgressBar, QFrame
from PySide6.QtCore import QObject, Signal, Qt, QTimer
from PySide6.QtGui import QImage, QFont, QPainter, QPen, QColor, QPainterPath
import cv2
import numpy as np
import unicodedata
import re
from PIL import Image

DEBUG_Module = False
DEBUG_ImageUtils = False
DEBUG_QRCodeUtils = False
DEBUG_OutlinedLabel = False
DEBUG_LoadingBar = False


class ImageUtils:
    @staticmethod
    def qimage_to_cv(qimg: QImage) -> np.ndarray:
        if DEBUG_ImageUtils:
            print(f"[DEBUG][ImageUtils] Entering qimage_to_cv: args={qimg}")
        qimg = qimg.convertToFormat(QImage.Format_RGB888)
        w, h = qimg.width(), qimg.height()
        buffer = qimg.bits().tobytes()
        arr = np.frombuffer(buffer, np.uint8).reshape((h, w, 3))
        result = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        if DEBUG_ImageUtils:
            print(f"[DEBUG][ImageUtils] Exiting qimage_to_cv: return={result}")
        return result

    @staticmethod
    def cv_to_qimage(cv_img: np.ndarray) -> QImage:
        if DEBUG_ImageUtils:
            print(f"[DEBUG][ImageUtils] Entering cv_to_qimage: args={cv_img}")
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        result = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
        if DEBUG_ImageUtils:
            print(f"[DEBUG][ImageUtils] Exiting cv_to_qimage: return={result}")
        return result


def normalize_btn_name(btn_name: str) -> str:
    if DEBUG_Module:
        print(f"[DEBUG][Module] Entering normalize_btn_name: args={btn_name}")
    name = btn_name.lower()
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    name = re.sub(r'[^a-z0-9]+', '_', name)
    name = name.strip('_')
    result = name
    if DEBUG_Module:
        print(f"[DEBUG][Module] Exiting normalize_btn_name: return={result}")
    return result


class QRCodeUtils:
    @staticmethod
    def generate_qrcode(data: str, box_size: int = 10, border: int = 4) -> Image.Image:
        if DEBUG_QRCodeUtils:
            print(f"[DEBUG][QRCodeUtils] Entering generate_qrcode: args={(data, box_size, border)}")
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
        if DEBUG_QRCodeUtils:
            print(f"[DEBUG][QRCodeUtils] Exiting generate_qrcode: return={img}")
        return img

    @staticmethod
    def pil_to_qimage(pil_img: Image.Image) -> QImage:
        if DEBUG_QRCodeUtils:
            print(f"[DEBUG][QRCodeUtils] Entering pil_to_qimage: args={pil_img}")
        import io
        buf = io.BytesIO()
        pil_img.save(buf, format='PNG')
        result = QImage.fromData(buf.getvalue())
        if DEBUG_QRCodeUtils:
            print(f"[DEBUG][QRCodeUtils] Exiting pil_to_qimage: return={result}")
        return result

    class Worker(QObject):
        finished = Signal(QImage)

        def __init__(self, data: str) -> None:
            if DEBUG_QRCodeUtils:
                print(f"[DEBUG][QRCodeUtils] Entering Worker.__init__: args={(data,)}")
            super().__init__()
            self.data = data
            if DEBUG_QRCodeUtils:
                print(f"[DEBUG][QRCodeUtils] Exiting Worker.__init__: return=None")

        def run(self) -> None:
            if DEBUG_QRCodeUtils:
                print(f"[DEBUG][QRCodeUtils] Entering Worker.run: args=()")
            img = QRCodeUtils.generate_qrcode(self.data)
            qimg = QRCodeUtils.pil_to_qimage(img)
            self.finished.emit(qimg)
            if DEBUG_QRCodeUtils:
                print(f"[DEBUG][QRCodeUtils] Exiting Worker.run: return=None")

class LoadingBar(QWidget):
    def __init__(self, width_percent: float = 0.5, height_percent: float = 0.1, border_thickness: int = 8, parent=None) -> None:
        if DEBUG_LoadingBar:
            print(f"[DEBUG][LoadingBar] Entering __init__: args={(width_percent, height_percent, border_thickness, parent)}")
        super().__init__(parent)
        screen_size = QApplication.primaryScreen().size()
        w = int(screen_size.width() * width_percent)
        h = int(screen_size.height() * height_percent)
        self.setFixedSize(w, h)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        corner_radius = int(h * 0.25)
        bar_height = int(h * 0.4)
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
        vertical_margin = max(0, (h - 2 * border_thickness - bar_height) // 2)
        main_layout = QVBoxLayout(frame)
        main_layout.setContentsMargins(border_thickness, vertical_margin, border_thickness, vertical_margin)
        main_layout.setSpacing(0)
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
        if DEBUG_LoadingBar:
            print(f"[DEBUG][LoadingBar] Exiting __init__: return=None")


    def set_percent(self, percent: int) -> None:
        """
        Set the progress bar value (0-100).
        """
        if DEBUG_LoadingBar:
            print(f"[DEBUG][LoadingBar] set_percent: {percent}")
        self.progress.setValue(max(0, min(100, percent)))


