# gui_classes/resultwidget.py
from PySide6.QtWidgets import QWidget, QLabel, QGridLayout, QSizePolicy, QApplication
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt

class LoadWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)        
        layout = QGridLayout(self)        

        self.load_animation_label = QLabel(alignment=Qt.AlignCenter)
        self.load_animation_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # Ne pas utiliser setScaledContents(True) pour éviter la déformation

        # Taille relative à l'écran
        screen = QApplication.primaryScreen()
        size = screen.size()
        w = int(size.width() * 0.2)
        h = int(size.height() * 0.2)
        self.load_animation_label.setMinimumSize(w, h)  # Minimum, pas fixe

        # Utiliser QMovie pour animer le GIF
        self.movie = QMovie("./gui_template/load.gif")
        self.load_animation_label.setMovie(self.movie)
        self.movie.start()

        # Centrer le label dans le layout
        layout.addWidget(self.load_animation_label, 0, 0, 1, 1, alignment=Qt.AlignCenter)

    def fct(self):
        return 
