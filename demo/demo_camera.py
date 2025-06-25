import sys
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QComboBox
from PySide6.QtCore import Qt, QThread, Signal, QObject, QMutex, QMutexLocker, QTimer
from PySide6.QtGui import QImage, QPixmap, QPainter, QTransform
import cv2

DEBUG_CameraCaptureThread = True
DEBUG_BackgroundManager = True
DEBUG_MainWindow = True

class CameraCaptureThread(QThread):
    frame_ready = Signal(QImage)
    RESOLUTIONS = {0: (640, 480), 1: (1280, 720), 2: (1920, 1080), 3: (2560, 1440)}

    def __init__(self, camera_id: int = 0, parent=None):
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Entering __init__: args={{camera_id:{camera_id}, parent:{parent}}}")
        super().__init__(parent)
        self.camera_id = camera_id
        self._running = True
        self.cap = None
        self.current_res = 0
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Exiting __init__: return=None")

    def set_resolution_level(self, level: int) -> None:
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Entering set_resolution_level: args={{level:{level}}}")
        if level in self.RESOLUTIONS:
            self.current_res = level
            if self.cap and self.cap.isOpened():
                w, h = self.RESOLUTIONS[level]
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Exiting set_resolution_level: return=None")

    def run(self) -> None:
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Entering run: args={{}}")
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            print(f"[Camera] Impossible d'ouvrir la caméra id={self.camera_id}")
            if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Exiting run: return=None")
            return
        self.set_resolution_level(self.current_res)
        while self._running:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
                self.frame_ready.emit(qimg)
            self.msleep(33)
        self.cap.release()
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Exiting run: return=None")

    def stop(self) -> None:
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Entering stop: args={{}}")
        self._running = False
        self.wait()
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Exiting stop: return=None")
import sys
from PySide6.QtWidgets import (
    QWidget, QLabel, QGridLayout, QPushButton, QHBoxLayout, QVBoxLayout, QApplication
)
from PySide6.QtGui import QPixmap, QIcon, QPainter, QImage
from PySide6.QtCore import Qt, QSize, QMutex, QMutexLocker
from gui_classes.gui_object.overlay import (
    OverlayLoading, OverlayRules, OverlayInfo, OverlayQrcode, OverlayLang
)
from gui_classes.gui_object.toolbox import QRCodeUtils
from gui_classes.gui_object.constante import (
    GRID_WIDTH, GRID_VERTICAL_SPACING, GRID_HORIZONTAL_SPACING,
    GRID_LAYOUT_MARGINS, GRID_LAYOUT_SPACING, GRID_ROW_STRETCHES,
    ICON_BUTTON_STYLE, LOGO_SIZE, INFO_BUTTON_SIZE
)
from gui_classes.gui_object.btn import Btns

DEBUG_PhotoBoothBaseWidget = True

class BackgroundManager(QWidget):
    def __init__(self, parent=None):
        if DEBUG_PhotoBoothBaseWidget: print(f"[DEBUG][BackgroundManager] Entering __init__: args={{parent:{parent}}}")
        super().__init__(parent)
        self._mutex = QMutex()
        self.pixmap = None
        self.lower()
        if DEBUG_PhotoBoothBaseWidget: print(f"[DEBUG][BackgroundManager] Exiting __init__: return=None")

    def set_pixmap(self, pix: QPixmap) -> None:
        if DEBUG_PhotoBoothBaseWidget: print(f"[DEBUG][BackgroundManager] Entering set_pixmap: args={{pix:{pix}}}")
        with QMutexLocker(self._mutex):
            self.pixmap = pix
        if DEBUG_PhotoBoothBaseWidget: print(f"[DEBUG][BackgroundManager] Exiting set_pixmap: return=None")

    def paintEvent(self, event) -> None:
        if DEBUG_PhotoBoothBaseWidget: print(f"[DEBUG][BackgroundManager] Entering paintEvent: args={{event:{event}}}")
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        with QMutexLocker(self._mutex):
            if self.pixmap:
                scaled = self.pixmap.scaled(
                    self.width(), self.height(), 
                    Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )
                x = (scaled.width() - self.width()) // 2
                y = (scaled.height() - self.height()) // 2
                painter.drawPixmap(-x, -y, scaled)
        if DEBUG_PhotoBoothBaseWidget: print(f"[DEBUG][BackgroundManager] Exiting paintEvent: return=None")

class BaseWindow(QWidget):
    def __init__(self, parent=None):
        if DEBUG_PhotoBoothBaseWidget: print(f"[DEBUG][PhotoBoothBaseWidget] Entering __init__: args={{parent:{parent}}}")
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        self.bg = BackgroundManager(self)
        self.bg.setGeometry(0, 0, 1920, 1080)
        self.bg.show()

        self.overlay_widget = QWidget(self)
        self.overlay_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(*GRID_LAYOUT_MARGINS)
        self.overlay_layout.setSpacing(GRID_LAYOUT_SPACING)
        self.overlay_layout.setVerticalSpacing(GRID_VERTICAL_SPACING)
        self.overlay_layout.setHorizontalSpacing(GRID_HORIZONTAL_SPACING)

        self.setupcontainer()
        self.setup_row_stretches()

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.overlay_widget)
        self.btns = None

        self._lang_btn.clicked.connect(self.show_lang_dialog)
        self._rules_btn.clicked.connect(self.show_rules_dialog)

        if DEBUG_PhotoBoothBaseWidget: print(f"[DEBUG][PhotoBoothBaseWidget] Exiting __init__: return=None")

    def resizeEvent(self, event) -> None:
        if DEBUG_PhotoBoothBaseWidget: print(f"[DEBUG][PhotoBoothBaseWidget] Entering resizeEvent: args={{event:{event}}}")
        self.bg.setGeometry(0, 0, self.width(), self.height())
        self.overlay_widget.setGeometry(0, 0, self.width(), self.height())
        if self.btns:
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.raise_()
        super().resizeEvent(event)
        if DEBUG_PhotoBoothBaseWidget: print(f"[DEBUG][PhotoBoothBaseWidget] Exiting resizeEvent: return=None")

    def setupcontainer(self) -> None:
        if DEBUG_PhotoBoothBaseWidget: print(f"[DEBUG][PhotoBoothBaseWidget] Entering setupcontainer: args={{}}")
        top_bar = QHBoxLayout()
        logo = QLabel()
        pix = QPixmap("gui_template/base_window/logo1.png").scaled(LOGO_SIZE, LOGO_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo.setPixmap(pix)
        top_bar.addWidget(logo)

        self._lang_btn = QPushButton()
        self._rules_btn = QPushButton()
        for btn, ico in [(self._lang_btn, "language.png"), (self._rules_btn, "rule_ico.png")]:
            btn.setStyleSheet(ICON_BUTTON_STYLE)
            icon = QPixmap(f"gui_template/base_window/{ico}")
            btn.setIcon(QIcon(icon))
            btn.setIconSize(QSize(INFO_BUTTON_SIZE, INFO_BUTTON_SIZE))
            btn.setFixedSize(INFO_BUTTON_SIZE+16, INFO_BUTTON_SIZE+16)
            top_bar.addWidget(btn)

        container = QWidget()
        container.setLayout(top_bar)
        container.setAttribute(Qt.WA_TranslucentBackground, True)
        self.overlay_layout.addWidget(container, 0, 0, 1, GRID_WIDTH)
        if DEBUG_PhotoBoothBaseWidget: print(f"[DEBUG][PhotoBoothBaseWidget] Exiting setupcontainer: return=None")

    def setup_row_stretches(self) -> None:
        if DEBUG_PhotoBoothBaseWidget: print(f"[DEBUG][PhotoBoothBaseWidget] Entering setup_row_stretches: args={{}}")
        for row, stretch in GRID_ROW_STRETCHES.items():
            idx = {'title':0,'display':1,'buttons':2}[row]
            self.overlay_layout.setRowStretch(idx, stretch)
        if DEBUG_PhotoBoothBaseWidget: print(f"[DEBUG][PhotoBoothBaseWidget] Exiting setup_row_stretches: return=None")

    # ... autres méthodes (clear_buttons, show_loading, etc.) restent inchangées.

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = BaseWindow()
    win.showFullScreen()
    sys.exit(app.exec())
