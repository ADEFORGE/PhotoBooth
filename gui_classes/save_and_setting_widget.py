import cv2
import numpy as np
import glob
import os
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QButtonGroup
from gui_classes.gui_base_widget import PhotoBoothBaseWidget
from constante import dico_styles
from gui_classes.more_info_box import InfoDialog
from constante import BUTTON_STYLE
from comfy_classes.comfy_class_API_test_GUI import ImageGeneratorAPIWrapper

class GenerationWorker(QObject):
    finished = Signal(str)  # path to generated image

    def __init__(self, style):
        super().__init__()
        self.style = style
        self.generator = ImageGeneratorAPIWrapper()

    def run(self):
        self.generator.set_style(self.style)
        self.generator.generate_image()
        images = self.generator.get_image_paths()
        if images:
            self.finished.emit(images[0])
        else:
            self.finished.emit("")

class SaveAndSettingWidget(PhotoBoothBaseWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.selected_style = None
        self.generated_image = None
        self._thread = None
        self._worker = None

        # Première ligne : boutons Validate et Refuse
        self.first_buttons = [
            ("Validate", "validate"),
            ("Refuse", "refuse")
        ]

        # Seconde ligne : boutons de style (toggle)
        self.button_config = {}
        for style in dico_styles:
            self.button_config[style] = ("toggle_style", True)

        self.setup_buttons_from_config()

    def show_image(self):
        if self.generated_image is not None:
            super().show_image(self.generated_image)
        elif img := self.window().captured_image:
            super().show_image(img)

    def on_toggle(self, checked: bool, style_name: str):
        if checked:
            self.selected_style = style_name
            # Lancer la génération d'image pour le nouveau style
            self.generated_image = None
            self.show_gif("gui_template/load.gif")
            self._thread = QThread()
            self._worker = GenerationWorker(style_name)
            self._worker.moveToThread(self._thread)
            self._thread.started.connect(self._worker.run)
            self._worker.finished.connect(self.on_generation_finished)
            self._worker.finished.connect(self._thread.quit)
            self._worker.finished.connect(self._worker.deleteLater)
            self._thread.finished.connect(self._thread.deleteLater)
            self._thread.start()

    def on_generation_finished(self, image_path):
        if image_path and os.path.exists(image_path):
            img = cv2.imread(image_path)
            self.generated_image = self.cv_to_qimage(img)
        else:
            self.generated_image = None
        self.show_image()

    def validate(self):
        # Ouvre la boîte d'information
        dialog = InfoDialog(self)
        dialog.exec()

    def refuse(self):
        # Retourne à la caméra
        self.window().set_view(0)

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
