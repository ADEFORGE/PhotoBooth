from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QWidget, QHBoxLayout, QLabel, QGraphicsBlurEffect
from PySide6.QtCore import Qt
from constante import DIALOG_BOX_STYLE


class RulesDialog(QDialog):
    """
    Dialog box displaying usage rules.
    """

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rules")
        self.setFixedSize(600, 400)
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # Ajout pour transparence réelle
        self.setStyleSheet(DIALOG_BOX_STYLE)  # Applique le style commun

        # --- Ajout d'un fond filtré ---
        bg = QLabel(self)
        bg.setGeometry(0, 0, 600, 400)
        bg.setStyleSheet("background-color: rgba(24,24,24,0.82); border-radius: 18px;")
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(18)
        bg.setGraphicsEffect(blur)
        bg.lower()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        # Titre
        title = QLabel("Usage Rules")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Zone de texte
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("background: transparent; color: white; font-size: 16px; border: none;")
        main_layout.addWidget(self.text_edit, stretch=1)

        # Bouton fermer
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        accept_btn = QPushButton("Accept")
        accept_btn.clicked.connect(self.accept)
        btn_layout.addWidget(accept_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)
        self._load_rules_content()

    def _load_rules_content(self) -> None:
        try:
            with open("rules.txt", "r") as f:
                content = f.read()
                self.text_edit.setText(content)
        except Exception as e:
            self.text_edit.setText(f"Error loading rules: {str(e)}")