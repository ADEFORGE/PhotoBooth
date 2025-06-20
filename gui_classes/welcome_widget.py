# file:welcome_widget.py
from gui_classes.gui_base_widget import PhotoBoothBaseWidget
from gui_classes.btn import Btns
from PySide6.QtCore import Qt, Property, QPropertyAnimation
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from gui_classes.background_manager import BackgroundManager
from PySide6.QtGui import QPainter
import os
import json
from constante import TITLE_LABEL_STYLE

class WelcomeWidget(PhotoBoothBaseWidget):
    def __init__(self, parent=None):
        print("[WELCOME][DEBUG] __init__ start")
        super().__init__(parent)
        print("[WELCOME][DEBUG] __init__ after super")
        print("[WELCOME] Init WelcomeWidget")
        self.setWindowTitle("PhotoBooth - Accueil")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        # --- Fond animé (InfiniteScrollView) via BackgroundManager ---
        self._scroll_view = None
        self.set_scroll_fond()

        # === Ajout du titre et du message d'accueil ===
        UI_TEXTS_PATH = os.path.join(os.path.dirname(__file__), "../ui_texts.json")
        with open(UI_TEXTS_PATH, 'r', encoding='utf-8') as f:
            UI_TEXTS = json.load(f)
        welcome_texts = UI_TEXTS.get("WelcomeWidget", {})
        
        # Création d'un widget conteneur pour centrer le texte
        self.center_widget = QWidget(self)
        self.center_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Titre avec style et dimensions
        self.title_label = QLabel(welcome_texts.get("title", "Bienvenue"), self.center_widget)
        self.title_label.setStyleSheet("color: white; font-size: 72px; font-weight: bold; font-family: Arial;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.title_label.setWordWrap(True)  # Permet le saut de ligne automatique
        
        # Message avec style et dimensions
        self.message_label = QLabel(welcome_texts.get("message", ""), self.center_widget)
        self.message_label.setStyleSheet("color: white; font-size: 36px; font-family: Arial;")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.message_label.setWordWrap(True)
        
        # Layout vertical pour empiler titre et message
        text_layout = QVBoxLayout(self.center_widget)
        text_layout.setContentsMargins(40, 40, 40, 40)
        text_layout.setSpacing(30)
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.message_label)
        
        # Positionne le widget au centre
        if hasattr(self, '_update_center_widget_geometry'):
            self._update_center_widget_geometry()
        else:
            # fallback: center manually
            parent_rect = self.rect()
            center_width = int(parent_rect.width() * 0.8)
            center_height = int(parent_rect.height() * 0.6)
            x = (parent_rect.width() - center_width) // 2
            y = (parent_rect.height() - center_height) // 2
            self.center_widget.setGeometry(x, y, center_width, center_height)
            self.center_widget.raise_()
        print("[WELCOME][DEBUG] before layout creation")
        # Layout principal qui centre le widget conteneur
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.center_widget, 0, Qt.AlignCenter)
        print("[WELCOME][DEBUG] after layout creation")

        print("[WELCOME] Appel setup_buttons")
        # Bouton style 1 avec icône (camera.png)
        self.setup_buttons(
            style1_names=["camera"],  # Assurez-vous que gui_template/btn_icons/camera.png existe
            style2_names=[],
            slot_style1="goto_camera"
        )
        if self.btns:
            print("[WELCOME] Btns créés :", self.btns.style1_btns, self.btns.style2_btns)
            self.btns.raise_()
            self.overlay_widget.raise_()
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.raise_()
                btn.show()

        # Restaure le cleanup normal
        if hasattr(self, "cleanup") and hasattr(self.cleanup, "__code__") and "ignoré" in self.cleanup.__code__.co_consts:
            del self.cleanup

        # Démarre le thread caméra dès l'accueil
        try:
            if self.window() and hasattr(self.window(), "camera_widget"):
                self.window().camera_widget.start_camera()
        except Exception as e:
            print(f"[WELCOME] Erreur démarrage caméra: {e}")
        print("[WELCOME][DEBUG] __init__ end")
        self.gradient_opacity = 1.0
        self._gradient_anim = None

    def get_gradient_opacity(self):
        return self.gradient_opacity

    def set_gradient_opacity(self, value):
        self.gradient_opacity = value
        self.update()

    gradient_opacity_prop = Property(float, get_gradient_opacity, set_gradient_opacity)

    def fade_out_gradient(self, duration=1000):
        if self._gradient_anim:
            self._gradient_anim.stop()
        self._gradient_anim = QPropertyAnimation(self, b'gradient_opacity_prop')
        self._gradient_anim.setDuration(duration)
        self._gradient_anim.setStartValue(1.0)
        self._gradient_anim.setEndValue(0.0)
        self._gradient_anim.start()

    def resizeEvent(self, event):
        self._update_center_widget_geometry()
        if self._scroll_view:
            self._scroll_view.resize(self.size())
        self.overlay_widget.setGeometry(self.rect())
        super().resizeEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        # Ajout du fondu du gradient
        if self.background_manager and self.background_manager.get_source() == 'scroll' and self.gradient_opacity > 0:
            gradient_pixmap = self.background_manager._get_scaled_gradient("gui_template/Gradient Intro Screen.png", self.size())
            if gradient_pixmap:
                painter = QPainter(self)
                painter.setOpacity(self.gradient_opacity)
                painter.drawPixmap(0, 0, gradient_pixmap)
                painter.setOpacity(1.0)
                painter.end()

    def goto_camera(self):
        print("[WELCOME] goto_camera called")
        if self.window():
            self.window().set_view(1)

    def cleanup(self):
        print("[WELCOME][DEBUG] cleanup start (reset state, not destruction)")
        # Nettoyage complet du scroll animé et suppression du widget du parent (stack)
        BackgroundManager.stop_scroll_fond(self)
        BackgroundManager.clear_scroll_fond(self)
        if hasattr(self, '_scroll_view') and self._scroll_view:
            self._scroll_view.setParent(None)
            self._scroll_view.deleteLater()
            self._scroll_view = None
        if hasattr(self, "btns") and self.btns:
            print("[WELCOME][DEBUG] cleanup: cleaning btns")
            self.btns.cleanup()
        else:
            print("[WELCOME][DEBUG] cleanup: no btns to clean")
        # Optionnel : masquer le widget lui-même pour éviter tout effet de flash
        self.hide()
        print("[WELCOME][DEBUG] cleanup end (widget kept alive)")

    def showEvent(self, event):
        super().showEvent(event)
        if self.btns:
            self.btns.raise_()
        BackgroundManager.start_scroll_fond(self)
        try:
            if self.window() and hasattr(self.window(), "camera_widget"):
                self.window().camera_widget.start_camera()
        except Exception as e:
            print(f"[WELCOME] Erreur démarrage caméra (showEvent): {e}")

    def hideEvent(self, event):
        BackgroundManager.stop_scroll_fond(self)
        super().hideEvent(event)

    def on_enter(self):
        print("[WELCOME][DEBUG] on_enter called")
        # Correction : toujours garantir un scroll animé
        if not hasattr(self, '_scroll_view') or self._scroll_view is None:
            print("[WELCOME][DEBUG] on_enter: _scroll_view is None, recreating scroll fond")
            self.set_scroll_fond()
        BackgroundManager.start_scroll_fond(self)
        need_recreate = not self.btns or not getattr(self.btns, 'style1_btns', [])
        if not need_recreate:
            try:
                for btn in self.btns.style1_btns + self.btns.style2_btns:
                    btn.show()
                    btn.raise_()
                print("[WELCOME][DEBUG] on_enter: buttons already present")
            except Exception as e:
                print(f"[WELCOME][DEBUG] on_enter: Exception on btns: {e}, will recreate btns")
                need_recreate = True
        if need_recreate:
            print("[WELCOME][DEBUG] on_enter: recreating buttons")
            if self.btns:
                try:
                    self.btns.cleanup()
                except Exception as e:
                    print(f"[WELCOME][DEBUG] Exception during btns.cleanup(): {e}")
                self.btns = None
            self.setup_buttons(
                style1_names=["camera"],
                style2_names=[],
                slot_style1="goto_camera"
            )
        self.overlay_widget.raise_()
        print("[WELCOME][DEBUG] on_enter: END")

    def _update_center_widget_geometry(self):
        parent_rect = self.rect()
        center_width = int(parent_rect.width() * 0.8)
        center_height = int(parent_rect.height() * 0.6)
        x = (parent_rect.width() - center_width) // 2
        y = (parent_rect.height() - center_height) // 2
        self.center_widget.setGeometry(x, y, center_width, center_height)
        self.center_widget.raise_()

    def set_scroll_fond(self):
        BackgroundManager.set_scroll_fond(self)
