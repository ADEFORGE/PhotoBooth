from PySide6.QtWidgets import (QWidget, QLabel, QGridLayout, QPushButton, 
                             QApplication, QSizePolicy, QHBoxLayout, QButtonGroup, QVBoxLayout)
from PySide6.QtGui import QPixmap, QMovie, QImage, QFont, QIcon, QPainter
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, Property, QElapsedTimer, QThread, Signal, QObject
import cv2  # Ajout de l'import manquant
from gui_classes.image_utils import ImageUtils
from comfy_classes.comfy_class_API_test_GUI import ImageGeneratorAPIWrapper
from gui_classes.loading_overlay import LoadingOverlay

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

class GenerationWorker(QObject):
    finished = Signal(QImage)  # QImage prêt à afficher

    def __init__(self, style, input_image=None, parent=None):
        super().__init__(parent)
        self.style = style
        self.generator = ImageGeneratorAPIWrapper()
        self.input_image = input_image  # QImage

    def run(self):
        if self.input_image is not None:
            arr = ImageUtils.qimage_to_cv(self.input_image)
            cv2.imwrite("../ComfyUI/input/input.png", arr)
        self.generator.set_style(self.style)
        self.generator.generate_image()
        images = self.generator.get_image_paths()
        if images:
            img = cv2.imread(images[0])
            qimg = ImageUtils.cv_to_qimage(img)
            qimg = qimg.scaled(1200, 1200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.finished.emit(qimg)
        else:
            self.finished.emit(QImage())

class PhotoBoothBaseWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._worker = None
        self._generation_in_progress = False
        self.loading_overlay = None
        self.selected_style = None
        self.generated_image = None
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
        self.setup_title()
        self.button_config = {}
        self.first_buttons = []  # Nouvelle liste pour les boutons du haut
        self.setup_row_stretches()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.overlay_widget)
        self.overlay_widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        # Supprimer toute gestion d'opacité/animation pour éviter de masquer la caméra
        # self._opacity = 0.0
        # self._fade_animation = QPropertyAnimation(self, b"opacity", self)
        # self._fade_animation.setDuration(300)
        # self._fade_animation.setStartValue(0.0)
        # self._fade_animation.setEndValue(1.0)

    def resizeEvent(self, event):
        self.update()
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        # painter.setOpacity(self._opacity)  # SUPPRIMER l'opacité

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
        # Redimensionne pour limiter la taille mémoire
        if qimage and not qimage.isNull():
            qimage = qimage.scaled(1200, 1200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
                        print(f"[CLEANUP] Suppression bouton {w}")
                        w.setParent(None)
        import objgraph
        objgraph.show_most_common_types(limit=10)

    def get_grid_width(self):
        return GRID_WIDTH

    def setup_grid_layout(self):
        # Non utilisé, remplacé par overlay_layout
        pass

    def setup_logos(self):
        # Place les logos et les deux boutons (info/rules) dans un layout horizontal aligné en haut
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(10)

        # Logos à gauche (vertical)
        logo_layout = QVBoxLayout()
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
        top_bar.addWidget(logo_widget, alignment=Qt.AlignLeft | Qt.AlignTop)

        # Espace au centre (expansif)
        top_bar.addStretch(1)

        # Boutons info/rules à droite (vertical)
        btn_layout = QVBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)

        # Bouton info
        info_btn = QPushButton()
        info_btn.setStyleSheet(ICON_BUTTON_STYLE)
        icon = QPixmap("gui_template/moreinfo.png")
        info_btn.setIcon(QIcon(icon))
        info_btn.setIconSize(QSize(INFO_BUTTON_SIZE, INFO_BUTTON_SIZE))
        info_btn.setFixedSize(INFO_BUTTON_SIZE + 16, INFO_BUTTON_SIZE + 16)
        info_btn.clicked.connect(self.show_info_dialog)
        info_btn.raise_()
        self._info_btn = info_btn

        # Bouton rules
        rules_btn = QPushButton()
        rules_btn.setStyleSheet(ICON_BUTTON_STYLE)
        rules_btn.setFixedSize(INFO_BUTTON_SIZE + 16, INFO_BUTTON_SIZE + 16)
        rules_icon = QPixmap("gui_template/rule_ico.png")
        rules_btn.setIcon(QIcon(rules_icon))
        rules_btn.setIconSize(QSize(INFO_BUTTON_SIZE, INFO_BUTTON_SIZE))
        rules_btn.clicked.connect(self.show_rules_dialog)
        self._rules_btn = rules_btn

        btn_layout.addWidget(info_btn, alignment=Qt.AlignRight | Qt.AlignTop)
        btn_layout.addWidget(rules_btn, alignment=Qt.AlignRight | Qt.AlignTop)
        btn_layout.addStretch(1)
        btn_widget = QWidget()
        btn_widget.setLayout(btn_layout)
        btn_widget.setAttribute(Qt.WA_TranslucentBackground)
        btn_widget.setStyleSheet("background: rgba(0,0,0,0);")
        top_bar.addWidget(btn_widget, alignment=Qt.AlignRight | Qt.AlignTop)

        # Place le top_bar sur la première ligne de la grille, sur toute la largeur
        container = QWidget()
        container.setLayout(top_bar)
        container.setAttribute(Qt.WA_TranslucentBackground)
        container.setStyleSheet("background: rgba(0,0,0,0);")
        self.overlay_layout.addWidget(container, 0, 0, 1, GRID_WIDTH)

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
                btn.setIconSize(btn.size())
                btn.setText("")  # Pas de texte si icône
            else:
                btn.setText(btn_name)
        else:
            btn.setStyleSheet(GENERIC_BUTTON_STYLE)
            btn.setFixedSize(48, 48)
            if icon:
                btn.setIcon(icon)
                btn.setIconSize(btn.size())
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

    def show_info_dialog(self):
        dialog = InfoDialog(self)
        dialog.exec()

    def show_rules_dialog(self):
        dialog = RulesDialog(self)
        dialog.exec()

    def profile_slot(self, func, *args, **kwargs):
        timer = QElapsedTimer()
        timer.start()
        result = func(*args, **kwargs)
        elapsed_ms = timer.elapsed()
        print(f"[PROFILE] {func.__name__} executed in {elapsed_ms} ms")
        return result

    def __del__(self):
        print(f"[DEL] SaveAndSettingWidget détruit: {id(self)}")
        if hasattr(self, 'button_group'):
            for btn in self.button_group.buttons():
                try:
                    btn.clicked.disconnect()
                except Exception:
                    pass
        if hasattr(self, "_worker") and self._worker:
            try:
                self._worker.finished.disconnect()
            except Exception:
                pass

    def _ensure_overlay(self):
        """Assure qu'un overlay valide existe"""
        if not hasattr(self, 'loading_overlay') or self.loading_overlay is None:
            self.loading_overlay = LoadingOverlay(self)
            self.loading_overlay.resize(self.size())
        return self.loading_overlay

    def show_loading(self):
        """Affiche l'overlay de chargement"""
        overlay = self._ensure_overlay()
        overlay.resize(self.size())
        overlay.show()
        overlay.raise_()

    def hide_loading(self):
        """Cache l'overlay de chargement"""
        if hasattr(self, 'loading_overlay') and self.loading_overlay:
            self.loading_overlay.hide()

    def on_toggle(self, checked: bool, style_name: str, generate_image: bool = False):
        """
        Gère la sélection d'un style
        :param checked: État du bouton toggle
        :param style_name: Nom du style sélectionné
        :param generate_image: Si True, lance la génération d'image
        """
        if self._generation_in_progress:
            return

        if checked:
            self.selected_style = style_name
            
            if generate_image:
                self._set_style_buttons_enabled(False)
                self._generation_in_progress = True
                self.generated_image = None
                self.show_loading()
                self._cleanup_thread()
                
                # Crée et configure le thread de génération
                self._thread = QThread()
                input_img = getattr(self.window(), "captured_image", None)
                self._worker = GenerationWorker(style_name, input_img)
                self._worker.moveToThread(self._thread)
                self._thread.started.connect(self._worker.run)
                self._worker.finished.connect(self.on_generation_finished)
                self._worker.finished.connect(self._thread.quit)
                self._worker.finished.connect(self._worker.deleteLater)
                self._thread.finished.connect(self._thread.deleteLater)
                self._thread.finished.connect(self._on_thread_finished)
                self._thread.start()

    def on_generation_finished(self, qimg):
        self._generation_in_progress = False
        self._set_style_buttons_enabled(True)
        self.hide_loading()
        if qimg and not qimg.isNull():
            self.generated_image = qimg
            self.show_image(qimg)
        else:
            self.generated_image = None

    def _set_style_buttons_enabled(self, enabled: bool):
        """Active/désactive les boutons de style"""
        if hasattr(self, 'button_group'):
            for btn in self.button_group.buttons():
                btn.setEnabled(enabled)

    def _cleanup_thread(self):
        """Nettoie le thread de génération"""
        if hasattr(self, "_thread") and self._thread is not None:
            try:
                if not self._thread.isRunning():
                    self._thread = None
                    self._worker = None
            except Exception as e:
                print(f"[CLEANUP] Exception in _cleanup_thread: {e}")

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
