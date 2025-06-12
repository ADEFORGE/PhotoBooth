from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import QObject, QMutex

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
        # print("[BG_MANAGER] set_scroll_pixmap called")
        self._mutex.lock()
        try:
            self.scroll_pixmap = pixmap
            self.current_source = 'scroll'
            # print("[BG_MANAGER] set_scroll_pixmap: source set to 'scroll'")
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

    def get_background(self):
        # print("[BG_MANAGER] get_background called")
        self._mutex.lock()
        try:
            if self.generated_image is not None:
                # print("[BG_MANAGER] get_background: returning generated_image")
                return self.generated_image
            if self.captured_image is not None:
                # print("[BG_MANAGER] get_background: returning captured_image")
                return self.captured_image
            if self.camera_pixmap is not None:
                # print("[BG_MANAGER] get_background: returning camera_pixmap")
                return self.camera_pixmap
            if self.scroll_pixmap is not None:
                # print("[BG_MANAGER] get_background: returning scroll_pixmap")
                return self.scroll_pixmap
            # print("[BG_MANAGER] get_background: returning None")
            return None
        finally:
            self._mutex.unlock()

    def get_source(self):
        # print(f"[BG_MANAGER] get_source called: {self.current_source}")
        return self.current_source

    def clear_all(self):
        # print("[BG_MANAGER] clear_all called")
        self._mutex.lock()
        try:
            self.generated_image = None
            self.captured_image = None
            self.camera_pixmap = None
            self.scroll_pixmap = None
            self.current_source = None
            # print("[BG_MANAGER] clear_all: all sources cleared")
        finally:
            self._mutex.unlock()
