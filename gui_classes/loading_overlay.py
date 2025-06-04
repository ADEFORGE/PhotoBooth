from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt, QSize

class LoadingOverlay(QWidget):
    def __init__(self, parent=None, gif_path="gui_template/load.gif"):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.movie = QMovie(gif_path)
        self.movie.setScaledSize(QSize(400, 400))  # Doublé de 200 à 400
        self.label.setMovie(self.movie)
        self.movie.start()

        # Positionnement manuel du label au centre
        self.label.setGeometry(0, 0, 400, 400)  # Doublé de 200 à 400

    def update_overlay_geometry(self):
        if self.parentWidget():
            pw = self.parentWidget().width()
            ph = self.parentWidget().height()
            self.setGeometry(0, 0, pw, ph)
            # Centre le label
            x = (pw - 400) // 2  # Doublé de 200 à 400
            y = (ph - 400) // 2  # Doublé de 200 à 400
            self.label.setGeometry(x, y, 400, 400)  # Doublé de 200 à 400

    def showEvent(self, event):
        self.update_overlay_geometry()
        super().showEvent(event)
