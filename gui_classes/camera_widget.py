# gui_classes/camerawidget.py
import cv2
import os
from PySide6.QtCore import QTimer, Qt, QThread, Signal, QObject
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QPushButton, QApplication
from gui_classes.gui_base_widget import PhotoBoothBaseWidget
from constante import CAMERA_ID, dico_styles
from comfy_classes.comfy_class_API_test_GUI import ImageGeneratorAPIWrapper
from gui_classes.image_utils import ImageUtils  # Add this import
from gui_classes.loading_overlay import LoadingOverlay

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

class CameraWidget(PhotoBoothBaseWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.cap = None
        self.timer = QTimer(self, timeout=self.update_frame)
        self.selected_style = None  # Style sélectionné
        self.loading_overlay = None

        # Bouton principal sur la première ligne
        self.first_buttons = [
            ("take_selfie", "capture")
        ]
        # Boutons de style sur la seconde ligne
        self.button_config = {}
        for style in dico_styles:
            self.button_config[style] = ("toggle_style", True)  # Toggle pour chaque style

        self.setup_buttons_from_config()

    def on_toggle(self, checked: bool, style_name: str):
        """Gère la sélection du style"""
        if checked:
            self.selected_style = style_name
        else:
            self.selected_style = None

    def start_camera(self):
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(CAMERA_ID)
            self.timer.start(30)

    def stop_camera(self):
        if self.cap and self.cap.isOpened():
            self.timer.stop()
            self.cap.release()
            self.cap = None

    def update_frame(self):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret or frame is None:
            # Affiche l'image de secours si la caméra ne fonctionne pas
            self.show_pixmap(QPixmap("gui_template/nocam.png"))
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.show_image(qimg)
        self.update()  # Force le rafraîchissement

    def show_loading(self):
        if not self.loading_overlay:
            self.loading_overlay = LoadingOverlay(self)
            self.loading_overlay.setGeometry(self.rect())
        self.loading_overlay.show()
        self.loading_overlay.raise_()

    def hide_loading(self):
        if self.loading_overlay:
            self.loading_overlay.hide()

    def capture(self):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret:
            return
            
        # Sauvegarde l'image pour ComfyUI
        cv2.imwrite("../ComfyUI/input/input.png", frame)
        
        # Convertit pour l'affichage Qt
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
        self.window().captured_image = qimg

        if self.selected_style:
            # Afficher l'overlay de chargement par-dessus la caméra active
            self.show_loading()
            self.thread = QThread()
            self.worker = GenerationWorker(self.selected_style)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_generation_finished)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()
        else:
            # Pas de style sélectionné : arrêter la caméra et aller à la page de validation
            self.stop_camera()
            self.window().save_setting_widget.generated_image = None
            self.window().save_setting_widget.selected_style = None
            self.window().show_save_setting()

    def on_generation_finished(self, image_path):
        self.hide_loading()
        self.stop_camera()
        if image_path and os.path.exists(image_path):
            img = cv2.imread(image_path)
            qimg = ImageUtils.cv_to_qimage(img)
            self.window().save_setting_widget.generated_image = qimg
        else:
            self.window().save_setting_widget.generated_image = None
        self.window().show_save_setting()
