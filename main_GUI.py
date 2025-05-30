from PySide6.QtWidgets import QWidget, QLabel, QGridLayout, QPushButton, QApplication, QSizePolicy
from PySide6.QtGui import QPixmap, QMovie, QImage
from PySide6.QtCore import Qt, QSize
from constante import LABEL_WIDTH_RATIO, LABEL_HEIGHT_RATIO, GRID_WIDTH
import sys

class MainGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhotoBooth Nouvelle Génération")

        # Layout principal
        self.grid = QGridLayout(self)
        
        # Label principal pour image/camera/gif
        self.display_label = QLabel(alignment=Qt.AlignCenter)
        self.display_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.display_label.setStyleSheet("background: transparent;")  # Pour bien voir la zone

        # Taille relative à l'écran
        screen = QApplication.primaryScreen()
        size = screen.size()
        w = int(size.width() * LABEL_WIDTH_RATIO)
        h = int(size.height() * LABEL_HEIGHT_RATIO)
        self.display_label.setMinimumSize(w, h)
        self.display_label.setMaximumSize(w, h)

        self.grid.addWidget(self.display_label, 0, 0, 1, GRID_WIDTH, alignment=Qt.AlignCenter)


    def show_image(self, qimage: QImage):
        pix = QPixmap.fromImage(qimage)
        self.display_label.setPixmap(pix.scaled(
            self.display_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def show_pixmap(self, pixmap: QPixmap):
        self.display_label.setPixmap(pixmap.scaled(
            self.display_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def show_gif(self, gif_path: str):
        movie = QMovie(gif_path)
        movie.start()  # Démarre le GIF pour avoir accès à sa taille réelle

        # Attendre que le GIF soit chargé pour obtenir la taille d'origine
        movie.jumpToFrame(0)
        gif_size = movie.currentImage().size()
        label_size = self.display_label.size()

        # Calcul du ratio pour garder les proportions
        gif_w, gif_h = gif_size.width(), gif_size.height()
        label_w, label_h = label_size.width(), label_size.height()
        if gif_w == 0 or gif_h == 0:
            scaled_w, scaled_h = label_w, label_h
        else:
            ratio = min(label_w / gif_w, label_h / gif_h)
            scaled_w = int(gif_w * ratio)
            scaled_h = int(gif_h * ratio)

        movie.setScaledSize(QSize(scaled_w, scaled_h))
        self.display_label.setMovie(movie)
        movie.start()

    def clear_display(self):
        self.display_label.clear()

    def clear_buttons(self):
        """À surcharger dans les classes filles si besoin."""
        pass

    def get_grid_width(self):
        return GRID_WIDTH

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainGUI()
    win.showFullScreen()
    sys.exit(app.exec())