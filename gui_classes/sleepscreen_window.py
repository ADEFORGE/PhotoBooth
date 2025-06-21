# file: screensaver_window.py
from gui_classes.gui_base_widget import PhotoBoothBaseWidget
from gui_classes.background_manager import BackgroundManager
from gui_classes.language_manager import language_manager
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt
import os
from constante import TITLE_LABEL_STYLE, GRID_WIDTH

class SleepScreenWindow(PhotoBoothBaseWidget):
    """
    Fenêtre d'écran de veille animé.
    Hérite de PhotoBoothBaseWidget pour garder la structure UI de base.
    Affiche un fond scroll infini et un texte centré, avec support multilangue.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PhotoBooth - Veille")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        # --- Fond animé via BackgroundManager ---
        images_folder = os.path.join(
            os.path.dirname(__file__), '..', 'gui_template', 'sleep_picture'
        )
        self.background_manager.set_scroll(
            parent_widget=self,
            folder_path=images_folder,
            scroll_speed=1,
            fps=60,
            margin_x=1,
            margin_y=1,
            angle=15
        )

        # --- Conteneur centré pour titre et message ---
        self.center_widget = QWidget(self.overlay_widget)
        self.center_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.overlay_layout.addWidget(
            self.center_widget, 1, 0, 1, GRID_WIDTH, alignment=Qt.AlignCenter
        )
        self.center_layout = QVBoxLayout(self.center_widget)
        self.center_layout.setContentsMargins(40, 40, 40, 40)
        self.center_layout.setSpacing(20)
        self.center_layout.setAlignment(Qt.AlignCenter)

        # Labels texte
        self.title_label = QLabel(self.center_widget)
        self.title_label.setStyleSheet(TITLE_LABEL_STYLE)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)

        self.message_label = QLabel(self.center_widget)
        self.message_label.setStyleSheet("color: white; font-size: 36px;")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)

        self.center_layout.addWidget(self.title_label)
        self.center_layout.addWidget(self.message_label)

        # Charge le texte initial selon la langue
        self._load_texts()
        language_manager.subscribe(self._load_texts)

    def _load_texts(self):
        """
        Récupère les textes depuis LanguageManager et met à jour les labels.
        """
        ui_texts = language_manager.get_texts('SleepScreenWindow') or {}
        self.title_label.setText(ui_texts.get('title', 'Bienvenue'))
        self.message_label.setText(ui_texts.get('message', ''))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Ajuste la taille du fond scroll
        sw = self.background_manager.scroll_widget
        if sw:
            sw.resize(self.size())

    def showEvent(self, event):
        super().showEvent(event)
        # Relance le scroll si nécessaire
        images_folder = os.path.join(
            os.path.dirname(__file__), '..', 'gui_template', 'sleep_picture'
        )
        self.background_manager.set_scroll(parent_widget=self, folder_path=images_folder)

    def hideEvent(self, event):
        # Stoppe le scroll proprement
        self.background_manager.clear_scroll()
        super().hideEvent(event)

    def cleanup(self):
        """
        Nettoie les ressources spécifiques puis délègue au base cleanup.
        """
        self.background_manager.clear_scroll()
        language_manager.unsubscribe(self._load_texts)
        super().cleanup()
