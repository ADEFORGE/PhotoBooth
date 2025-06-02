from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                             QHBoxLayout, QWidget)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from constante import SPECIAL_BUTTON_STYLE, COLORS, WINDOW_STYLE

class InfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Information")
        self.setFixedSize(600, 300)
        
        # Force le fond de la boîte de dialogue (même style que l'app principale)
        self.setStyleSheet(f"background-color: {COLORS['orange']};")
        
        # Layout principal
        main_layout = QVBoxLayout()
        
        # Zone d'affichage de l'image
        self.image_label = QLabel()
        self.image_label.setStyleSheet("background: transparent;")
        self.image_label.setAlignment(Qt.AlignCenter)
        
        # Charge et affiche l'image
        self.current_image = QPixmap("gui_template/image.png")
        if not self.current_image.isNull():
            self.image_label.setPixmap(self.current_image.scaled(
                500, 300, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            ))
        
        main_layout.addWidget(self.image_label)
        
        # Layout pour les boutons de navigation
        nav_layout = QHBoxLayout()
        
        # Bouton précédent
        prev_btn = QPushButton("↤ Précédent")
        prev_btn.setStyleSheet(SPECIAL_BUTTON_STYLE)
        prev_btn.clicked.connect(self.previous_image)
        
        # Bouton suivant
        next_btn = QPushButton("Suivant ↦")
        next_btn.setStyleSheet(SPECIAL_BUTTON_STYLE)
        next_btn.clicked.connect(self.next_image)
        
        # Bouton fermer
        close_btn = QPushButton("Fermer")
        close_btn.setStyleSheet(SPECIAL_BUTTON_STYLE)
        close_btn.clicked.connect(self.accept)
        
        # Ajoute les boutons au layout de navigation
        nav_layout.addWidget(prev_btn)
        nav_layout.addWidget(close_btn)
        nav_layout.addWidget(next_btn)
        
        # Ajoute le layout de navigation au layout principal
        main_layout.addLayout(nav_layout)
        
        self.setLayout(main_layout)

    def previous_image(self):
        # À implémenter : chargement image précédente
        print("Previous image")
        
    def next_image(self):
        # À implémenter : chargement image suivante
        print("Next image")