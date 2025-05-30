# gui_classes/resultwidget.py
from PySide6.QtWidgets import QWidget, QLabel, QGridLayout, QSizePolicy, QApplication
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt

class LoadWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)        
        layout = QGridLayout(self)        

        self.load_animation_label = QLabel(alignment=Qt.AlignCenter)
        # Définir une taille fixe pour le label (par exemple, 120x120 pixels)
        self.load_animation_label.setFixedSize(400, 400)

        # Charger et mettre à l'échelle le GIF
        self.movie = QMovie("./gui_template/load.gif")
        self.movie.setScaledSize(self.load_animation_label.size())
        self.load_animation_label.setMovie(self.movie)
        self.movie.start()

        layout.addWidget(self.load_animation_label, 0, 0, 1, 1, alignment=Qt.AlignCenter)

    def fct(self):
        return
