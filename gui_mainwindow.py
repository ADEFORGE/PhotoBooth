# gui_main.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from gui_classes.camera_widget import CameraWidget
from gui_classes.style_chooser_widget import StyleChooserWidget
from gui_classes.result_widget import ResultWidget
from gui_classes.loading_widget import LoadingWidget
from constante import WINDOW_STYLE

class PhotoBoothApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhotoBooth")
        self.setStyleSheet(WINDOW_STYLE)
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
        self.choose_widget = StyleChooserWidget(self)
        self.result_widget = ResultWidget(self)
        self.load_widget = LoadingWidget(self)

        for w in [self.camera_widget, self.choose_widget, self.result_widget, self.load_widget]:
            self.stack.addWidget(w)

        self.set_view(0)

    def show_choose_style(self):
        self.set_view(1)
        self.choose_widget.show_image()

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
