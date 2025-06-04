from gui_classes.gui_base_widget import PhotoBoothBaseWidget
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from gui_classes.scrole import InfiniteScrollView
import os

class WelcomeWidget(PhotoBoothBaseWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("PhotoBooth - Accueil")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        # --- Fond animé (InfiniteScrollView) ---
        images_folder = os.path.join(os.path.dirname(__file__), "../gui_template/sleep_picture")
        self.scroll_view = InfiniteScrollView(images_folder, scroll_speed=1, tilt_angle=30, parent=self)
        self.scroll_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_view.setStyleSheet("border: none; background: transparent;")
        self.scroll_view.setGeometry(self.rect())
        self.scroll_view.lower()  # Met au fond

        # Définir le bouton principal en bas via first_buttons
        self.first_buttons = [
            ("take_selfie", "goto_camera")
        ]
        self.button_config = {}  # Pas d'autres boutons
        self.setup_buttons_from_config()

        self.overlay_widget.raise_()  # Met l'overlay au-dessus du fond

    def resizeEvent(self, event):
        self.scroll_view.setGeometry(self.rect())
        self.overlay_widget.setGeometry(self.rect())
        super().resizeEvent(event)

    def paintEvent(self, event):
        QWidget.paintEvent(self, event)

    def goto_camera(self):
        win = self.window()
        if hasattr(win, "set_view"):
            win.set_view(1)  # 1 = CameraWidget
