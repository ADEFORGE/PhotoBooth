# gui_main.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Qt
from gui_classes.camera_widget import CameraWidget
from gui_classes.save_and_setting_widget import SaveAndSettingWidget
from gui_classes.result_widget import ResultWidget
from gui_classes.loading_widget import LoadingWidget
from gui_classes.welcome_widget import WelcomeWidget
from constante import WINDOW_STYLE

class PhotoBoothApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhotoBooth")
        self.setStyleSheet(WINDOW_STYLE)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.captured_image = None
        self.generated_image = None

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Stack widget avec style
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(WINDOW_STYLE)
        layout.addWidget(self.stack)

        # Ajoute WelcomeWidget comme vue 0
        self.welcome_widget = WelcomeWidget(self)
        self.camera_widget = CameraWidget(self)
        self.save_setting_widget = SaveAndSettingWidget(self)
        self.result_widget = ResultWidget(self)
        self.load_widget = LoadingWidget(self)

        for w in [self.welcome_widget, self.camera_widget, self.save_setting_widget, self.result_widget, self.load_widget]:
            self.stack.addWidget(w)

        self.set_view(0)

    def show_save_setting(self):
        self.set_view(2)
        self.save_setting_widget.show_image()

    def show_result(self):
        self.set_view(3)
        self.result_widget.show_image()

    def show_load_widget(self):
        self.set_view(4)

    def set_view(self, index: int):
        # Correction : il faut que WelcomeWidget appelle set_view(1) pour la caméra,
        # et que la caméra soit bien à l'index 1.
        # On arrête la caméra seulement si on la quitte (currentIndex == 1 et index != 1)
        # MAIS il faut aussi que window() dans WelcomeWidget retourne bien l'instance de PhotoBoothApp.

        # Correction : forcer le parent de WelcomeWidget à être self (le PhotoBoothApp)
        # et s'assurer que window() retourne bien self dans tous les widgets.

        if self.stack.currentIndex() == 1 and index != 1:
            self.camera_widget.stop_camera()
        self.stack.setCurrentIndex(index)
        if index == 1:
            self.camera_widget.start_camera()
