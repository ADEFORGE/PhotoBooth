from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import QObject, QMutex, Qt, QTimer
from gui_classes.scroll_widget import InfiniteScrollWidget

class BackgroundManager(QObject):
    """
    Gère la source du fond d'écran pour l'application PhotoBooth.
    Priorité :
    1. Image générée (si existe)
    2. Capture (si existe)
    3. Caméra (si existe)
    4. Scroll (fond de veille)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mutex = QMutex()
        self.generated_image = None  # QImage
        self.captured_image = None   # QImage
        self.camera_pixmap = None    # QPixmap
        self.scroll_widget = None    # InfiniteScrollWidget
        self.current_source = None   # 'generated', 'capture', 'camera', 'scroll'

    # --- Set sources ---
    def set_generated_image(self, qimage):
        self._mutex.lock()
        try:
            self.generated_image = qimage
            self.current_source = 'generated'
        finally:
            self._mutex.unlock()

    def set_captured_image(self, qimage):
        self._mutex.lock()
        try:
            self.captured_image = qimage
            self.current_source = 'capture'
        finally:
            self._mutex.unlock()

    def set_camera_pixmap(self, pixmap):
        self._mutex.lock()
        try:
            self.camera_pixmap = pixmap
            self.current_source = 'camera'
        finally:
            self._mutex.unlock()

    def set_scroll(self, parent_widget, folder_path,
                   scroll_speed=1, fps=80, margin_x=1.5, margin_y=1.5, angle=15):
        """
        Initialise et affiche le fond scroll infini sur le widget cible.
        """
        if self.scroll_widget is None:
            self.scroll_widget = InfiniteScrollWidget(
                folder_path, scroll_speed, fps, margin_x, margin_y, angle, parent_widget)
            self.scroll_widget.setParent(parent_widget)
            self.scroll_widget.resize(parent_widget.size())
            self.scroll_widget.show()
            self.scroll_widget.start()
        else:
            self.scroll_widget.setSpeed(scroll_speed)
            self.scroll_widget.setAngle(angle)
        self.current_source = 'scroll'

    # --- Clear sources ---
    def clear_generated(self):
        self._mutex.lock()
        try:
            self.generated_image = None
            self._update_source()
        finally:
            self._mutex.unlock()

    def clear_capture(self):
        self._mutex.lock()
        try:
            self.captured_image = None
            self._update_source()
        finally:
            self._mutex.unlock()

    def clear_camera(self):
        self._mutex.lock()
        try:
            self.camera_pixmap = None
            self._update_source()
        finally:
            self._mutex.unlock()

    def clear_scroll(self):
        """Arrête et détruit le widget de scroll sans animation."""
        if self.scroll_widget:
            if self.scroll_widget.isRunning():
                self.scroll_widget.stop()
            self.scroll_widget.deleteLater()
            self.scroll_widget = None
            self._update_source()

    def clear_all(self):
        self._mutex.lock()
        try:
            self.generated_image = None
            self.captured_image = None
            self.camera_pixmap = None
            self.clear_scroll()
            self.current_source = None
        finally:
            self._mutex.unlock()

    def _update_source(self):
        if self.generated_image is not None:
            self.current_source = 'generated'
        elif self.captured_image is not None:
            self.current_source = 'capture'
        elif self.camera_pixmap is not None:
            self.current_source = 'camera'
        elif self.scroll_widget is not None:
            self.current_source = 'scroll'
        else:
            self.current_source = None

    # --- Background retrieval ---
    def get_background(self):
        self._mutex.lock()
        try:
            if self.generated_image:
                return QPixmap.fromImage(self.generated_image)
            if self.captured_image:
                return QPixmap.fromImage(self.captured_image)
            if self.camera_pixmap:
                return self.camera_pixmap
            if self.scroll_widget:
                return self.scroll_widget.grab()
            return None
        finally:
            self._mutex.unlock()

    def get_source(self):
        return self.current_source

    # --- Unset scroll with end animation ---
    def unset_scroll(self, on_finished=None, stop_speed=1):
        """
        Lance l'animation de fin du scroll, puis détruit le widget.
        """
        if self.scroll_widget:
            self.scroll_widget.begin_stop(stop_speed)
            # Calcul approximatif de la durée en ms puis callback
            # Nombre d'étapes = hauteur totale / vitesse
            total_steps = self.scroll_widget.scroll_tab.num_rows * self.scroll_widget.img_h
            interval = 1000 / self.scroll_widget.fps
            duration = int(total_steps * interval / stop_speed)
            QTimer.singleShot(duration, lambda: self.clear_scroll() or (on_finished and on_finished()))
        else:
            if on_finished:
                on_finished()
