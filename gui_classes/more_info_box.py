from PySide6.QtWidgets import (QVBoxLayout, QLabel, QHBoxLayout, QWidget, QGraphicsBlurEffect, QPushButton, QDialog)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QSize
from constante import DIALOG_BOX_STYLE, DIALOG_ACTION_BUTTON_STYLE, FIRST_BUTTON_STYLE
import os
import unicodedata
import re

def normalize_btn_name(btn_name):
    name = btn_name.lower()
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    name = re.sub(r'[^a-z0-9]+', '_', name)
    name = name.strip('_')
    return name

class InfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
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

        # Placement image
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.image_label)

        # Boutons navigation (anglais, sans caractères spéciaux)
        self.first_buttons = [
            ("previous", "previous_image"),
            ("close", "accept"),
            ("next", "next_image")
        ]
        self._setup_buttons_row(main_layout)
        self.update_buttons_state()

    def _setup_buttons_row(self, layout):
        row_layout = QHBoxLayout()
        for btn_name, method_name in self.first_buttons:
            btn = QPushButton()
            btn.setStyleSheet(FIRST_BUTTON_STYLE)
            btn.setFixedSize(48, 48)
            icon_name = normalize_btn_name(btn_name)
            icon_path = f"gui_template/btn_icons/{icon_name}.png"
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                btn.setIcon(icon)
                btn.setIconSize(QSize(32, 32))  # Correction ici : utiliser QSize directement
                btn.setText("")
            else:
                btn.setText(btn_name)
            btn.clicked.connect(getattr(self, method_name))
            if btn_name == "previous":
                self.prev_btn = btn
            elif btn_name == "next":
                self.next_btn = btn
            row_layout.addWidget(btn)
        layout.addLayout(row_layout)

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
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.image_paths) - 1)

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