from PySide6.QtWidgets import (QWidget, QLabel, QGridLayout, QPushButton, 
                             QApplication, QSizePolicy, QHBoxLayout, QButtonGroup)  # Ajoute QButtonGroup
from PySide6.QtGui import QPixmap, QMovie, QImage, QFont
from PySide6.QtCore import Qt, QSize
from constante import (
    GRID_WIDTH,
    DISPLAY_LABEL_STYLE, BUTTON_STYLE,
    TITLE_LABEL_TEXT,LOGO_SIZE,
    GRID_VERTICAL_SPACING, GRID_HORIZONTAL_SPACING,
    GRID_LAYOUT_MARGINS, GRID_LAYOUT_SPACING,
    GRID_ROW_STRETCHES, DISPLAY_SIZE_RATIO
)
import sys

class PhotoBoothBaseWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.grid = QGridLayout(self)
        self.setup_grid_layout()
        self.setup_logos()
        self.setup_title()
        self.setup_display()
        self.button_config = {}
        self.setup_row_stretches()
        self.setLayout(self.grid)

    def setup_grid_layout(self):
        """Configure les marges et l'espacement du grid layout."""
        self.grid.setContentsMargins(*GRID_LAYOUT_MARGINS)
        self.grid.setSpacing(GRID_LAYOUT_SPACING)
        self.grid.setVerticalSpacing(GRID_VERTICAL_SPACING)
        self.grid.setHorizontalSpacing(GRID_HORIZONTAL_SPACING)

    def setup_logos(self):
        """Place les logos en haut à gauche."""
        logo_layout = QHBoxLayout()
        logo1 = QLabel()
        logo2 = QLabel()
        
        for logo, path in [(logo1, "gui_template/logo1.png"), (logo2, "gui_template/logo2.png")]:
            pix = QPixmap(path)
            logo.setPixmap(pix.scaled(LOGO_SIZE, LOGO_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo.setAttribute(Qt.WA_TranslucentBackground)
            logo.setStyleSheet("background: rgba(0,0,0,0);")
            logo_layout.addWidget(logo)

        logo_widget = QWidget()
        logo_widget.setLayout(logo_layout)
        logo_widget.setAttribute(Qt.WA_TranslucentBackground)
        logo_widget.setStyleSheet("background: rgba(0,0,0,0);")
        # Force les logos à rester au-dessus du titre
        self.grid.addWidget(logo_widget, 0, 0, 1, 1, alignment=Qt.AlignLeft | Qt.AlignTop)
        logo_widget.raise_()  # Ajoute cette ligne pour mettre les logos au premier plan

    def setup_title(self):
        """Configure et place le titre."""
        self.title_label = OutlinedLabel(TITLE_LABEL_TEXT)
        self.title_label.setStyleSheet("background: transparent;")
        # Utilise toute la largeur du grid (0 à GRID_WIDTH)
        self.grid.addWidget(self.title_label, 0, 0, 1, GRID_WIDTH, alignment=Qt.AlignCenter)

    def setup_display(self):
        """Configure et place la zone d'affichage principale."""
        self.display_label = QLabel(alignment=Qt.AlignCenter)
        self.display_label.setStyleSheet(DISPLAY_LABEL_STYLE)
        self.display_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        screen = QApplication.primaryScreen()
        size = screen.size()
        w = int(size.width() * DISPLAY_SIZE_RATIO[0])
        h = int(size.height() * DISPLAY_SIZE_RATIO[1])
        self.display_label.setFixedSize(w, h)
        
        self.grid.addWidget(self.display_label, 1, 0, 1, GRID_WIDTH, alignment=Qt.AlignCenter)

    def setup_row_stretches(self):
        """Configure les proportions des lignes."""
        for row, stretch in GRID_ROW_STRETCHES.items():
            row_index = {"title": 0, "display": 1, "buttons": 2}[row]
            self.grid.setRowStretch(row_index, stretch)

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
        """Place automatiquement les boutons selon self.button_config."""
        self.clear_buttons()
        # Crée un groupe de boutons pour gérer l'exclusivité
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)  # Un seul bouton peut être checked à la fois
        
        col_max = self.get_grid_width()
        btn_names = list(self.button_config.items())
        total_btns = len(btn_names)
        col, row = 0, 2
        i = 0
        while i < total_btns:
            btns_this_row = min(col_max, total_btns - i)
            start_col = (col_max - btns_this_row) // 2
            for j in range(btns_this_row):
                btn_name, method_info = btn_names[i + j]
                btn = QPushButton(btn_name)
                btn.setStyleSheet(BUTTON_STYLE)
                
                # Gestion des boutons toggle
                if isinstance(method_info, tuple):
                    method_name, is_toggle = method_info
                    if is_toggle:
                        btn.setCheckable(True)
                        self.button_group.addButton(btn)  # Ajoute le bouton au groupe
                        btn.clicked.connect(lambda checked, name=btn_name: 
                            self.on_toggle(checked, name) if hasattr(self, 'on_toggle') else None)
                else:
                    method_name = method_info
                    if method_name not in ("none", None) and hasattr(self, method_name):
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
