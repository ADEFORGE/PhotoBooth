import sys
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QMutex, QMutexLocker, QThread, Signal
from PySide6.QtGui import QImage, QPixmap, QPainter, QTransform
import cv2

# Debug flags
DEBUG_CameraCaptureThread = False
DEBUG_BackgroundManager = False
DEBUG_PhotoBoothBaseWidget = True
DEBUG_MainWindow = True

# --- BaseWindow simplified import ---
from gui_classes.gui_window.base_window import BaseWindow

# --- Camera capture thread ---
class CameraCaptureThread(QThread):
    frame_ready = Signal(QImage)
    RESOLUTIONS = {0: (640, 480), 1: (1280, 720), 2: (1920, 1080), 3: (2560, 1440)}

    def __init__(self, camera_id=0):
        super().__init__()
        self.camera_id = camera_id
        self._running = True
        self.cap = None
        self.current_res = 0

    def set_resolution_level(self, level):
        if level in self.RESOLUTIONS and self.cap and self.cap.isOpened():
            w, h = self.RESOLUTIONS[level]
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
            self.current_res = level

    def run(self):
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            print(f"Cannot open camera {self.camera_id}")
            return
        self.set_resolution_level(self.current_res)
        while self._running:
            ret, frame = self.cap.read()
            if ret:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
                self.frame_ready.emit(qimg)
            self.msleep(33)
        self.cap.release()

    def stop(self):
        self._running = False
        self.wait()

# --- Background manager ---
class BackgroundManager:
    def __init__(self, label: QLabel, resolution_level=0, rotation=0):
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Init: res={resolution_level}, rot={rotation}")
        self.label = label
        self.rotation = rotation
        self._mutex = QMutex()
        self.last_frame = None
        self.thread = CameraCaptureThread()
        self.thread.set_resolution_level(resolution_level)
        self.thread.frame_ready.connect(self._on_frame)
        self.thread.start()

    def _on_frame(self, qimg: QImage):
        pix = QPixmap.fromImage(qimg)
        with QMutexLocker(self._mutex):
            self.last_frame = pix

    def update(self):
        with QMutexLocker(self._mutex):
            pix = self.last_frame
        if pix:
            if self.rotation:
                pix = pix.transformed(QTransform().rotate(self.rotation), Qt.SmoothTransformation)
            w, h = self.label.width(), self.label.height()
            scaled = pix.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = (scaled.width() - w) // 2
            y = (scaled.height() - h) // 2
            cropped = scaled.copy(x, y, w, h)
            self.label.setPixmap(cropped)

    def close(self):
        self.thread.stop()

# --- Main application window inheriting BaseWindow ---
class MainWindow(BaseWindow):
    def __init__(self, parent=None):
        if DEBUG_MainWindow: print(f"[DEBUG][MainWindow] Init: parent={parent}")
        super().__init__(parent)

        # Create camera display label as background
        self.bg_label = QLabel(self)
        self.bg_label.setAlignment(Qt.AlignCenter)
        self.bg_label.setStyleSheet("background: black;")
        # Ensure it is under the overlay
        self.bg_label.lower()
        # Initial geometry
        self.bg_label.setGeometry(0, 0, self.width(), self.height())

        # Initialize background manager on full label
        self.background_manager = BackgroundManager(self.bg_label)

        # Timer for refresh
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.background_manager.update)
        self.timer.start()
        if DEBUG_MainWindow: print(f"[DEBUG][MainWindow] Init complete")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Resize background label to cover entire window
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        # Resize overlay widget to cover window as well
        self.overlay_widget.setGeometry(0, 0, self.width(), self.height())

    def closeEvent(self, event):
        if DEBUG_MainWindow: print(f"[DEBUG][MainWindow] Closing")
        self.timer.stop()
        self.background_manager.close()
        super().closeEvent(event)

# --- Entry point ---

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
