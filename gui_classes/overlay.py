# gui_classes/overlay.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout, QHBoxLayout, QPushButton, QTextEdit, QSizePolicy, QGraphicsBlurEffect
from PySide6.QtCore import Qt, QSize, QEvent, QThread
from PySide6.QtGui import QMovie, QPixmap, QIcon, QImage, QPainter, QColor, QPen
from constante import DIALOG_BOX_STYLE, FIRST_BUTTON_STYLE
from gui_classes.btn import Btns
from gui_classes.toolbox import normalize_btn_name
import os

class Overlay(QWidget):
    def __init__(self, parent=None, center_on_screen=True):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setVisible(False)
        from constante import GRID_WIDTH
        self.GRID_WIDTH = GRID_WIDTH
        self._center_on_screen = center_on_screen
        self._centered_once = False

    def center_overlay(self):
        # Centre l'overlay sur l'écran principal en tenant compte de sa taille réelle
        screen = self.screen() if hasattr(self, 'screen') and self.screen() else None
        if screen is None:
            from PySide6.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            w, h = self.width(), self.height()
            x = geometry.x() + (geometry.width() - w) // 2
            y = geometry.y() + (geometry.height() - h) // 2
            self.move(x, y)

    def showEvent(self, event):
        super().showEvent(event)
        # Centre l'overlay à l'affichage, pour tenir compte de la taille réelle
        if self._center_on_screen and not self._centered_once:
            self.center_overlay()
            self._centered_once = True
        # Any additional logic for when overlay is shown can go here

    def hideEvent(self, event):
        super().hideEvent(event)
        # Any additional logic for when overlay is hidden can go here

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 128))

    def setup_buttons(self, style1_names, style2_names, slot_style1=None, slot_style2=None, start_row=3):
        if hasattr(self, 'btns') and self.btns:
            self.btns.cleanup()
        self.btns = Btns(self, [], [], None, None)
        self.btns.setup_buttons(style1_names, style2_names, slot_style1, slot_style2, layout=self.overlay_layout, start_row=start_row)
        self.overlay_widget.raise_()
        self.raise_()

    def setup_buttons_style_1(self, style1_names, slot_style1=None, start_row=3):
        if hasattr(self, 'btns') and self.btns:
            self.btns.setup_buttons_style_1(style1_names, slot_style1, layout=self.overlay_layout, start_row=start_row)
            self.overlay_widget.raise_()
            self.raise_()

    def setup_buttons_style_2(self, style2_names, slot_style2=None, start_row=4):
        if hasattr(self, 'btns') and self.btns:
            self.btns.setup_buttons_style_2(style2_names, slot_style2, layout=self.overlay_layout, start_row=start_row)
            self.overlay_widget.raise_()
            self.raise_()

    def show_overlay(self):
        self.setVisible(True)
        self.raise_()

    def hide_overlay(self):
        self.setVisible(False)
        self._centered_once = False  # Permet de recentrer si on réaffiche plus tard

class OverlayLoading(Overlay):
    def __init__(self, parent=None):
        super().__init__(parent)
        from constante import GRID_WIDTH
        self.overlay_widget = QWidget(self)
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_layout.setSpacing(0)
        # Centrer l'image sur la grille
        center_col = self.GRID_WIDTH // 2
        self.img_label = QLabel(self.overlay_widget)
        self.img_label.setAlignment(Qt.AlignCenter)
        self._movie = QMovie("gui_template/load.gif")
        self._movie.setScaledSize(QSize(64, 64))
        self.img_label.setMovie(self._movie)
        self.img_label.setFixedSize(64, 64)
        self.overlay_layout.addWidget(self.img_label, 0, center_col, 1, 1, alignment=Qt.AlignCenter)
        self.btns = Btns(self, [], [], None, None)
        self.setup_buttons_style_1(['close'], start_row=1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.overlay_widget)
        self.setLayout(layout)

    def showEvent(self, event):
        super().showEvent(event)
        if self._movie and not self._movie.isValid():
            self._movie.setFileName("gui_template/load.gif")
        if self._movie:
            self._movie.start()

    def hideEvent(self, event):
        if self._movie:
            self._movie.stop()
        super().hideEvent(event)

    def cleanup(self):
        if self._movie:
            self._movie.stop()
        super().cleanup()

class OverlayGray(Overlay):
    def __init__(self, parent=None, center_on_screen=True):
        super().__init__(parent, center_on_screen)
        self.setStyleSheet("background-color: rgba(24,24,24,0.82); border-radius: 18px; border: 3px solid black;")

class OverlayWhite(Overlay):
    def __init__(self, parent=None, center_on_screen=True):
        super().__init__(parent, center_on_screen)
        self.setStyleSheet("background-color: rgba(255,255,255,0.85); border-radius: 18px; border: 3px solid white;")

class OverlayTransparent(Overlay):
    def __init__(self, parent=None, center_on_screen=True):
        super().__init__(parent, center_on_screen)
        self.setStyleSheet("background: transparent;")

class OverlayRules(OverlayWhite):
    def __init__(self, parent=None, VALIDATION_OVERLAY_MESSAGE=None):
        super().__init__(parent)
        from constante import GRID_WIDTH
        self.setFixedSize(700, 540)  # Ensure overlay is large and consistent
        self.overlay_widget = QWidget(self)
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(40, 32, 40, 32)
        self.overlay_layout.setSpacing(24)
        self.overlay_layout.setRowStretch(0, 0)
        self.overlay_layout.setRowStretch(1, 2)
        self.overlay_layout.setRowStretch(2, 1)
        self.overlay_layout.setRowStretch(3, 0)
        row = 0
        # All widgets span the full grid width for proper centering
        if VALIDATION_OVERLAY_MESSAGE:
            msg_label = QLabel(VALIDATION_OVERLAY_MESSAGE, self.overlay_widget)
            msg_label.setStyleSheet("color: black; font-size: 22px; font-weight: bold; background: transparent;")
            msg_label.setAlignment(Qt.AlignCenter)
            self.overlay_layout.addWidget(msg_label, row, 0, 1, self.GRID_WIDTH, alignment=Qt.AlignCenter)
            row += 1
        self.img_label = QLabel(self.overlay_widget)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setMinimumSize(220, 220)
        self.img_label.setMaximumSize(260, 260)
        self.img_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.overlay_layout.addWidget(self.img_label, row, 0, 1, self.GRID_WIDTH, alignment=Qt.AlignCenter)
        row += 1
        self._movie = QMovie("gui_template/load.gif")
        self.img_label.setMovie(self._movie)
        self.text_edit = QTextEdit(self.overlay_widget)
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("background: transparent; color: black; font-size: 18px; border: none;")
        self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.text_edit.setMinimumHeight(80)
        self.text_edit.setMaximumHeight(180)
        self.text_edit.setMinimumWidth(int(self.width() * 0.85))
        try:
            with open("rules.txt", "r") as f:
                rules_text = f.read()
                html = f'<div align="center">{rules_text.replace(chr(10), "<br>")}</div>'
                self.text_edit.setHtml(html)
        except Exception as e:
            self.text_edit.setText(f"Error loading rules: {str(e)}")
        self.overlay_layout.addWidget(self.text_edit, row, 0, 1, self.GRID_WIDTH)
        row += 1
        # Place the buttons on the last row, spanning the full width
        self.btns = Btns(self, [], [], None, None)
        self.setup_buttons_style_1(['accept', 'close'], slot_style1=self._on_accept_close, start_row=row)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.overlay_widget)
        self.setLayout(layout)

    def show_default_image(self):
        if self._movie:
            self.img_label.setMovie(self._movie)
            self._movie.start()

    def display_qrcode(self, qimg: QImage):
        if self._movie:
            self._movie.stop()
        self.img_label.setMovie(None)
        if not qimg or qimg.isNull():
            self.img_label.setText("Erreur QR code")
            return
        pix = QPixmap.fromImage(qimg)
        target_size = min(self.img_label.width(), self.img_label.height(), 240)
        self.img_label.setPixmap(pix.scaled(
            target_size, target_size,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        self.img_label.repaint()

    def _on_accept_close(self):
        sender = self.sender()
        if sender and sender.objectName() == 'accept':
            if self.window() and hasattr(self.window(), 'set_view'):
                self.window().set_view(1)
        elif sender and sender.objectName() == 'close':
            if self.window() and hasattr(self.window(), 'set_view'):
                self.window().set_view(0)

class OverlayInfo(OverlayGray):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Information")
        self.setFixedSize(600, 400)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        from constante import GRID_WIDTH
        self.overlay_widget = QWidget(self)
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_layout.setSpacing(0)
        # Correction du centrage : calcul de la colonne centrale
        center_col = self.GRID_WIDTH // 2
        # Fond filtré
        bg = QLabel(self.overlay_widget)
        bg.setGeometry(0, 0, 600, 400)
        bg.setStyleSheet("background-color: rgba(24,24,24,0.82); border-radius: 18px;")
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(18)
        bg.setGraphicsEffect(blur)
        bg.lower()
        self.image_paths = [
            "gui_template/info1.png",
            "gui_template/info2.png",
            "gui_template/info3.png"
        ]
        self.current_index = 0
        self.image_label = QLabel(self.overlay_widget)
        self.image_label.setStyleSheet("background: transparent;")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.update_image()
        # Place l'image centrée sur la grille, sur toute la largeur
        self.overlay_layout.addWidget(self.image_label, 0, 0, 1, self.GRID_WIDTH, alignment=Qt.AlignCenter)
        # Place les boutons centrés sur la ligne suivante, sur toute la largeur
        self.btns = Btns(self, [], [], None, None)
        self.setup_buttons_style_1(['previous', 'close', 'next'], slot_style1=self._on_info_btn, start_row=1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.overlay_widget)
        self.setLayout(layout)

    def _on_info_btn(self):
        sender = self.sender()
        if sender and sender.objectName() == 'previous':
            if self.current_index > 0:
                self.current_index -= 1
                self.update_image()
                self.update_buttons_state()
        elif sender and sender.objectName() == 'next':
            if self.current_index < len(self.image_paths) - 1:
                self.current_index += 1
                self.update_image()
                self.update_buttons_state()
        elif sender and sender.objectName() == 'close':
            self.hide_overlay()
            self.deleteLater()

    def update_image(self):
        current_path = self.image_paths[self.current_index]
        pixmap = QPixmap(current_path)
        if not pixmap.isNull():
            self.image_label.setPixmap(pixmap.scaled(
                500, 300,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))

    def update_buttons_state(self):
        # Optionnel : désactive les boutons si besoin
        pass
