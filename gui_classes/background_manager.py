from PySide6.QtGui import QPixmap, QImage, QPainter
from PySide6.QtCore import QObject, QMutex, Qt

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
        # print("[BG_MANAGER] __init__ called")
        self._mutex = QMutex()
        self.generated_image = None  # QImage
        self.captured_image = None   # QImage
        self.camera_pixmap = None    # QPixmap
        self.scroll_pixmap = None    # QPixmap
        self.current_source = None   # 'generated', 'capture', 'camera', 'scroll'
        self._gradient_cache = {}    # (path, QSize) -> QPixmap

    def set_generated_image(self, qimage):
        # print("[BG_MANAGER] set_generated_image called")
        self._mutex.lock()
        try:
            self.generated_image = qimage
            self.current_source = 'generated'
            # print("[BG_MANAGER] set_generated_image: source set to 'generated'")
        finally:
            self._mutex.unlock()

    def set_captured_image(self, qimage):
        # print("[BG_MANAGER] set_captured_image called")
        self._mutex.lock()
        try:
            self.captured_image = qimage
            self.current_source = 'capture'
            # print("[BG_MANAGER] set_captured_image: source set to 'capture'")
        finally:
            self._mutex.unlock()

    def set_camera_pixmap(self, pixmap):
        # print("[BG_MANAGER] set_camera_pixmap called")
        self._mutex.lock()
        try:
            self.camera_pixmap = pixmap
            self.current_source = 'camera'
            # print("[BG_MANAGER] set_camera_pixmap: source set to 'camera'")
        finally:
            self._mutex.unlock()

    def set_scroll_pixmap(self, pixmap):
        #print("[DEBUG][BGMANAGER] set_scroll_pixmap called")
        self._mutex.lock()
        try:
            self.scroll_pixmap = pixmap
            self.current_source = 'scroll'
            #print(f"[DEBUG][BGMANAGER] set_scroll_pixmap: source set to 'scroll'")
        finally:
            self._mutex.unlock()

    def clear_generated(self):
        # print("[BG_MANAGER] clear_generated called")
        self._mutex.lock()
        try:
            self.generated_image = None
            if self.captured_image is not None:
                self.current_source = 'capture'
            elif self.camera_pixmap is not None:
                self.current_source = 'camera'
            elif self.scroll_pixmap is not None:
                self.current_source = 'scroll'
            else:
                self.current_source = None
            # print(f"[BG_MANAGER] clear_generated: current_source={self.current_source}")
        finally:
            self._mutex.unlock()

    def clear_capture(self):
        # print("[BG_MANAGER] clear_capture called")
        self._mutex.lock()
        try:
            self.captured_image = None
            if self.generated_image is not None:
                self.current_source = 'generated'
            elif self.camera_pixmap is not None:
                self.current_source = 'camera'
            elif self.scroll_pixmap is not None:
                self.current_source = 'scroll'
            else:
                self.current_source = None
            # print(f"[BG_MANAGER] clear_capture: current_source={self.current_source}")
        finally:
            self._mutex.unlock()

    def clear_camera(self):
        # print("[BG_MANAGER] clear_camera called")
        self._mutex.lock()
        try:
            self.camera_pixmap = None
            if self.generated_image is not None:
                self.current_source = 'generated'
            elif self.captured_image is not None:
                self.current_source = 'capture'
            elif self.scroll_pixmap is not None:
                self.current_source = 'scroll'
            else:
                self.current_source = None
            # print(f"[BG_MANAGER] clear_camera: current_source={self.current_source}")
        finally:
            self._mutex.unlock()

    def clear_scroll(self):
        # print("[BG_MANAGER] clear_scroll called")
        self._mutex.lock()
        try:
            self.scroll_pixmap = None
            if self.generated_image is not None:
                self.current_source = 'generated'
            elif self.captured_image is not None:
                self.current_source = 'capture'
            elif self.camera_pixmap is not None:
                self.current_source = 'camera'
            else:
                self.current_source = None
            # print(f"[BG_MANAGER] clear_scroll: current_source={self.current_source}")
        finally:
            self._mutex.unlock()

    def _get_scaled_gradient(self, gradient_path, size):
        key = (gradient_path, size.width(), size.height())
        if key in self._gradient_cache:
            return self._gradient_cache[key]
        gradient = QPixmap(gradient_path)
        if not gradient.isNull():
            scaled = gradient.scaled(size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self._gradient_cache[key] = scaled
            return scaled
        return None

    def get_background(self):
        self._mutex.lock()
        try:
            background = None
            gradient_path = None
            if self.generated_image is not None:
                background = QPixmap.fromImage(self.generated_image)
                gradient_path = "gui_template/Gradient Camera Screen.png"
            elif self.captured_image is not None:
                background = QPixmap.fromImage(self.captured_image)
                gradient_path = "gui_template/Gradient Camera Screen.png"
            elif self.camera_pixmap is not None:
                background = self.camera_pixmap
                gradient_path = "gui_template/Gradient Camera Screen.png"
            elif self.scroll_pixmap is not None:
                background = self.scroll_pixmap
                gradient_path = "gui_template/Gradient Intro Screen.png"

            if background is not None and gradient_path is not None:
                result = QPixmap(background.size())
                result.fill(Qt.transparent)
                painter = QPainter(result)
                painter.drawPixmap(0, 0, background)
                gradient = self._get_scaled_gradient(gradient_path, background.size())
                if gradient is not None:
                    painter.drawPixmap(0, 0, gradient)
                painter.end()
                return result
            return None
        finally:
            self._mutex.unlock()

    def get_source(self):
        # print(f"[BG_MANAGER] get_source called: {self.current_source}")
        return self.current_source

    def clear_all(self):
        print("[DEBUG][BGMANAGER] clear_all called")
        # print("[BG_MANAGER] clear_all called")
        self._mutex.lock()
        try:
            self.generated_image = None
            self.captured_image = None
            self.camera_pixmap = None
            self.scroll_pixmap = None
            self.current_source = None
            # print("[BG_MANAGER] clear_all: all sources cleared")
            print("[DEBUG][BGMANAGER] clear_all: all sources cleared")
        finally:
            self._mutex.unlock()

    @staticmethod
    def set_scroll_fond(widget):
        print("[BGMANAGER][DEBUG] set_scroll_fond called for widget:", widget)
        import os
        from gui_classes.scrole import InfiniteScrollView
        from PySide6.QtCore import Qt
        images_folder = os.path.join(os.path.dirname(__file__), "../gui_template/sleep_picture")
        if not hasattr(widget, '_scroll_view') or widget._scroll_view is None:
            print("[BGMANAGER][DEBUG] Creating new InfiniteScrollView")
            widget._scroll_view = InfiniteScrollView(
                images_folder, scroll_speed=1, tilt_angle=30, fps=60,
                on_frame=lambda sv: BackgroundManager._update_scroll_background(widget, sv)
            )
            widget._scroll_view.resize(widget.size())
            widget._scroll_view._populate_scene()
            widget._scroll_view.setParent(widget)
            widget._scroll_view.setAttribute(Qt.WA_TransparentForMouseEvents)
            widget._scroll_view.setStyleSheet("background: transparent;")
            widget._scroll_view.hide()
        else:
            widget._scroll_view.setAttribute(Qt.WA_TransparentForMouseEvents)
            widget._scroll_view.setStyleSheet("background: transparent;")
            widget._scroll_view.hide()
        if widget._scroll_view and not widget._scroll_view.timer.isActive():
            print("[BGMANAGER][DEBUG] Starting scroll timer")
            widget._scroll_view.timer.start()
        # Met à jour le fond immédiatement
        print("[BGMANAGER][DEBUG] Updating scroll background")
        BackgroundManager._update_scroll_background(widget, widget._scroll_view)

    @staticmethod
    def _update_scroll_background(widget, scroll_view=None):
        print(f"[BGMANAGER][DEBUG] _update_scroll_background called for widget={widget} scroll_view={scroll_view}")
        if scroll_view is None and hasattr(widget, '_scroll_view'):
            scroll_view = widget._scroll_view
        if scroll_view:
            pixmap = scroll_view.grab()
            if hasattr(widget, 'background_manager'):
                print("[BGMANAGER][DEBUG] Setting scroll pixmap on background_manager")
                widget.background_manager.set_scroll_pixmap(pixmap)
            widget.update()
            print("[BGMANAGER][DEBUG] Widget updated after scroll background")

    @staticmethod
    def clear_scroll_fond(widget):
        print(f"[BGMANAGER][DEBUG] clear_scroll_fond called for widget={widget}")
        if hasattr(widget, '_scroll_view') and widget._scroll_view:
            if hasattr(widget._scroll_view, 'timer') and widget._scroll_view.timer.isActive():
                print("[BGMANAGER][DEBUG] Stopping scroll timer")
                widget._scroll_view.timer.stop()
            print("[BGMANAGER][DEBUG] Deleting scroll view")
            widget._scroll_view.deleteLater()
            widget._scroll_view = None

    @staticmethod
    def start_scroll_fond(widget):
        print(f"[BGMANAGER][DEBUG] start_scroll_fond called for widget={widget}")
        if hasattr(widget, '_scroll_view') and widget._scroll_view and hasattr(widget._scroll_view, 'timer'):
            if not widget._scroll_view.timer.isActive():
                print("[BGMANAGER][DEBUG] Starting scroll timer")
                widget._scroll_view.timer.start()

    @staticmethod
    def stop_scroll_fond(widget):
        print(f"[BGMANAGER][DEBUG] stop_scroll_fond called for widget={widget}")
        if hasattr(widget, '_scroll_view') and widget._scroll_view and hasattr(widget._scroll_view, 'timer'):
            if widget._scroll_view.timer.isActive():
                print("[BGMANAGER][DEBUG] Stopping scroll timer")
                widget._scroll_view.timer.stop()

    @staticmethod
    def end_scroll_animation(widget, on_finished=None):
        print(f"[BGMANAGER][DEBUG] end_scroll_animation called for widget={widget} on_finished={on_finished}")
        if hasattr(widget, 'fade_out_gradient'):
            widget.fade_out_gradient(1000)
        if hasattr(widget, '_scroll_view') and widget._scroll_view:
            # Show and raise the scroll view for the end animation, keep it transparent for mouse events
            widget._scroll_view.setAttribute(Qt.WA_TransparentForMouseEvents)
            widget._scroll_view.setStyleSheet("background: transparent;")
            widget._scroll_view.show()
            widget._scroll_view.raise_()
            if hasattr(widget._scroll_view, 'end_animation'):
                print("[BGMANAGER][DEBUG] Calling end_animation on scroll_view")
                widget._scroll_view.end_animation(on_finished=on_finished)
            else:
                print("[BGMANAGER][DEBUG] No end_animation on scroll_view, calling on_finished directement")
                if on_finished:
                    on_finished()
        else:
            print("[BGMANAGER][DEBUG] No _scroll_view, calling on_finished directement")
            if on_finished:
                on_finished()
