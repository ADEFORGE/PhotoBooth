from PySide6.QtWidgets import (QVBoxLayout, QLabel, QHBoxLayout, QWidget, QGraphicsBlurEffect, QPushButton)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from constante import DIALOG_BOX_STYLE, DIALOG_ACTION_BUTTON_STYLE
from gui_classes.gui_base_widget import PhotoBoothBaseWidget

class InfoDialog(PhotoBoothBaseWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Information")
        self.setFixedSize(600, 400)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet(DIALOG_BOX_STYLE)

        # --- Ajout d'un fond filtré ---
        bg = QLabel(self)
        bg.setGeometry(0, 0, 600, 400)
        bg.setStyleSheet("background-color: rgba(24,24,24,0.82); border-radius: 18px;")
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(18)
        bg.setGraphicsEffect(blur)
        bg.lower()

        # Images et index courant
        self.image_paths = [
            "gui_template/info1.png",
            "gui_template/info2.png",
            "gui_template/info3.png"
        ]
        self.current_index = 0

        # Affichage image
        self.image_label = QLabel(self)
        self.image_label.setStyleSheet("background: transparent;")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.update_image()
        self.overlay_layout.addWidget(self.image_label, 1, 0, 1, self.get_grid_width(), alignment=Qt.AlignCenter)

        # Définition des boutons (anglais, sans caractères spéciaux)
        self.first_buttons = [
            ("previous", "previous_image"),
            ("close", "accept"),
            ("next", "next_image")
        ]
        self.button_config = {}

        self.setup_buttons_from_config()
        self.update_buttons_state()

    def accept(self):
        self.close()

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
        for btn in self.findChildren(QPushButton):
            if btn.text() == "" and btn.icon():  # bouton icône uniquement
                icon_name = btn.icon().name() if hasattr(btn.icon(), "name") else ""
                # fallback: utilise l'ordre
            elif btn.text() == "previous":
                btn.setEnabled(self.current_index > 0)
            elif btn.text() == "next":
                btn.setEnabled(self.current_index < len(self.image_paths) - 1)
            # "close" toujours activé

    def previous_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_image()
            self.update_buttons_state()

    def next_image(self):
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.update_image()
            self.update_buttons_state()