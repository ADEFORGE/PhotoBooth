# file: screensaver_window.py
import os
import json
from gui_classes.gui_base_widget import PhotoBoothBaseWidget
from gui_classes.language_manager import language_manager
from gui_classes.btn import Btns
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

from constante import TITLE_LABEL_STYLE, GRID_WIDTH

class SleepScreenWindow(PhotoBoothBaseWidget):
    """
    Fenêtre d'écran de veille minimaliste, fond totalement transparent,
    labels dynamiques et bouton caméra, sans gestion de fond animé, scroll ou BackgroundManager.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Texte par défaut
        ui_texts_path = os.path.join(os.path.dirname(__file__), '..', 'ui_texts.json')
        try:
            with open(ui_texts_path, 'r', encoding='utf-8') as f:
                all_ui_texts = json.load(f)
            self._default_texts = all_ui_texts.get('WelcomeWidget', {})
        except Exception:
            self._default_texts = {}

        self.setWindowTitle("PhotoBooth - Veille")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.showFullScreen()

        # Suppression du fond animé et du BackgroundManager

        # Conteneur centré
        self.center_widget = QWidget(self.overlay_widget)
        self.center_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.overlay_layout.addWidget(
            self.center_widget, 1, 0, 1, GRID_WIDTH, alignment=Qt.AlignCenter
        )
        self.center_layout = QVBoxLayout(self.center_widget)
        self.center_layout.setContentsMargins(40, 40, 40, 40)
        self.center_layout.setSpacing(30)
        self.center_layout.setAlignment(Qt.AlignCenter)

        # Labels
        self.title_label = QLabel(self.center_widget)
        self.title_label.setStyleSheet("color: white; font-size: 72px; font-weight: bold; font-family: Arial;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)

        self.message_label = QLabel(self.center_widget)
        self.message_label.setStyleSheet("color: white; font-size: 36px; font-family: Arial;")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)

        self.center_layout.addWidget(self.title_label)
        self.center_layout.addWidget(self.message_label)

        # Bouton caméra
        self.setup_buttons(
            style1_names=['camera'],
            style2_names=[],
            slot_style1='on_camera_button_clicked'
        )

        language_manager.subscribe(self.update_language)
        self.update_language()

    def update_language(self):
        texts = language_manager.get_texts('WelcomeWidget') or {}
        self.title_label.setText(texts.get('title', self._default_texts.get('title', 'Bienvenue')))
        self.message_label.setText(texts.get('message', self._default_texts.get('message', '')))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay_widget.setGeometry(self.rect())

    def showEvent(self, event):
        super().showEvent(event)
        if self.btns:
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.show(); btn.raise_()

    def hideEvent(self, event):
        super().hideEvent(event)

    def cleanup(self):
        if self.btns:
            self.btns.cleanup(); self.btns = None
        language_manager.unsubscribe(self.update_language)
        super().cleanup()

    # Contrôle d'affichage
    def show_items(self):
        self.title_label.show(); self.message_label.show()
        if self.btns:
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.show(); btn.setEnabled(True)

    def hide_items(self):
        self.title_label.hide(); self.message_label.hide()
        if self.btns:
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.hide(); btn.setEnabled(False)

    def on_camera_button_clicked(self):
        # Démarre la transition vers PhotoBooth
        self.window().start_change_view(1)
