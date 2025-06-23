from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import QObject, QMutex, Qt

class BackgroundManager(QObject):
    """
    Gère la source du fond d'écran pour l'application PhotoBooth.
    Priorité :
    1. Image générée (si existe)
    2. Capture (si existe)
    3. Caméra (si existe)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mutex = QMutex()
        self.generated_image = None  # QImage
        self.captured_image = None   # QImage
        self.camera_pixmap = None    # QPixmap
        self.current_source = None   # 'generated', 'capture', 'camera'

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

    def clear_all(self):
        self._mutex.lock()
        try:
            self.generated_image = None
            self.captured_image = None
            self.camera_pixmap = None
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
            return None
        finally:
            self._mutex.unlock()

    def get_source(self):
        return self.current_source



    def clear_scroll_overlay(self):
        """
        Détruit proprement l'overlay de scroll et le widget de scroll s'ils existent.
        """
        if hasattr(self, 'scroll_overlay') and self.scroll_overlay:
            self.scroll_overlay.hide()
            self.scroll_overlay.deleteLater()
            self.scroll_overlay = None
        if hasattr(self, 'scroll_widget') and self.scroll_widget:
            self.scroll_widget = None

    def start_scroll(self, parent, on_started=None):
        """
        Crée et affiche l'overlay de scroll animé. Appelle on_started() une fois prêt.
        """
        from gui_classes.scroll_widget import InfiniteScrollWidget
        from PySide6.QtWidgets import QVBoxLayout, QWidget
        self.clear_scroll_overlay()
        class ScrollOverlay(QWidget):
            def __init__(self, parent):
                super().__init__(parent)
                self.setAttribute(Qt.WA_TranslucentBackground)
                self.setStyleSheet("background: transparent;")
                self.setGeometry(0, 0, parent.width(), parent.height())
                self.lower()
                self.show()
            def resizeEvent(self, event):
                if self.parent():
                    self.setGeometry(0, 0, self.parent().width(), self.parent().height())
                super().resizeEvent(event)
        self.scroll_overlay = ScrollOverlay(parent)
        overlay_layout = QVBoxLayout(self.scroll_overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)
        self.scroll_widget = InfiniteScrollWidget(
            './gui_template/sleep_picture',
            scroll_speed=2,
            fps=60,
            margin_x=1,
            margin_y=1,
            angle=15
        )
        overlay_layout.addWidget(self.scroll_widget)
        self.scroll_widget.start()
        if on_started:
            on_started()

    def stop_scroll(self, set_view=None):
        """
        Met l'overlay de scroll au-dessus, appelle set_view() juste après, puis lance l'animation de fin du scroll.
        """
        if hasattr(self, 'scroll_overlay') and self.scroll_overlay:
            self.scroll_overlay.raise_()
        if set_view:
            set_view()
        if hasattr(self, 'scroll_widget') and self.scroll_widget:
            self.scroll_widget.begin_stop(stop_speed=6, on_finished=None)
        else:
            self.clear_scroll_overlay()

