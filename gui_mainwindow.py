# gui_main.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Qt
from gui_classes.camera_widget import CameraWidget
from gui_classes.save_and_setting_widget import SaveAndSettingWidget
from gui_classes.result_widget import ResultWidget
from gui_classes.loading_widget import LoadingWidget
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

        self.camera_widget = CameraWidget(self)
        self.save_setting_widget = SaveAndSettingWidget(self)
        self.result_widget = ResultWidget(self)
        self.load_widget = LoadingWidget(self)

        for w in [self.camera_widget, self.save_setting_widget, self.result_widget, self.load_widget]:
            self.stack.addWidget(w)

        self.set_view(0)

    def show_save_setting(self):
        self.set_view(1)
        self.save_setting_widget.show_image()

    def show_result(self):
        self.set_view(2)
        self.result_widget.show_image()

    def show_load_widget(self):
        self.set_view(3)

    def set_view(self, index: int):
        if self.stack.currentIndex() == 0:
            self.camera_widget.stop_camera()
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.camera_widget.start_camera()
