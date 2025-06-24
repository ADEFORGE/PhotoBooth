from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import QObject, QMutex, QMutexLocker, Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

DEBUG_BackgroundManager = False

class BackgroundManager(QObject):
    def __init__(self, parent=None) -> None:
        """Inputs: parent (QObject or None). Returns: None."""
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Entering __init__: args={{'parent':{parent}}}")
        super().__init__(parent)
        self._mutex = QMutex()
        self.generated_image: QImage | None = None
        self.captured_image: QImage | None = None
        self.camera_pixmap: QPixmap | None = None
        self.current_source: str | None = None
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting __init__: return=None")

    def set_generated_image(self, qimage: QImage) -> None:
        """Inputs: qimage (QImage). Returns: None."""
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Entering set_generated_image: args={{'qimage':{qimage}}}")
        with QMutexLocker(self._mutex):
            self.generated_image = qimage
            self.current_source = 'generated'
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting set_generated_image: return=None")

    def set_captured_image(self, qimage: QImage) -> None:
        """Inputs: qimage (QImage). Returns: None."""
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Entering set_captured_image: args={{'qimage':{qimage}}}")
        with QMutexLocker(self._mutex):
            self.captured_image = qimage
            self.current_source = 'capture'
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting set_captured_image: return=None")

    def set_camera_pixmap(self, pixmap: QPixmap) -> None:
        """Inputs: pixmap (QPixmap). Returns: None."""
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Entering set_camera_pixmap: args={{'pixmap':{pixmap}}}")
        with QMutexLocker(self._mutex):
            self.camera_pixmap = pixmap
            self.current_source = 'camera'
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting set_camera_pixmap: return=None")

    def clear_generated(self) -> None:
        """Inputs: None. Returns: None."""
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Entering clear_generated: args={{}}")
        with QMutexLocker(self._mutex):
            self.generated_image = None
            self._update_source()
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting clear_generated: return=None")

    def clear_capture(self) -> None:
        """Inputs: None. Returns: None."""
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Entering clear_capture: args={{}}")
        with QMutexLocker(self._mutex):
            self.captured_image = None
            self._update_source()
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting clear_capture: return=None")

    def clear_camera(self) -> None:
        """Inputs: None. Returns: None."""
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Entering clear_camera: args={{}}")
        with QMutexLocker(self._mutex):
            self.camera_pixmap = None
            self._update_source()
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting clear_camera: return=None")

    def clear_all(self) -> None:
        """Inputs: None. Returns: None."""
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Entering clear_all: args={{}}")
        with QMutexLocker(self._mutex):
            self.generated_image = None
            self.captured_image = None
            self.camera_pixmap = None
            self.current_source = None
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting clear_all: return=None")

    def _update_source(self) -> None:
        """Inputs: None. Returns: None."""
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Entering _update_source: args={{}}")
        if self.generated_image is not None:
            self.current_source = 'generated'
        elif self.captured_image is not None:
            self.current_source = 'capture'
        elif self.camera_pixmap is not None:
            self.current_source = 'camera'
        else:
            self.current_source = None
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting _update_source: return=None")

    def get_background(self) -> QPixmap | None:
        """Inputs: None. Returns: QPixmap or None."""
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Entering get_background: args={{}}")
        from PySide6.QtGui import QPixmap, QPainter
        from PySide6.QtCore import Qt
        base_pixmap = None
        with QMutexLocker(self._mutex):
            if self.generated_image:
                base_pixmap = QPixmap.fromImage(self.generated_image)
            elif self.captured_image:
                base_pixmap = QPixmap.fromImage(self.captured_image)
            else:
                base_pixmap = self.camera_pixmap
        # Appliquer le gradient Camera Screen si ce n'est pas le scroll overlay
        if base_pixmap is not None:
            gradient_path = "./gui_template/Gradient Camera Screen.png"
            gradient_pix = QPixmap(gradient_path)
            if not gradient_pix.isNull():
                result = QPixmap(base_pixmap.size())
                result.fill(Qt.transparent)
                painter = QPainter(result)
                painter.drawPixmap(0, 0, base_pixmap)
                painter.setOpacity(1.0)
                painter.drawPixmap(0, 0, gradient_pix.scaled(base_pixmap.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
                painter.end()
                base_pixmap = result
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting get_background: return={base_pixmap}")
        return base_pixmap

    def get_source(self) -> str | None:
        """Inputs: None. Returns: current source key (str) or None."""
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Entering get_source: args={{}}")
        result = self.current_source
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting get_source: return={result}")
        return result

    def create_scroll_overlay(self, parent, on_created=None):
        """Crée l'overlay de scroll si non existant, puis callback."""
        if getattr(self, 'scroll_overlay', None) is None:
            from PySide6.QtWidgets import QVBoxLayout
            class ScrollOverlay(QWidget):
                def __init__(self, parent):
                    super().__init__(parent)
                    self.setAttribute(Qt.WA_TranslucentBackground)
                    self.setStyleSheet("background: transparent;")
                    self.setGeometry(0, 0, parent.width(), parent.height())
                    self.hide()
                def resizeEvent(self, event):
                    if self.parent():
                        self.setGeometry(0, 0, self.parent().width(), self.parent().height())
                    super().resizeEvent(event)
            self.scroll_overlay = ScrollOverlay(parent)
            layout = QVBoxLayout(self.scroll_overlay)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            from gui_classes.scroll_widget import InfiniteScrollWidget
            self.scroll_widget = InfiniteScrollWidget(
                './gui_template/sleep_picture',
                scroll_speed=2,
                fps=80,
                margin_x=1,
                margin_y=1,
                angle=15
            )
            layout.addWidget(self.scroll_widget)
        if on_created:
            on_created()

    def raise_scroll_overlay(self, on_raised=None):
        if getattr(self, 'scroll_overlay', None):
            self.scroll_overlay.raise_()
        if on_raised:
            on_raised()

    def lower_scroll_overlay(self, on_lowered=None):
        if getattr(self, 'scroll_overlay', None):
            self.scroll_overlay.lower()
        if on_lowered:
            on_lowered()

    def start_scroll_animation(self, stop_speed=30, on_finished=None):
        if getattr(self, 'scroll_widget', None):
            self.scroll_widget.begin_stop(stop_speed=stop_speed, on_finished=on_finished)
        else:
            if on_finished:
                on_finished()

    def clean_scroll_overlay(self, on_cleaned=None):
        if getattr(self, 'scroll_widget', None):
            self.scroll_widget.clear()
        if on_cleaned:
            on_cleaned()

    def clear_scroll_overlay(self, on_cleared=None):
        if getattr(self, 'scroll_overlay', None):
            self.scroll_overlay.hide()
            self.scroll_overlay.deleteLater()
            self.scroll_overlay = None
        self.scroll_widget = None
        if hasattr(self, 'gradient_label'):
            self.gradient_label = None
        if on_cleared:
            on_cleared()

    def hide_scroll_overlay(self, on_hidden=None):
        if getattr(self, 'scroll_overlay', None) and self.scroll_overlay.isVisible():
            self.scroll_overlay.hide()
        if on_hidden:
            on_hidden()

    def show_scroll_overlay(self, on_shown=None):
        if getattr(self, 'scroll_overlay', None):
            if not self.scroll_overlay.isVisible():
                self.scroll_overlay.show()
            # Démarre l'animation si le widget existe et n'est pas déjà en cours
            if getattr(self, 'scroll_widget', None):
                if hasattr(self.scroll_widget, 'isRunning'):
                    running = self.scroll_widget.isRunning()
                else:
                    running = False
                if not running:
                    self.scroll_widget.start()
                    if DEBUG_BackgroundManager:
                        print("[DEBUG][BackgroundManager] show_scroll_overlay: scroll_widget.start() called")
        if on_shown:
            on_shown()

