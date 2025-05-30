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

class Worker(QObject):
    finished = Signal()
    result = Signal(str)

    def __init__(self, generator):
        super().__init__()
        self.generator = generator

    def run(self):
        self.generator.generate_image()
        self.finished.emit()


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
            self.button_config[style] = "toggle_style"
        self.button_config["Apply Style"] = "apply_style"

        self.setup_buttons_from_config()  # Place tous les boutons centrés

    def clear_buttons(self):
        for i in reversed(range(1, self.grid.rowCount())):
            for j in range(self.grid.columnCount()):
                item = self.grid.itemAtPosition(i, j)
                if item:
                    w = item.widget()
                    if w:
                        w.setParent(None)

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

    def setup_buttons_from_config(self):
        """Place automatiquement les boutons selon self.button_config, centrés sur chaque ligne."""
        self.clear_buttons()
        col_max = self.get_grid_width()
        btn_names = list(self.button_config.items())
        total_btns = len(btn_names)
        col, row = 0, 1
        i = 0
        while i < total_btns:
            btns_this_row = min(col_max, total_btns - i)
            start_col = (col_max - btns_this_row) // 2
            for j in range(btns_this_row):
                btn_name, method_name = btn_names[i + j]
                btn = QPushButton(btn_name)
                # Si c'est un style, bouton checkable et groupé
                if method_name == "toggle_style":
                    btn.setCheckable(True)
                    if btn_name == list(dico_styles.keys())[0]:
                        btn.setChecked(True)
                        self.selected_style = btn_name
                    btn.toggled.connect(lambda checked, s=btn_name: self.on_toggle(checked, s))
                    self.button_group.addButton(btn)
                elif method_name not in ("none", None):
                    if hasattr(self, method_name):
                        btn.clicked.connect(getattr(self, method_name))
                self.grid.addWidget(btn, row, start_col + j)
            i += btns_this_row
            row += 1
