from gui_classes.gui_base_widget import PhotoBoothBaseWidget
from gui_classes.btn import Btns
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout, QSizePolicy
from gui_classes.scrole import InfiniteScrollView
from gui_classes.language_manager import language_manager
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

        # --- Fond animé (InfiniteScrollView) réactivé ---
        images_folder = os.path.join(os.path.dirname(__file__), "../gui_template/sleep_picture")
        self.scroll_view = InfiniteScrollView(images_folder, scroll_speed=1, tilt_angle=30, parent=self)
        self.scroll_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_view.setStyleSheet("border: none; background: transparent;")
        self.scroll_view.setGeometry(self.rect())
        self.scroll_view.lower()  # Met au fond

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
        self._update_center_widget_geometry()
        print("[WELCOME][DEBUG] before layout creation")
        # Layout principal qui centre le widget conteneur
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.center_widget, 0, Qt.AlignCenter)
        print("[WELCOME][DEBUG] after layout creation")

        # Utilise le BackgroundManager pour le fond de veille
        if hasattr(self, 'background_manager'):
            # On prend un screenshot du scroll_view pour le fond
            pixmap = self.scroll_view.grab()
            self.background_manager.set_scroll_pixmap(pixmap)
            self.update()

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

        language_manager.subscribe(self.update_language)
        self.update_language()

    def update_language(self):
        welcome_texts = language_manager.get_texts("WelcomeWidget")
        self.title_label.setText(welcome_texts.get("title", "Bienvenue"))
        self.message_label.setText(welcome_texts.get("message", ""))

    def resizeEvent(self, event):
        self.scroll_view.setGeometry(self.rect())
        self.overlay_widget.setGeometry(self.rect())
        self._update_center_widget_geometry()
        super().resizeEvent(event)

    def paintEvent(self, event):
        QWidget.paintEvent(self, event)

    def goto_camera(self):
        print("[WELCOME] goto_camera called")
        if self.window():
            self.window().set_view(1)

    def cleanup(self):
        print("[WELCOME][DEBUG] cleanup start (reset state, not destruction)")
        # Stop scroll_view timer and reset scene, but do not delete the widget or its children
        if hasattr(self, "scroll_view"):
            print("[WELCOME][DEBUG] cleanup: stopping scroll_view")
            if hasattr(self.scroll_view, "stop"):
                self.scroll_view.stop()
            # Optionally clear scene content for a fresh start
            if hasattr(self.scroll_view, 'scene') and self.scroll_view.scene is not None:
                print("[WELCOME][DEBUG] cleanup: clearing graphics scene")
                self.scroll_view.scene.clear()
                self.scroll_view._populated = False  # <-- Ajouté ici !
        else:
            print("[WELCOME][DEBUG] cleanup: no scroll_view to clean")
        # Optionally reset text/buttons if needed
        if hasattr(self, "btns") and self.btns:
            print("[WELCOME][DEBUG] cleanup: cleaning btns")
            self.btns.cleanup()
        else:
            print("[WELCOME][DEBUG] cleanup: no btns to clean")
        # Do not delete layouts or widgets, just reset state if needed
        print("[WELCOME][DEBUG] cleanup end (widget kept alive)")
        language_manager.unsubscribe(self.update_language)

    def showEvent(self, event):
        super().showEvent(event)
        if self.btns:
            self.btns.raise_()
        # Démarre le thread caméra si ce n'est pas déjà fait
        try:
            if self.window() and hasattr(self.window(), "camera_widget"):
                self.window().camera_widget.start_camera()
        except Exception as e:
            print(f"[WELCOME] Erreur démarrage caméra (showEvent): {e}")

    def _update_center_widget_geometry(self):
        """Centre le widget de texte au milieu de l'écran"""
        parent_rect = self.rect()
        center_width = int(parent_rect.width() * 0.8)  # 80% de la largeur
        center_height = int(parent_rect.height() * 0.6)  # 60% de la hauteur
        
        x = (parent_rect.width() - center_width) // 2
        y = (parent_rect.height() - center_height) // 2
        
        self.center_widget.setGeometry(x, y, center_width, center_height)
        self.center_widget.raise_()

    def on_enter(self):
        print("[WELCOME][DEBUG] on_enter called")
        if hasattr(self, "scroll_view"):
            print(f"[WELCOME][DEBUG] on_enter: scroll_view isVisible={self.scroll_view.isVisible()} geometry={self.scroll_view.geometry()}")
            if hasattr(self.scroll_view, 'scene') and self.scroll_view.scene is not None:
                print(f"[WELCOME][DEBUG] on_enter: scene items count={len(self.scroll_view.scene.items())}")
                if len(self.scroll_view.scene.items()) == 0:
                    print("[WELCOME][DEBUG] on_enter: repopulating scroll scene (empty scene)")
                    self.scroll_view._populated = False
                    self.scroll_view._populate_scene()
                    print(f"[WELCOME][DEBUG] on_enter: scene repopulated, items count={len(self.scroll_view.scene.items())}")
            else:
                print("[WELCOME][DEBUG] on_enter: scene is None, repopulating scroll scene")
                self.scroll_view._populated = False
                self.scroll_view._populate_scene()
                print(f"[WELCOME][DEBUG] on_enter: scene repopulated, items count={len(self.scroll_view.scene.items())}")
            if hasattr(self.scroll_view, 'timer'):
                print(f"[WELCOME][DEBUG] on_enter: timer isActive={self.scroll_view.timer.isActive()}")
                if not self.scroll_view.timer.isActive():
                    print("[WELCOME][DEBUG] on_enter: restarting scroll timer")
                    self.scroll_view.timer.start(30)
            self.scroll_view.show()
            self.scroll_view.lower()
            print(f"[WELCOME][DEBUG] on_enter: scroll_view isVisible after show/lower={self.scroll_view.isVisible()}")
        else:
            print("[WELCOME][DEBUG] on_enter: no scroll_view present")
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
