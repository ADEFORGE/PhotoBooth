from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QLinearGradient
from PySide6.QtCore import QObject, QMutex, Qt, QPoint, QPointF

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
        print("[DEBUG][BGMANAGER] set_scroll_pixmap called")
        self._mutex.lock()
        try:
            self.scroll_pixmap = pixmap
            self.current_source = 'scroll'
            print(f"[DEBUG][BGMANAGER] set_scroll_pixmap: source set to 'scroll'")
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

    def apply_bottom_gradient(self, image):
        """
        Applique un dégradé vertical du bas vers le haut sur l'image.
        Le dégradé va de noir opaque en bas à transparent en haut,
        sur 20% de la hauteur de l'image depuis le bas.
        """
        if isinstance(image, QImage):
            pixmap = QPixmap.fromImage(image)
        elif isinstance(image, QPixmap):
            pixmap = image
        else:
            return None

        # Crée un pixmap avec la même taille
        result = QPixmap(pixmap.size())
        result.fill(Qt.transparent)

        # Dessine l'image originale
        painter = QPainter(result)
        painter.drawPixmap(0, 0, pixmap)

        # Calcule la zone de dégradé (20% de la hauteur depuis le bas)
        height = pixmap.height()
        gradient_height = int(height * 0.2)
        gradient_start = height - gradient_height

        # Crée le dégradé linéaire avec une opacité plus forte
        gradient = QLinearGradient(QPointF(0, gradient_start), QPointF(0, height))
        gradient.setColorAt(0, QColor(0, 0, 0, 0))  # Transparent en haut
        gradient.setColorAt(0.4, QColor(0, 0, 0, 100))  # Semi-transparent au milieu
        gradient.setColorAt(0.7, QColor(0, 0, 0, 200))  # Plus opaque
        gradient.setColorAt(1, QColor(0, 0, 0, 255))  # Complètement opaque en bas

        # Applique le dégradé
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.fillRect(0, gradient_start, pixmap.width(), gradient_height, gradient)
        painter.end()

        return result

    def get_background(self):
        self._mutex.lock()
        try:
            background = None
            if self.generated_image is not None:
                background = QPixmap.fromImage(self.generated_image)
            elif self.captured_image is not None:
                background = QPixmap.fromImage(self.captured_image)
            elif self.camera_pixmap is not None:
                background = self.camera_pixmap
            elif self.scroll_pixmap is not None:
                background = self.scroll_pixmap

            if background is not None:
                result = self.apply_bottom_gradient(background)
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
