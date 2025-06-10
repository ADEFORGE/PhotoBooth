from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import QObject

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
        self.generated_image = None  # QImage
        self.captured_image = None   # QImage
        self.camera_pixmap = None    # QPixmap
        self.scroll_pixmap = None    # QPixmap
        self.current_source = None   # 'generated', 'capture', 'camera', 'scroll'

    def set_generated_image(self, qimage):
        self.generated_image = qimage
        self.current_source = 'generated'

    def set_captured_image(self, qimage):
        self.captured_image = qimage
        self.current_source = 'capture'

    def set_camera_pixmap(self, pixmap):
        self.camera_pixmap = pixmap
        self.current_source = 'camera'

    def set_scroll_pixmap(self, pixmap):
        self.scroll_pixmap = pixmap
        self.current_source = 'scroll'

    def clear_generated(self):
        self.generated_image = None
        if self.captured_image is not None:
            self.current_source = 'capture'
        elif self.camera_pixmap is not None:
            self.current_source = 'camera'
        elif self.scroll_pixmap is not None:
            self.current_source = 'scroll'
        else:
            self.current_source = None

    def clear_capture(self):
        self.captured_image = None
        if self.generated_image is not None:
            self.current_source = 'generated'
        elif self.camera_pixmap is not None:
            self.current_source = 'camera'
        elif self.scroll_pixmap is not None:
            self.current_source = 'scroll'
        else:
            self.current_source = None

    def clear_camera(self):
        self.camera_pixmap = None
        if self.generated_image is not None:
            self.current_source = 'generated'
        elif self.captured_image is not None:
            self.current_source = 'capture'
        elif self.scroll_pixmap is not None:
            self.current_source = 'scroll'
        else:
            self.current_source = None

    def clear_scroll(self):
        self.scroll_pixmap = None
        if self.generated_image is not None:
            self.current_source = 'generated'
        elif self.captured_image is not None:
            self.current_source = 'capture'
        elif self.camera_pixmap is not None:
            self.current_source = 'camera'
        else:
            self.current_source = None

    def get_background(self):
        """
        Retourne l'objet à afficher comme fond (QImage ou QPixmap)
        """
        if self.generated_image is not None:
            return self.generated_image
        if self.captured_image is not None:
            return self.captured_image
        if self.camera_pixmap is not None:
            return self.camera_pixmap
        if self.scroll_pixmap is not None:
            return self.scroll_pixmap
        return None

    def get_source(self):
        return self.current_source

    def clear_all(self):
        self.generated_image = None
        self.captured_image = None
        self.camera_pixmap = None
        self.scroll_pixmap = None
        self.current_source = None
