import sys
from PySide6.QtCore import Qt, QObject, QMutex, QMutexLocker
from PySide6.QtGui import QImage, QPixmap, QPainter, QTransform
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout

from gui_classes.gui_manager.thread_manager import CameraCaptureThread

DEBUG_BackgroundManager = False

class BackgroundManager(QObject):
    """
    Gère le flux caméra, les captures et les images générées,
    avec un overlay dégradé optimisé pour éviter les ralentissements.
    """

    def __init__(self, label: QLabel,
                 gradient_path: str = './gui_template/gradient/gradient_1.png',
                 resolution_level: int = 0,
                 rotation: int = 0,
                 parent=None) -> None:
        super().__init__(parent)
        self.label = label
        self.rotation = rotation
        self.gradient_path = gradient_path
        self._mutex = QMutex()

        # Optimisation du peintre: ne pas effacer entièrement
        self.label.setAttribute(Qt.WA_OpaquePaintEvent)

        # Création du QLabel pour le dégradé
        self.gradient_label = QLabel(self.label.parent())
        self.gradient_label.setAttribute(Qt.WA_TranslucentBackground)
        self.gradient_label.setStyleSheet("background: transparent;")
        self._init_gradient()

        # Thread caméra
        self.thread = CameraCaptureThread()
        self.thread.set_resolution_level(resolution_level)
        self.thread.frame_ready.connect(self._on_frame_ready)
        self.thread.start()

        # États des images
        self.last_camera: QPixmap | None = None
        self.captured: QPixmap | None = None
        self.generated: QPixmap | None = None
        self.current: str = 'live'

    def _init_gradient(self) -> None:
        """Charge et dimensionne le gradient une seule fois."""
        pixmap = QPixmap(self.gradient_path)
        if pixmap.isNull():
            return
        geom = self.label.geometry()
        self.gradient_label.setGeometry(geom)
        self._gradient_pixmap = pixmap
        self._resize_gradient()
        self.gradient_label.lower()

    def _resize_gradient(self) -> None:
        """Redimensionne le gradient sans le recharger."""
        if not hasattr(self, '_gradient_pixmap'):
            return
        geom = self.label.geometry()
        scaled = self._gradient_pixmap.scaled(
            geom.width(), geom.height(),
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        self.gradient_label.setPixmap(scaled)
        self.gradient_label.setGeometry(geom)

    def set_rotation(self, angle: int) -> None:
        if angle in (0, 90, 180, 270):
            with QMutexLocker(self._mutex):
                self.rotation = angle
                if DEBUG_BackgroundManager:
                    print(f"Rotation définie à {angle}°")

    def _on_frame_ready(self, qimg: QImage) -> None:
        pix = QPixmap.fromImage(qimg)
        with QMutexLocker(self._mutex):
            self.last_camera = pix
        self._update_view()

    def set_live(self) -> None:
        with QMutexLocker(self._mutex):
            self.current = 'live'
        self._update_view()

    def capture(self) -> None:
        with QMutexLocker(self._mutex):
            if self.last_camera:
                self.captured = QPixmap(self.last_camera)
            self.current = 'captured'

    def set_generated(self, qimage: QImage) -> None:
        with QMutexLocker(self._mutex):
            self.generated = QPixmap.fromImage(qimage)
            self.current = 'generated'
        self._update_view()

    def on_generate(self) -> None:
        img = QImage(640, 480, QImage.Format_RGB888)
        img.fill(Qt.red)
        self.set_generated(img)

    def clear(self) -> None:
        with QMutexLocker(self._mutex):
            self.captured = None
            self.generated = None
            self.current = 'live'
        self._update_view()

    def get_pixmap(self) -> QPixmap | None:
        with QMutexLocker(self._mutex):
            if self.current == 'generated' and self.generated:
                return self.generated
            if self.current == 'captured' and self.captured:
                return self.captured
            return self.last_camera

    def _update_view(self) -> None:
        """Actualise uniquement le contenu caméra, pas le gradient."""
        pix = self.get_pixmap()
        if pix:
            self._render_camera(pix)

    def _render_camera(self, pix: QPixmap) -> None:
        if pix is None:
            self.label.clear()
            return
        if self.rotation:
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

    def resize_event(self) -> None:
        """Doit être appelé lors du resize du parent pour ajuster gradient et vue."""
        self._resize_gradient()
        self._update_view()

    def update_background(self) -> None:
        """Alias: update du gradient et du flux caméra."""
        self.resize_event()

    def close(self) -> None:
        self.thread.stop()
        self.thread.wait()

    def get_background_image(self) -> QPixmap | None:
        return self.get_pixmap()

    def is_work(self, flag: bool) -> None:
        # TODO: Ajuster la résolution selon flag
        pass

