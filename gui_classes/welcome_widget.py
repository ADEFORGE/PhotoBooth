from gui_classes.gui_base_widget import PhotoBoothBaseWidget
from gui_classes.btn import Btns
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from gui_classes.scrole import InfiniteScrollView
import os

class WelcomeWidget(PhotoBoothBaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
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

    def resizeEvent(self, event):
        self.scroll_view.setGeometry(self.rect())
        self.overlay_widget.setGeometry(self.rect())
        super().resizeEvent(event)

    def paintEvent(self, event):
        QWidget.paintEvent(self, event)

    def goto_camera(self):
        print("[WELCOME] goto_camera called")
        if self.window():
            self.window().set_view(1)

    def cleanup(self):
        if hasattr(self, "btns") and self.btns:
            self.btns.cleanup()
            self.btns = None

    def showEvent(self, event):
        super().showEvent(event)
        if self.btns:
            self.btns.raise_()
