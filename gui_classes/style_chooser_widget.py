# gui_classes/choosestylewidget.py
import cv2
import numpy as np
import glob
import os
import time
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QPushButton, QButtonGroup
from gui_classes.gui_base_widget import PhotoBoothBaseWidget
from constante import dico_styles
from comfy_classes.comfy_class_API_test_GUI import ImageGeneratorAPIWrapper
from constante import (
    BUTTON_STYLE
)
from gui_classes.image_utils import ImageUtils


class Worker(QObject):
    finished = Signal(QImage)

    def __init__(self, generator, input_image=None):
        super().__init__()
        self.generator = generator
        self.input_image = input_image

    def run(self):
        if self.input_image is not None:
            arr = ImageUtils.qimage_to_cv(self.input_image)
            cv2.imwrite("../ComfyUI/input/input.png", arr)
        self.generator.generate_image()
        png_files = glob.glob("../ComfyUI/output/*.png")
        if png_files:
            processed = cv2.imread(png_files[0])
            qimg = ImageUtils.cv_to_qimage(processed)
            qimg = qimg.scaled(1200, 1200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.finished.emit(qimg)
            os.remove(png_files[0])
            os.remove("../ComfyUI/input/input.png")
        else:
            self.finished.emit(QImage())


class StyleChooserWidget(PhotoBoothBaseWidget):
    def __init__(self, parent=None):
        self.generator = ImageGeneratorAPIWrapper()
        super().__init__()
        self.selected_style = None

        self.clear_buttons()
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        # Prépare le dico pour tous les boutons (styles + action)
        self.button_config = {}
        for style in dico_styles:
            self.button_config[style] = ("toggle_style", True)  # Indique que c'est un toggle button
        self.button_config["Apply Style"] = "apply_style"  # Bouton normal

        self.setup_buttons_from_config()  # Place tous les boutons centrés

    def show_image(self):
        if img := self.window().captured_image:
            super().show_image(img)

    def on_toggle(self, checked: bool, style_name: str):
        if checked:
            self.selected_style = style_name
            self.generator.set_style(style_name)


    def apply_style(self):
        if not self.selected_style:
            return
        input_img = self.window().captured_image
        self.window().show_load_widget()
        self.thread = QThread()
        self.worker = Worker(self.generator, input_img)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_generation_finished(self, qimg):
        if qimg and not qimg.isNull():
            self.window().generated_image = qimg
            self.window().show_result()
