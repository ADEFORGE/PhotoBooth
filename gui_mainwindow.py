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

        self.widgets = [
            self.welcome_widget,
            self.camera_widget,
            self.save_setting_widget,
            self.result_widget,
            self.load_widget
        ]

        for w in self.widgets:
            self.stack.addWidget(w)

        self.set_view(0)

    def _cleanup_widget(self, widget):
        # Nettoie threads et overlays pour chaque widget si la méthode existe
        if hasattr(widget, "_cleanup_thread"):
            widget._cleanup_thread()
        if hasattr(widget, "loading_overlay") and getattr(widget, "loading_overlay", None):
            widget.loading_overlay.hide()
            widget.loading_overlay.deleteLater()
            widget.loading_overlay = None
        # Ajoute ici tout nettoyage spécifique d'overlay ou de ressources

    def show_save_setting(self):
        self.set_view(2)
        self.save_setting_widget.show_image()

    def show_result(self):
        self.set_view(3)
        self.result_widget.show_image()

    def show_load_widget(self):
        self.set_view(4)

    def set_view(self, index: int):
        prev_index = self.stack.currentIndex()
        prev_widget = self.widgets[prev_index] if 0 <= prev_index < len(self.widgets) else None
        next_widget = self.widgets[index] if 0 <= index < len(self.widgets) else None

        # Cas particulier : passage direct CameraWidget -> SaveAndSettingWidget (garde le thread)
        if not (prev_index == 1 and index == 2):
            # Nettoie la vue précédente (thread, overlay, etc.)
            if prev_widget:
                self._cleanup_widget(prev_widget)

        # Arrête la caméra seulement si on la quitte
        if prev_index == 1 and index != 1:
            self.camera_widget.stop_camera()

        self.stack.setCurrentIndex(index)

        # Démarre la caméra si besoin
        if index == 1:
            self.camera_widget.start_camera()
