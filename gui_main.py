# gui_main.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from gui_classes.camerawidget import CameraWidget
from gui_classes.choosestylewidget import ChooseStyleWidget
from gui_classes.resultwidget import ResultWidget
from gui_classes.loadwidget import LoadWidget

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhotoBooth")
        self.captured_image = None
        self.generated_image = None

        self.stack = QStackedWidget(self)
        self.camera_widget = CameraWidget(self)
        self.choose_widget = ChooseStyleWidget(self)
        self.result_widget = ResultWidget(self)
        self.load_widget = LoadWidget(self)

        for w in [self.camera_widget, self.choose_widget, self.result_widget, self.load_widget]:
            self.stack.addWidget(w)

        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)

        self.set_view(0)

    def show_choose_style(self):
        self.set_view(1)
        self.choose_widget.show_image()

    def show_result(self):
        self.set_view(2)
        self.result_widget.show_image()

    def set_view(self, index: int):
        if self.stack.currentIndex() == 0:
            self.camera_widget.stop_camera()
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.camera_widget.start_camera()
