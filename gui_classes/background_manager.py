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
        if hasattr(self, 'gradient_label'):
            self.gradient_label = None
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Exiting clear_scroll_overlay: return=None")

    def start_scroll(self, parent: QWidget, on_started=None) -> None:
        """Inputs: parent (QWidget), on_started (callable or None). Returns: None."""
        if DEBUG_BackgroundManager:
            print(f"[DEBUG][BackgroundManager] Entering start_scroll: args={{'parent':{parent}, 'on_started':{on_started}}}")
        self.clear_scroll_overlay()
        from PySide6.QtGui import QPixmap
        from PySide6.QtWidgets import QLabel
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
        # Ajout du gradient overlay (Intro Screen) AU-DESSUS du scroll_widget, sans débordement (stretch)
        self.gradient_label = QLabel(self.scroll_overlay)
        self.gradient_label.setAttribute(Qt.WA_TranslucentBackground)
        self.gradient_label.setStyleSheet("background: transparent;")
        self.gradient_label.setGeometry(0, 0, parent.width(), parent.height())
        self.gradient_label.setPixmap(QPixmap("./gui_template/Gradient Intro Screen.png").scaled(self.gradient_label.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        self.gradient_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.gradient_label.raise_()  # S'assurer qu'il est au-dessus du scroll_widget
        self.gradient_label.show()
        def resize_gradient():
            self.gradient_label.setGeometry(0, 0, self.scroll_overlay.width(), self.scroll_overlay.height())
            pix = QPixmap("./gui_template/Gradient Intro Screen.png")
            self.gradient_label.setPixmap(pix.scaled(self.gradient_label.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        self.scroll_overlay.resizeEvent = lambda event: (resize_gradient(), ScrollOverlay.resizeEvent(self.scroll_overlay, event))
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

