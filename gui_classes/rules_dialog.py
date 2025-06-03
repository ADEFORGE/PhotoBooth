from PySide6.QtWidgets import QVBoxLayout, QTextEdit, QHBoxLayout, QLabel, QGraphicsBlurEffect, QWidget, QPushButton, QDialog
from PySide6.QtGui import QIcon
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


class RulesDialog(QDialog):
    """
    Dialog box displaying usage rules.
    """

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rules")
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

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        # Titre
        title = QLabel("Usage Rules", self)
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Texte
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("background: transparent; color: white; font-size: 16px; border: none;")
        main_layout.addWidget(self.text_edit)
        self._load_rules_content()

        # Boutons (anglais, sans caractères spéciaux)
        self.first_buttons = [("accept", "accept")]
        self._setup_buttons_row(main_layout)

        self.setLayout(main_layout)

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
            row_layout.addWidget(btn)
        layout.addLayout(row_layout)

    def accept(self):
        self.close()

    def _load_rules_content(self) -> None:
        try:
            with open("rules.txt", "r") as f:
                content = f.read()
                self.text_edit.setText(content)
        except Exception as e:
            self.text_edit.setText(f"Error loading rules: {str(e)}")