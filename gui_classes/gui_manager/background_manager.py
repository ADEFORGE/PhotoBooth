import sys
from PySide6.QtCore import Qt, QObject, QMutex, QMutexLocker
from PySide6.QtGui import QImage, QPixmap, QPainter, QTransform
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout

from gui_classes.gui_manager.thread_manager import CameraCaptureThread

import logging
logger = logging.getLogger(__name__)

from gui_classes.gui_object.constant import DEBUG, DEBUG_FULL

DEBUG_BackgroundManager = DEBUG
DEBUG_BackgroundManager_FULL = DEBUG_FULL

class BackgroundManager(QObject):
    def __init__(
        self,
        label: QLabel,
        gradient_path: str = './gui_template/gradient/gradient_1.png',
        resolution_level: int = 0,
        rotation: int = 270,
        parent=None
    ) -> None:
        """
        Initialize the BackgroundManager with a label, gradient path, resolution, rotation, and optional parent.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering __init__: args=({label!r}, {gradient_path!r}, {resolution_level!r}, {rotation!r}, {parent!r})")
        super().__init__(parent)
        self.label = label
        self.rotation = rotation
        self.gradient_path = gradient_path
        self._mutex = QMutex()
        self._show_gradient = True 

        self.label.setAttribute(Qt.WA_OpaquePaintEvent)

        self.gradient_label = QLabel(self.label.parent())
        self.gradient_label.setAttribute(Qt.WA_TranslucentBackground)
        self.gradient_label.setStyleSheet("background: transparent;")
        self._init_gradient()
        self.thread = CameraCaptureThread()
        self.thread.set_resolution_level(resolution_level)
        self.thread.frame_ready.connect(self._on_frame_ready)
        self.thread.start()

        self.last_camera: QPixmap | None = None
        self.captured: QPixmap | None = None
        self.generated: QPixmap | None = None
        self.current: str = 'live'
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Exiting __init__: return=None")

    def _init_gradient(self) -> None:
        """
        Load and size the gradient overlay once.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering _init_gradient: args=()")
        pixmap = QPixmap(self.gradient_path)
        if pixmap.isNull():
            return
        geom = self.label.geometry()
        self.gradient_label.setGeometry(geom)
        self._gradient_pixmap = pixmap
        self._resize_gradient()
        self.gradient_label.lower()
        
        if not self._show_gradient:
            self.gradient_label.hide()
        
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Exiting _init_gradient: return=None")

    def _resize_gradient(self) -> None:
        """
        Resize the gradient overlay without reloading it.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering _resize_gradient: args=()")
        if not hasattr(self, '_gradient_pixmap'):
            return
        geom = self.label.geometry()
        scaled = self._gradient_pixmap.scaled(
            geom.width(), geom.height(),
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        self.gradient_label.setPixmap(scaled)
        self.gradient_label.setGeometry(geom)
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Exiting _resize_gradient: return=None")

    def show_gradient(self, show: bool) -> None:
        """
        Show or hide the gradient overlay.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering show_gradient: args=({show})")
        with QMutexLocker(self._mutex):
            self._show_gradient = show
            if show:
                self.gradient_label.show()
            else:
                self.gradient_label.hide()
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Exiting show_gradient: return=None")

    def set_rotation(self, angle: int) -> None:
        """
        Set the rotation angle for the camera or captured image.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering set_rotation: args=({angle})")
        if angle in (0, 90, 180, 270):
            with QMutexLocker(self._mutex):
                self.rotation = angle
                if DEBUG_BackgroundManager:
                    logger.info(f"[DEBUG][BackgroundManager] Rotation set to {angle}°")
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Exiting set_rotation: return=None")

    def _on_frame_ready(self, qimg: QImage) -> None:
        """
        Handle a new frame from the camera thread.
        """
        if DEBUG_BackgroundManager_FULL:
            logger.info(f"[DEBUG][BackgroundManager] Entering _on_frame_ready: args=({qimg!r})")
        pix = QPixmap.fromImage(qimg)
        with QMutexLocker(self._mutex):
            self.last_camera = pix
        self._update_view()
        if DEBUG_BackgroundManager_FULL:
            logger.info(f"[DEBUG][BackgroundManager] Exiting _on_frame_ready: return=None")

    def set_live(self) -> None:
        """
        Switch to live camera mode and update the view.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering set_live: args=()")
        with QMutexLocker(self._mutex):
            self.current = 'live'
        self._update_view()
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Exiting set_live: return=None")

    def capture(self, qimage: QImage = None) -> None:
        """
        Capture the current camera frame.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering capture: args=()")
        with QMutexLocker(self._mutex):
            if qimage is not None:
                pix = QPixmap.fromImage(qimage)
                self.captured = pix
            elif self.last_camera:
                pix = QPixmap(self.last_camera)
                self.captured = pix
            self.current = 'captured'
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Exiting capture: return=None")

    def set_generated(self, qimage: QImage) -> None:
        """
        Set the generated image and update the view.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering set_generated: args=({qimage!r})")
        with QMutexLocker(self._mutex):
            self.generated = QPixmap.fromImage(qimage)
            self.current = 'generated'
        self._update_view()
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Exiting set_generated: return=None")

    def on_generate(self) -> None:
        """
        Generate a test image and set it as the generated image.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering on_generate: args=()")
        img = QImage(640, 480, QImage.Format_RGB888)
        img.fill(Qt.red)
        self.set_generated(img)
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Exiting on_generate: return=None")

    def cleanup(self) -> None:
        """
        Clear captured and generated images and reset to live mode.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering cleanup: args=()")
        with QMutexLocker(self._mutex):
            self.captured = None
            self.generated = None
            self.current = 'live'
        self._update_view()
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Exiting cleanup: return=None")

    def get_pixmap(self) -> QPixmap | None:
        """
        Return the current QPixmap depending on the mode.
        """
        if DEBUG_BackgroundManager_FULL:
            logger.info(f"[DEBUG][BackgroundManager] Entering get_pixmap: args=()")
        with QMutexLocker(self._mutex):
            if self.current == 'generated' and self.generated:
                return self.generated
            if self.current == 'captured' and self.captured:
                return self.captured
            return self.last_camera
        if DEBUG_BackgroundManager_FULL:
            logger.info(f"[DEBUG][BackgroundManager] Exiting get_pixmap: return={self.last_camera}")

    def _update_view(self) -> None:
        """
        Update only the camera content, not the gradient.
        """
        if DEBUG_BackgroundManager_FULL:
            logger.info(f"[DEBUG][BackgroundManager] Entering _update_view: args=()")
        pix = self.get_pixmap()
        if pix:
            self._render_camera(pix)
        if DEBUG_BackgroundManager_FULL:
            logger.info(f"[DEBUG][BackgroundManager] Exiting _update_view: return=None")

    def _render_camera(self, pix: QPixmap) -> None:
        """
        Render the given QPixmap to the label, applying rotation and scaling.
        """
        if DEBUG_BackgroundManager_FULL:
            logger.info(f"[DEBUG][BackgroundManager] Entering _render_camera: args=({pix!r})")
        if pix is None:
            if DEBUG_BackgroundManager_FULL:
                logger.info(f"[DEBUG][BackgroundManager] No pixmap to render, clearing label")
            self.label.clear()
            return
        apply_rotation = False
        with QMutexLocker(self._mutex):
            if self.current in ('live'):
                apply_rotation = True
        if apply_rotation and self.rotation:
            pix = pix.transformed(
                QTransform().rotate(self.rotation),
                Qt.SmoothTransformation
            )
        lw, lh = self.label.width(), self.label.height()
        ow, oh = pix.width(), pix.height()
        factor = lh / oh
        nw = int(ow * factor)
        scaled = pix.scaled(
            nw, lh,
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        if nw < lw:
            result = QPixmap(lw, lh)
            result.fill(Qt.black)
            painter = QPainter(result)
            painter.drawPixmap((lw - nw) // 2, 0, scaled)
            painter.end()
        else:
            x = (nw - lw) // 2
            result = scaled.copy(x, 0, lw, lh)
        self.label.setPixmap(result)
        if DEBUG_BackgroundManager_FULL:
            logger.info(f"[DEBUG][BackgroundManager] Exiting _render_camera: return=None")

    def resize_event(self) -> None:
        """
        Should be called on parent resize to adjust gradient and camera view.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering resize_event: args=()")
        self._resize_gradient()
        self._update_view()
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Exiting resize_event: return=None")

    def update_background(self) -> None:
        """
        Alias for updating both the gradient and camera view.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering update_background: args=()")
        self.resize_event()
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Exiting update_background: return=None")   

    def close(self) -> None:
        """
        Stop and wait for the camera thread to finish.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering close: args=()")
        self.thread.stop()
        self.thread.wait()
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Exiting close: return=None")

    def get_background_image(self) -> QPixmap | None:
        """
        Return the current background image, applying rotation if set.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering get_background_image: args=()")
        pix = self.get_pixmap()
        if pix and self.rotation:
            if DEBUG_BackgroundManager:
                logger.info(f"[DEBUG][BackgroundManager] Applying rotation: {self.rotation} degrees")
            return pix.transformed(QTransform().rotate(self.rotation), Qt.SmoothTransformation)            
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Exiting get_background_image: return={pix}")
        return pix


    def set_camera_resolution(self, level: int) -> None:
        """
        Change the camera stream resolution.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering set_camera_resolution: args=({level})")
        if hasattr(self, 'thread') and hasattr(self.thread, 'set_resolution_level'):
            self.thread.set_resolution_level(level)
            if DEBUG_BackgroundManager:
                logger.info(f"[DEBUG][BackgroundManager] Camera resolution changed: level {level}")
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Exiting set_camera_resolution: return=None")

    def on_enter(self) -> None:
        """
        Call when entering the view: show gradient and set camera to high resolution.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering on_enter: args=()")
        self.show_gradient(True)

        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] on_enter: gradient ON, resolution 2 (FullHD)")

    def on_leave(self, timer=None) -> None:
        """
        Call when leaving the view: hide gradient, set camera to low resolution, and unsubscribe from timer if provided.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering on_leave: args=({timer})")
        self.show_gradient(False)
        self.set_camera_resolution(0)
        if timer is not None:
            timer.unsubscribe(self.update_background)
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] on_leave: gradient OFF, resolution 0 (low)")
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Exiting on_leave: return=None")

    def preset(self, timer=None):
        """
        Subscribe update_background to the given timer and set camera to high resolution.
        """
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] Entering preset: args=({timer})")
        self.set_camera_resolution(2)
        if timer is not None:
            if DEBUG_BackgroundManager:
                logger.info(f"[DEBUG][BackgroundManager] Subscribing to timer for background updates")
            timer.subscribe(self.update_background)
        if DEBUG_BackgroundManager:
            logger.info(f"[DEBUG][BackgroundManager] preset: resolution 2 (FullHD), timer subscribed")
