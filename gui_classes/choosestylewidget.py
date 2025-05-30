# gui_classes/choosestylewidget.py
import cv2
import numpy as np
import glob
import os
import time
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QSizePolicy, QGridLayout, QButtonGroup

from constante import dico_styles

from comfy_classes.comfy_class_API import ImageGeneratorAPIWrapper

class Worker(QObject):
    finished = Signal()
    result = Signal(str)

    def __init__(self, generator):
        super().__init__()
        self.generator = generator

    def run(self):
        self.generator.generate_image()
        self.finished.emit()


class ChooseStyleWidget(QWidget):
    def __init__(self, parent=None):
        self.generator = ImageGeneratorAPIWrapper()
        super().__init__(parent)
        self.selected_style = None

        self.image_label = QLabel(alignment=Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        grid = QGridLayout(self)
        grid.addWidget(self.image_label, 0, 0, 1, len(dico_styles))

        for idx, style in enumerate(dico_styles):
            btn = QPushButton(style)
            btn.setCheckable(True)
            if idx == 0:
                btn.setChecked(True)
                self.selected_style = style
            btn.toggled.connect(lambda checked, s=style: self.on_toggle(checked, s))
            self.button_group.addButton(btn)
            grid.addWidget(btn, 1, idx)

        self.run_btn = QPushButton("Apply Style")
        self.run_btn.clicked.connect(self.apply_style)
        grid.addWidget(self.run_btn, 2, 0, 1, len(dico_styles))

    def show_image(self):
        if img := self.window().captured_image:
            self.image_label.setPixmap(QPixmap.fromImage(img))

    def on_toggle(self, checked: bool, style_name: str):
        if checked:
            self.selected_style = style_name
            self.generator.set_style(style_name)


    def apply_style(self):
        if not self.selected_style:
            return
        cv2_img = self.qimage_to_cv(self.window().captured_image)
        cv2.imwrite("../ComfyUI/input/input.png", cv2_img)

        self.window().show_load_widget()

        self.thread = QThread()
        self.worker = Worker(self.generator)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_generation_finished(self):
        png_files = glob.glob("../ComfyUI/output/*.png")
        if png_files:
            processed = cv2.imread(png_files[0])
            self.window().generated_image = self.cv_to_qimage(processed)
            self.window().show_result()
            os.remove(png_files[0])
            os.remove("../ComfyUI/input/input.png")
        

    @staticmethod
    def qimage_to_cv(qimg: QImage) -> np.ndarray:
        qimg = qimg.convertToFormat(QImage.Format_RGB888)
        w, h = qimg.width(), qimg.height()
        buffer = qimg.bits().tobytes()
        arr = np.frombuffer(buffer, np.uint8).reshape((h, w, 3))
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

    @staticmethod
    def cv_to_qimage(cv_img: np.ndarray) -> QImage:
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        return QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
