from PySide6.QtWidgets import (QWidget, QLabel, QGridLayout, QPushButton, 
                             QApplication, QSizePolicy, QHBoxLayout, QButtonGroup, QVBoxLayout)
from PySide6.QtGui import QPixmap, QMovie, QImage, QFont, QIcon, QPainter
from PySide6.QtCore import Qt, QSize
from gui_classes.more_info_box import InfoDialog
from gui_classes.rules_dialog import RulesDialog
from constante import (
    GRID_WIDTH, DISPLAY_LABEL_STYLE, BUTTON_STYLE,
    SPECIAL_BUTTON_STYLE, SPECIAL_BUTTON_NAMES, TITLE_LABEL_TEXT,
    LOGO_SIZE, INFO_BUTTON_SIZE, INFO_BUTTON_STYLE,
    GRID_VERTICAL_SPACING, GRID_HORIZONTAL_SPACING,
    GRID_LAYOUT_MARGINS, GRID_LAYOUT_SPACING,
    GRID_ROW_STRETCHES, DISPLAY_SIZE_RATIO,
    dico_styles, ICON_BUTTON_STYLE,  # <-- Ajout ici
    get_style_button_style, FIRST_BUTTON_STYLE, GENERIC_BUTTON_STYLE
)
import sys
import os
import unicodedata
import re

def normalize_btn_name(btn_name):
    # Enlève accents, met en minuscule, remplace espaces et caractères spéciaux par _
    name = btn_name.lower()
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    name = re.sub(r'[^a-z0-9]+', '_', name)
    name = name.strip('_')
    return name

class PhotoBoothBaseWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Utilise un layout vertical superposé
        self._background_pixmap = None
        self._background_movie = None
        self._background_qimage = None

        self.overlay_widget = QWidget(self)
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(*GRID_LAYOUT_MARGINS)
        self.overlay_layout.setSpacing(GRID_LAYOUT_SPACING)
        self.overlay_layout.setVerticalSpacing(GRID_VERTICAL_SPACING)
        self.overlay_layout.setHorizontalSpacing(GRID_HORIZONTAL_SPACING)

        self.setup_logos()
        self.setup_info_button()
        self.setup_rules_button()  # Ajout ici
        self.setup_title()
        self.button_config = {}
        self.first_buttons = []  # Nouvelle liste pour les boutons du haut
        self.setup_row_stretches()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.overlay_widget)
        self.overlay_widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    def resizeEvent(self, event):
        self.update()
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        # Détermine la source à afficher
        img = None
        if self._background_pixmap:
            img = self._background_pixmap
        elif self._background_qimage:
            img = QPixmap.fromImage(self._background_qimage)
        elif self._background_movie:
            img = self._background_movie.currentPixmap()
        # Si une image est présente, on la dessine avec gestion du ratio
        if img and not img.isNull():
            widget_w = self.width()
            widget_h = self.height()
            img_w = img.width()
            img_h = img.height()
            # Redimensionne l'image pour que la hauteur corresponde à la fenêtre
            scale = widget_h / img_h
            scaled_w = int(img_w * scale)
            scaled_h = widget_h
            scaled_img = img.scaled(scaled_w, scaled_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # Si l'image est plus large que la fenêtre, crop horizontalement
            if scaled_w > widget_w:
                x_offset = (scaled_w - widget_w) // 2
                target_rect = self.rect()
                source_rect = scaled_img.rect().adjusted(x_offset, 0, -x_offset, 0)
                painter.drawPixmap(target_rect, scaled_img, source_rect)
            else:
                # Si l'image est moins large, fond noir et image centrée
                painter.fillRect(self.rect(), Qt.black)
                x = (widget_w - scaled_w) // 2
                painter.drawPixmap(x, 0, scaled_w, scaled_h, scaled_img)
        else:
            # Si pas d'image, fond noir
            painter.fillRect(self.rect(), Qt.black)
        # ...ne pas appeler super().paintEvent(event) ici pour éviter d'effacer le fond...

    def show_image(self, qimage: QImage):
        self._background_qimage = qimage
        self._background_pixmap = None
        self._background_movie = None
        self.update()

    def show_pixmap(self, pixmap: QPixmap):
        self._background_pixmap = pixmap
        self._background_qimage = None
        self._background_movie = None
        self.update()

    def show_gif(self, gif_path: str):
        self._background_movie = QMovie(gif_path)
        self._background_movie.frameChanged.connect(self.update)
        self._background_movie.start()
        self._background_pixmap = None
        self._background_qimage = None
        self.update()

    def clear_display(self):
        self._background_pixmap = None
        self._background_qimage = None
        self._background_movie = None
        self.update()

    def clear_buttons(self):
        # Supprime tous les widgets (boutons) sous la ligne 0 dans overlay_layout
        for i in reversed(range(2, self.overlay_layout.rowCount())):
            for j in range(self.overlay_layout.columnCount()):
                item = self.overlay_layout.itemAtPosition(i, j)
                if item:
                    w = item.widget()
                    if w:
                        w.setParent(None)

    def get_grid_width(self):
        return GRID_WIDTH

    def setup_grid_layout(self):
        # Non utilisé, remplacé par overlay_layout
        pass

    def setup_logos(self):
        logo_layout = QVBoxLayout()  # <-- Changement ici : QVBoxLayout au lieu de QHBoxLayout
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
        self.overlay_layout.addWidget(logo_widget, 0, 0, 1, 1, alignment=Qt.AlignLeft | Qt.AlignTop)
        logo_widget.raise_()

    def setup_title(self):
        self.title_label = OutlinedLabel(TITLE_LABEL_TEXT)
        self.title_label.setStyleSheet("background: transparent;")
        self.overlay_layout.addWidget(self.title_label, 0, 0, 1, GRID_WIDTH, alignment=Qt.AlignCenter)

    def setup_row_stretches(self):
        for row, stretch in GRID_ROW_STRETCHES.items():
            row_index = {"title": 0, "display": 1, "buttons": 2}[row]
            self.overlay_layout.setRowStretch(row_index, stretch)

    def get_style_button_style(self, style_name):
        # Chemin de la texture
        texture_path = f"gui_template/styles_textures/{style_name}.png"
        if os.path.exists(texture_path):
            # Texture présente
            return (
                f"QPushButton {{"
                f"border: 2px solid black;"
                f"border-radius: 8px;"
                f"background-image: url('{texture_path}');"
                f"background-repeat: no-repeat;"
                f"background-position: center;"
                f"background-color: black;"
                f"color: white;"
                f"font-size: 18px;"
                f"font-weight: bold;"
                f"}}"
                f"QPushButton:hover {{"
                f"border: 2px solid gray;"
                f"}}"
                f"QPushButton:pressed {{"
                f"border: 4px solid white;"
                f"}}"
            )
        else:
            # Pas de texture, fond noir
            return (
                f"QPushButton {{"
                f"border: 2px solid black;"
                f"border-radius: 8px;"
                f"background-color: black;"
                f"color: white;"
                f"font-size: 18px;"
                f"font-weight: bold;"
                f"}}"
                f"QPushButton:hover {{"
                f"border: 2px solid gray;"
                f"}}"
                f"QPushButton:pressed {{"
                f"border: 4px solid white;"
                f"}}"
            )

    def get_icon_button_style(self):
        # Rond, gris transparent, bordures dynamiques
        return (
            f"QPushButton {{"
            f"background-color: rgba(180,180,180,0.5);"
            f"border: 2px solid #888;"
            f"border-radius: 24px;"  # Pour bouton rond, taille fixée plus bas
            f"min-width: 48px; min-height: 48px;"
            f"max-width: 48px; max-height: 48px;"
            f"font-size: 22px;"
            f"color: white;"
            f"font-weight: bold;"
            f"}}"
            f"QPushButton:hover {{"
            f"border: 2.5px solid white;"
            f"}}"
            f"QPushButton:pressed {{"
            f"border: 3px solid black;"
            f"}}"
        )

    def _create_button(self, btn_name, method_info):
        btn = QPushButton()
        icon_name = normalize_btn_name(btn_name)
        icon_path = f"gui_template/btn_icons/{icon_name}.png"
        icon = QIcon(icon_path) if os.path.exists(icon_path) else None

        # Style pour bouton de style (dico_styles)
        if btn_name in dico_styles:
            btn.setCheckable(True)
            btn.setStyleSheet(get_style_button_style(btn_name))
            btn.setMinimumSize(80, 80)
            btn.setMaximumSize(120, 120)
            self.button_group.addButton(btn)
            btn.clicked.connect(lambda checked, name=btn_name: 
                self.on_toggle(checked, name) if hasattr(self, 'on_toggle') else None)
            if icon:
                btn.setIcon(icon)
                btn.setIconSize(QSize(40, 40))  # Taille réduite de l'icône style
                btn.setText("")
            else:
                btn.setText(btn_name)
        else:
            btn.setStyleSheet(GENERIC_BUTTON_STYLE)
            btn.setFixedSize(48, 48)
            if icon:
                btn.setIcon(icon)
                btn.setIconSize(QSize(28, 28))  # Taille réduite de l'icône générique
                btn.setText("")
            else:
                btn.setText(btn_name)
            if isinstance(method_info, tuple):
                method_name, is_toggle = method_info
                if is_toggle:
                    btn.setCheckable(True)
                    self.button_group.addButton(btn)
                    btn.clicked.connect(lambda checked, name=btn_name: 
                        self.on_toggle(checked, name) if hasattr(self, 'on_toggle') else None)
            else:
                method_name = method_info
                if method_name not in ("none", None) and hasattr(self, method_name):
                    btn.clicked.connect(getattr(self, method_name))
        return btn

    def setup_buttons_from_config(self):
        self.clear_buttons()
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        col_max = self.get_grid_width()

        # --- Placement des boutons de first_buttons sur la première ligne de boutons (row=2) ---
        row = 2
        if hasattr(self, "first_buttons") and self.first_buttons:
            btn_names = list(self.first_buttons.items()) if isinstance(self.first_buttons, dict) else list(self.first_buttons)
            total_first = len(btn_names)
            btns_this_row = min(col_max, total_first)
            start_col = (col_max - btns_this_row) // 2
            skip_central = btns_this_row % 2 == 0
            central_col = col_max // 2 if skip_central else -1
            col = start_col
            for j in range(btns_this_row):
                if skip_central and col == central_col:
                    col += 1
                btn_name, method_info = btn_names[j]
                btn = self._create_button(btn_name, method_info)
                self.overlay_layout.addWidget(btn, row, col, alignment=Qt.AlignHCenter)
                col += 1
            row += 1

        # --- Placement des autres boutons comme avant, à partir de row ---
        btn_names = list(self.button_config.items())
        total_btns = len(btn_names)
        i = 0
        while i < total_btns:
            btns_this_row = min(col_max, total_btns - i)
            start_col = (col_max - btns_this_row) // 2
            skip_central = btns_this_row % 2 == 0
            central_col = col_max // 2 if skip_central else -1
            col = start_col
            for j in range(btns_this_row):
                if skip_central and col == central_col:
                    col += 1
                btn_name, method_info = btn_names[i + j]
                btn = self._create_button(btn_name, method_info)
                self.overlay_layout.addWidget(btn, row, col, alignment=Qt.AlignHCenter)
                col += 1
            i += btns_this_row
            row += 1

    def setup_info_button(self):
        info_btn = QPushButton()
        info_btn.setStyleSheet(ICON_BUTTON_STYLE)
        icon = QPixmap("gui_template/moreinfo.png")
        info_btn.setIcon(QIcon(icon))
        info_btn.setIconSize(QSize(24, 24))  # Taille réduite de l'icône info
        info_btn.setFixedSize(INFO_BUTTON_SIZE + 16, INFO_BUTTON_SIZE + 16)
        info_btn.clicked.connect(self.show_info_dialog)
        self.overlay_layout.addWidget(info_btn, 0, GRID_WIDTH-1, 1, 1, alignment=Qt.AlignRight | Qt.AlignTop)
        info_btn.raise_()
        self._info_btn = info_btn  # Pour positionner le bouton Rules juste en dessous

    def setup_rules_button(self):
        rules_btn = QPushButton()
        rules_btn.setStyleSheet(ICON_BUTTON_STYLE)
        rules_btn.setFixedSize(INFO_BUTTON_SIZE + 16, INFO_BUTTON_SIZE + 16)
        rules_icon = QPixmap("gui_template/rule_ico.png")
        rules_btn.setIcon(QIcon(rules_icon))
        rules_btn.setIconSize(QSize(24, 24))  # Taille réduite de l'icône rules
        rules_btn.clicked.connect(self.show_rules_dialog)
        # Place juste en dessous du bouton info
        self.overlay_layout.addWidget(rules_btn, 1, GRID_WIDTH-1, 1, 1, alignment=Qt.AlignRight | Qt.AlignTop)
        self._rules_btn = rules_btn

    def show_info_dialog(self):
        dialog = InfoDialog(self)
        dialog.exec()

    def show_rules_dialog(self):
        dialog = RulesDialog(self)
        dialog.exec()

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
        metrics = painter.fontMetrics()
        x = (rect.width() - metrics.horizontalAdvance(text)) // 2
        y = (rect.height() + metrics.ascent() - metrics.descent()) // 2
        path = QPainterPath()
        path.addText(x, y, font, text)
        pen = QPen(self.outline_color)
        pen.setWidth(self.outline_width)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.setPen(self.text_color)
        painter.drawText(rect, Qt.AlignCenter, text)
