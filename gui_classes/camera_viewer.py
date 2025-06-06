from PySide6.QtCore import Qt, QTimer, QThread
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from gui_classes.overlay import OverlayLoading
from gui_classes.gui_base_widget import PhotoBoothBaseWidget, GenerationWorker
import cv2

class CameraViewer(PhotoBoothBaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cap = None
        self.timer = QTimer(self, timeout=self.update_frame)
        self.selected_style = None
        self.loading_overlay = None
        self.generated_image = None
        self._thread = None
        self._worker = None
        self._generation_in_progress = False
        self.original_photo = None

    def start_camera(self):
        from constante import CAMERA_ID
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(CAMERA_ID)
            self.timer.start(30)
            self.generated_image = None

    def stop_camera(self):
        if self.cap and self.cap.isOpened():
            self.timer.stop()
            self.cap.release()
            self.cap = None

    def update_frame(self):
        if self.generated_image is not None:
            self.show_image(self.generated_image)
            return
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.show_pixmap(QPixmap("gui_template/nocam.png"))
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.show_image(qimg)
        self.update()

    def show_loading(self):
        if not self.loading_overlay:
            self.loading_overlay = OverlayLoading(self)
            self.loading_overlay.setGeometry(self.rect())
        self.loading_overlay.show()
        self.loading_overlay.raise_()

    def hide_loading(self):
        if self.loading_overlay:
            self.loading_overlay.hide()

    def capture_photo(self, style_name=None):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
        self.original_photo = qimg
        if style_name:
            self.show_loading()
            self._generation_in_progress = True
            self._thread = QThread()
            self._worker = GenerationWorker(qimg, style_name)
            self._worker.moveToThread(self._thread)
            self._thread.started.connect(self._worker.run)
            self._worker.finished.connect(self.on_generation_finished)
            self._worker.finished.connect(self._thread.quit)
            self._worker.finished.connect(self._worker.deleteLater)
            self._thread.finished.connect(self._thread.deleteLater)
            self._thread.start()
        else:
            self.generated_image = qimg
            self.stop_camera()
            self.update_frame()

    def on_generation_finished(self, qimg):
        self._generation_in_progress = False
        self.hide_loading()
        self.stop_camera()
        if qimg and not qimg.isNull():
            self.generated_image = qimg
        else:
            self.generated_image = self.original_photo
        self.update_frame()

    def cleanup(self):
        self.stop_camera()
        self.generated_image = None
        self._thread = None
        self._worker = None
        if self.loading_overlay:
            self.loading_overlay.hide()
            self.loading_overlay = None

    def showEvent(self, event):
        super().showEvent(event)
        if self.generated_image is not None:
            self.update_frame()
