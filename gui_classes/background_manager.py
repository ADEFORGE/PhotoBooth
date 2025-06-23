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
        with QMutexLocker(self._mutex):
            if self.generated_image:
                result = QPixmap.fromImage(self.generated_image)
            elif self.captured_image:
                result = QPixmap.fromImage(self.captured_image)
            else:
                result = self.camera_pixmap
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting get_background: return={result}")
        return result

    def get_source(self) -> str | None:
        """Inputs: None. Returns: current source key (str) or None."""
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Entering get_source: args={{}}")
        result = self.current_source
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting get_source: return={result}")
        return result

    def clear_scroll_overlay(self) -> None:
        """Inputs: None. Returns: None."""
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Entering clear_scroll_overlay: args={{}}")
        if getattr(self, 'scroll_overlay', None):
            self.scroll_overlay.hide()
            self.scroll_overlay.deleteLater()
            self.scroll_overlay = None
        if getattr(self, 'scroll_widget', None):
            self.scroll_widget = None
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting clear_scroll_overlay: return=None")

    def start_scroll(self, parent: QWidget, on_started=None) -> None:
        """Inputs: parent (QWidget), on_started (callable or None). Returns: None."""
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Entering start_scroll: args={{'parent':{parent}, 'on_started':{on_started}}}")
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
        layout = QVBoxLayout(self.scroll_overlay)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        from gui_classes.scroll_widget import InfiniteScrollWidget
        self.scroll_widget = InfiniteScrollWidget(
            './gui_template/sleep_picture',
            scroll_speed=2,
            fps=60,
            margin_x=1,
            margin_y=1,
            angle=15
        )
        layout.addWidget(self.scroll_widget)
        self.scroll_widget.start()
        if on_started:
            on_started()
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting start_scroll: return=None")

    def stop_scroll(self, set_view=None) -> None:
        """Inputs: set_view (callable or None). Returns: None."""
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Entering stop_scroll: args={{'set_view':{set_view}}}")
        if getattr(self, 'scroll_overlay', None):
            self.scroll_overlay.raise_()
        if set_view:
            set_view()
        if getattr(self, 'scroll_widget', None):
            self.scroll_widget.begin_stop(stop_speed=30, on_finished=None)
        else:
            self.clear_scroll_overlay()
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting stop_scroll: return=None")

