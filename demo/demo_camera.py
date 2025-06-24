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

class BackgroundManager(QObject):
    def __init__(self, label: QLabel, combo_res: QComboBox, rotation: int = 0, interval_ms: int = 33, parent=None):
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering __init__: args={{label:{label}, combo_res:{combo_res}, rotation:{rotation}, interval_ms:{interval_ms}}}")
        super().__init__(parent)
        self.label = label
        self.combo_res = combo_res
        self._mutex = QMutex()
        self.rotation = rotation
        self.label.lower()
        self.thread = CameraCaptureThread()
        self.thread.frame_ready.connect(self._on_frame_ready)
        self.thread.start()
        self.last_camera = None
        self.captured = None
        self.generated = None
        self.current = 'live'
        self.combo_res.addItems(["Low", "HD 720p", "Full HD", "2K"])
        self.combo_res.currentIndexChanged.connect(self._on_resolution_changed)
        self.timer = QTimer(self)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self.update_background)
        self.timer.start()
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting __init__: return=None")

    def set_rotation(self, angle: int) -> None:
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering set_rotation: args={{angle:{angle}}}")
        if angle in (0, 90, 180, 270):
            with QMutexLocker(self._mutex):
                self.rotation = angle
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting set_rotation: return=None")

    def _on_resolution_changed(self, index: int) -> None:
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering _on_resolution_changed: args={{index:{index}}}")
        self.thread.set_resolution_level(index)
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting _on_resolution_changed: return=None")

    def _on_frame_ready(self, qimg: QImage) -> None:
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering _on_frame_ready: args={{qimg:{qimg}}}")
        pix = QPixmap.fromImage(qimg)
        with QMutexLocker(self._mutex):
            self.last_camera = pix
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting _on_frame_ready: return=None")

    def set_live(self) -> None:
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering set_live: args={{}}")
        with QMutexLocker(self._mutex): self.current = 'live'
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting set_live: return=None")

    def capture(self) -> None:
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering capture: args={{}}")
        with QMutexLocker(self._mutex):
            if self.last_camera: self.captured = QPixmap(self.last_camera)
            self.current = 'captured'
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting capture: return=None")

    def set_generated(self, qimage: QImage) -> None:
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering set_generated: args={{qimage:{qimage}}}")
        with QMutexLocker(self._mutex):
            self.generated = QPixmap.fromImage(qimage)
            self.current = 'generated'
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting set_generated: return=None")

    def on_generate(self) -> None:
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering on_generate: args={{}}")
        w, h = 640, 480
        img = QImage(w, h, QImage.Format_RGB888)
        img.fill(Qt.red)
        self.set_generated(img)
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting on_generate: return=None")

    def clear(self) -> None:
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering clear: args={{}}")
        with QMutexLocker(self._mutex):
            self.captured = None
            self.generated = None
            self.current = 'live'
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting clear: return=None")

    def get_pixmap(self) -> QPixmap:
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering get_pixmap: args={{}}")
        with QMutexLocker(self._mutex):
            result = self.generated if self.current=='generated' and self.generated else (self.captured if self.current=='captured' and self.captured else self.last_camera)
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting get_pixmap: return={result}")
        return result

    def render_pixmap(self, pix: QPixmap) -> None:
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering render_pixmap: args={{pix:{pix}}}")
        self.label.lower()
        if self.rotation != 0:
            pix = pix.transformed(QTransform().rotate(self.rotation), Qt.SmoothTransformation)
        lw, lh = self.label.width(), self.label.height()
        ow, oh = pix.width(), pix.height()
        factor = lh/oh; nw = int(ow*factor)
        scaled = pix.scaled(nw, lh, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        if nw < lw:
            result = QPixmap(lw, lh); result.fill(Qt.black)
            p = QPainter(result); x=(lw-nw)//2; p.drawPixmap(x,0,scaled); p.end()
        else:
            x=(nw-lw)//2; result = scaled.copy(x,0,lw,lh)
        grad = QPixmap("./gui_template/Gradient_1.png")
        if not grad.isNull():
            gs = grad.scaled(lw,lh,Qt.IgnoreAspectRatio,Qt.SmoothTransformation)
            p = QPainter(result); p.setOpacity(1.0); p.drawPixmap(0,0,gs); p.end()
        self.label.setPixmap(result)
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting render_pixmap: return=None")

    def update_background(self) -> None:
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering update_background: args={{}}")
        pix = self.get_pixmap()
        if pix: self.render_pixmap(pix)
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting update_background: return=None")

    def close(self) -> None:
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering close: args={{}}")
        self.timer.stop()
        self.thread.stop()
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting close: return=None")

class MainWindow(QWidget):
    def __init__(self):
        if DEBUG_MainWindow: print(f"[DEBUG][MainWindow] Entering __init__: args={{}}")
        super().__init__()
        self.setWindowTitle("Demo Background Manager")
        self.showFullScreen()
        self.label = QLabel(alignment=Qt.AlignCenter)
        self.combo_res = QComboBox()
        self.combo_rot = QComboBox(); self.combo_rot.addItems(["0°","90°","180°","270°"])
        self.btn_capture = QPushButton("Capture"); self.btn_live = QPushButton("Live")
        self.btn_generate = QPushButton("Générer image"); self.btn_clear = QPushButton("Clear")
        ctrl = QHBoxLayout(); ctrl.addWidget(self.combo_res); ctrl.addWidget(self.combo_rot)
        for btn in (self.btn_capture,self.btn_live,self.btn_generate,self.btn_clear): ctrl.addWidget(btn)
        layout = QVBoxLayout(self); layout.addWidget(self.label); layout.addLayout(ctrl)
        init_rot = self.combo_rot.currentIndex()*90
        self.bg = BackgroundManager(self.label, self.combo_res, rotation=init_rot)
        self.combo_rot.currentIndexChanged.connect(lambda idx: self.bg.set_rotation(idx*90))
        self.btn_capture.clicked.connect(self.bg.capture)
        self.btn_live.clicked.connect(self.bg.set_live)
        self.btn_generate.clicked.connect(self.bg.on_generate)
        self.btn_clear.clicked.connect(self.bg.clear)
        if DEBUG_MainWindow: print(f"[DEBUG][MainWindow] Exiting __init__: return=None")

    def closeEvent(self, event) -> None:
        if DEBUG_MainWindow: print(f"[DEBUG][MainWindow] Entering closeEvent: args={{event:{event}}}")
        self.bg.close()
        super().closeEvent(event)
        if DEBUG_MainWindow: print(f"[DEBUG][MainWindow] Exiting closeEvent: return=None")

def main() -> None:
    if DEBUG_MainWindow: print(f"[DEBUG][MainWindow] Entering main: args={{}}")
    app = QApplication(sys.argv)
    win = MainWindow()
    sys.exit(app.exec())
    if DEBUG_MainWindow: print(f"[DEBUG][MainWindow] Exiting main: return=None")

if __name__ == '__main__':
    main()

