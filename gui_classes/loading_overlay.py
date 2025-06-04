from PySide6.QtWidgets import QWidget, QLabel 
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QMovie, QPainter, QColor

class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Configuration basique
        self.img_label = QLabel(self)
        self.img_label.setAlignment(Qt.AlignCenter)
        self._movie = QMovie("gui_template/load.gif")
        self._movie.setScaledSize(QSize(64, 64))
        self.img_label.setMovie(self._movie)
        self.img_label.setFixedSize(64, 64)

    def showEvent(self, event):
        super().showEvent(event)
        # Centre le GIF
        self.img_label.move(
            (self.width() - self.img_label.width()) // 2,
            (self.height() - self.img_label.height()) // 2
        )
        # Démarre l'animation
        if self._movie and not self._movie.isValid():
            self._movie.setFileName("gui_template/load.gif")
        if self._movie:
            self._movie.start()

    def hideEvent(self, event):
        if self._movie:
            self._movie.stop()
        super().hideEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 128))