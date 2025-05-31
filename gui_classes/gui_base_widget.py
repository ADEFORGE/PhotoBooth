from PySide6.QtWidgets import QWidget, QLabel, QGridLayout, QPushButton, QApplication, QSizePolicy, QHBoxLayout
from PySide6.QtGui import QPixmap, QMovie, QImage, QFont
from PySide6.QtCore import Qt, QSize
from constante import (
    LABEL_WIDTH_RATIO, LABEL_HEIGHT_RATIO, GRID_WIDTH,
    DISPLAY_LABEL_STYLE, BUTTON_STYLE, WINDOW_STYLE,
    APP_FONT_FAMILY, APP_FONT_SIZE,
    TITLE_LABEL_TEXT, TITLE_LABEL_STYLE,
    LOGO_SIZE  # <-- Ajoute ceci
)
import sys

class PhotoBoothBaseWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhotoBooth Nouvelle Génération")
        # Supprime ces deux lignes
        # self.setStyleSheet(WINDOW_STYLE)
        # self.setAutoFillBackground(True)
        
        self.setFont(QFont(APP_FONT_FAMILY, APP_FONT_SIZE))
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)

        # Ajout des logos en haut à gauche
        logo_layout = QHBoxLayout()
        logo1 = QLabel()
        logo2 = QLabel()
        pix1 = QPixmap("gui_template/logo1.png")
        pix2 = QPixmap("gui_template/logo2.png")
        logo1.setPixmap(pix1.scaled(LOGO_SIZE, LOGO_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo2.setPixmap(pix2.scaled(LOGO_SIZE, LOGO_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo1.setAttribute(Qt.WA_TranslucentBackground)
        logo2.setAttribute(Qt.WA_TranslucentBackground)
        logo1.setStyleSheet("background: rgba(0,0,0,0);")
        logo2.setStyleSheet("background: rgba(0,0,0,0);")
        logo_layout.addWidget(logo1)
        logo_layout.addWidget(logo2)
        logo_widget = QWidget()
        logo_widget.setLayout(logo_layout)
        logo_widget.setAttribute(Qt.WA_TranslucentBackground)
        logo_widget.setStyleSheet("background: rgba(0,0,0,0);")
        self.grid.addWidget(logo_widget, 0, 0, 1, 1, alignment=Qt.AlignLeft | Qt.AlignTop)

        # Titre (centré sur la première ligne)
        self.title_label = OutlinedLabel(TITLE_LABEL_TEXT)
        self.title_label.setStyleSheet("background: transparent;")
        self.grid.addWidget(self.title_label, 0, 1, 1, GRID_WIDTH - 1, alignment=Qt.AlignCenter)

        self.display_label = QLabel(alignment=Qt.AlignCenter)
        self.display_label.setStyleSheet(DISPLAY_LABEL_STYLE)
        self.display_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        screen = QApplication.primaryScreen()
        size = screen.size()
        w = int(size.width() * LABEL_WIDTH_RATIO)
        h = int(size.height() * LABEL_HEIGHT_RATIO)
        self.display_label.setMinimumSize(w, h)
        self.display_label.setMaximumSize(w, h)
        self.grid.addWidget(self.display_label, 1, 0, 1, GRID_WIDTH, alignment=Qt.AlignCenter)

        self.button_config = {}

        # AJOUTE CETTE LIGNE :
        self.setLayout(self.grid)

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
        """Supprime tous les widgets (boutons) sous la ligne 0."""
        for i in reversed(range(2, self.grid.rowCount())):  # Commence à 2 !
            for j in range(self.grid.columnCount()):
                item = self.grid.itemAtPosition(i, j)
                if item:
                    w = item.widget()
                    if w:
                        w.setParent(None)

    def get_grid_width(self):
        return GRID_WIDTH

    def setup_buttons_from_config(self):
        """Place automatiquement les boutons selon self.button_config, centrés sur chaque ligne.
        Si la méthode associée est 'none' ou None, le bouton n'est pas connecté."""
        self.clear_buttons()
        col_max = self.get_grid_width()
        btn_names = list(self.button_config.items())
        total_btns = len(btn_names)
        col, row = 0, 2
        i = 0
        while i < total_btns:
            btns_this_row = min(col_max, total_btns - i)
            start_col = (col_max - btns_this_row) // 2
            for j in range(btns_this_row):
                btn_name, method_name = btn_names[i + j]
                btn = QPushButton(btn_name)
                btn.setStyleSheet(BUTTON_STYLE)
                if method_name not in ("none", None):
                    if hasattr(self, method_name):
                        btn.clicked.connect(getattr(self, method_name))
                self.grid.addWidget(btn, row, start_col + j)
            i += btns_this_row
            row += 1

from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QPainterPath
from PySide6.QtCore import Qt

from constante import (
    TITLE_LABEL_TEXT, TITLE_LABEL_FONT_SIZE, TITLE_LABEL_FONT_FAMILY,
    TITLE_LABEL_BOLD, TITLE_LABEL_ITALIC, TITLE_LABEL_COLOR,
    TITLE_LABEL_BORDER_COLOR, TITLE_LABEL_BORDER_WIDTH
)

class OutlinedLabel(QLabel):
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self.outline_color = QColor(TITLE_LABEL_BORDER_COLOR)
        self.text_color = QColor(TITLE_LABEL_COLOR)
        self.outline_width = TITLE_LABEL_BORDER_WIDTH
        font = QFont(TITLE_LABEL_FONT_FAMILY, TITLE_LABEL_FONT_SIZE)
        font.setBold(TITLE_LABEL_BOLD)
        font.setItalic(TITLE_LABEL_ITALIC)
        self.setFont(font)
        self.setAlignment(Qt.AlignCenter)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = self.font()
        painter.setFont(font)
        rect = self.rect()
        text = self.text()

        # Centrage vertical/horizontal
        metrics = painter.fontMetrics()
        x = (rect.width() - metrics.horizontalAdvance(text)) // 2
        y = (rect.height() + metrics.ascent() - metrics.descent()) // 2

        # Chemin du texte
        path = QPainterPath()
        path.addText(x, y, font, text)

        # Contour
        pen = QPen(self.outline_color)
        pen.setWidth(self.outline_width)
        painter.setPen(pen)
        painter.drawPath(path)

        # Texte plein
        painter.setPen(self.text_color)
        painter.drawText(rect, Qt.AlignCenter, text)
