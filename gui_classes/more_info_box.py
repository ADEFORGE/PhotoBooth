from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                             QHBoxLayout, QWidget)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from constante import SPECIAL_BUTTON_STYLE, COLORS, WINDOW_STYLE

class InfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Information")
        self.setFixedSize(600, 400)
        
        # Liste des images et index courant
        self.image_paths = [
            "gui_template/info1.png",
            "gui_template/info2.png",
            "gui_template/info3.png"
        ]
        self.current_index = 0
        
        # Force le fond de la boîte de dialogue (même style que l'app principale)
        self.setStyleSheet(f"background-color: {COLORS['orange']};")
        
        # Layout principal
        main_layout = QVBoxLayout()
        
        # Zone d'affichage de l'image
        self.image_label = QLabel()
        self.image_label.setStyleSheet("background: transparent;")
        self.image_label.setAlignment(Qt.AlignCenter)
        
        # Charge la première image
        self.update_image()
        
        main_layout.addWidget(self.image_label)
        
        # Layout pour les boutons de navigation
        nav_layout = QHBoxLayout()
        
        # Bouton précédent
        self.prev_btn = QPushButton("↤ Précédent")
        self.prev_btn.setStyleSheet(SPECIAL_BUTTON_STYLE)
        self.prev_btn.clicked.connect(self.previous_image)
        
        # Bouton suivant
        self.next_btn = QPushButton("Suivant ↦")
        self.next_btn.setStyleSheet(SPECIAL_BUTTON_STYLE)
        self.next_btn.clicked.connect(self.next_image)
        
        # Bouton fermer
        close_btn = QPushButton("Fermer")
        close_btn.setStyleSheet(SPECIAL_BUTTON_STYLE)
        close_btn.clicked.connect(self.accept)
        
        # Ajoute les boutons au layout de navigation
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(close_btn)
        nav_layout.addWidget(self.next_btn)
        
        # Ajoute le layout de navigation au layout principal
        main_layout.addLayout(nav_layout)
        
        self.setLayout(main_layout)
        
        # Met à jour l'état des boutons
        self.update_buttons_state()

    def update_image(self):
        """Charge et affiche l'image courante."""
        current_path = self.image_paths[self.current_index]
        pixmap = QPixmap(current_path)
        if not pixmap.isNull():
            self.image_label.setPixmap(pixmap.scaled(
                500, 300,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))

    def update_buttons_state(self):
        """Met à jour l'état actif/inactif des boutons de navigation."""
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.image_paths) - 1)

    def previous_image(self):
        """Affiche l'image précédente."""
        if self.current_index > 0:
            self.current_index -= 1
            self.update_image()
            self.update_buttons_state()

    def next_image(self):
        """Affiche l'image suivante."""
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.update_image()
            self.update_buttons_state()