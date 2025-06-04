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
import objgraph

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
        # Désactive tous les boutons si un thread de génération est en cours dans SaveAndSettingWidget
        save_widget = getattr(self.window(), "save_setting_widget", None)
        if save_widget and getattr(save_widget, "_generation_in_progress", False):
            if hasattr(self, 'button_group'):
                for btn in self.button_group.buttons():
                    btn.setEnabled(False)
            return
        if checked:
            self.selected_style = style_name
        else:
            self.selected_style = None
        # Appelle la méthode parente avec generate_image=False
        super().on_toggle(checked, style_name, generate_image=False)

    def start_camera(self):
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(CAMERA_ID)
            self.timer.start(30)

    def stop_camera(self):
        # Arrête la caméra et tout thread éventuel de génération dans SaveAndSettingWidget
        if self.cap and self.cap.isOpened():
            self.timer.stop()
            self.cap.release()
            self.cap = None
        # Arrête aussi le thread de génération du widget de sauvegarde si actif
        save_widget = getattr(self.window(), "save_setting_widget", None)
        if save_widget and hasattr(save_widget, "_cleanup_thread"):
            save_widget._cleanup_thread()

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

        cv2.imwrite("../ComfyUI/input/input.png", frame)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
        # Redimensionne avant de stocker
        qimg = qimg.scaled(1200, 1200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.window().captured_image = qimg

        save_widget = self.window().save_setting_widget

        if self.selected_style:
            save_widget.selected_style = self.selected_style
            save_widget.generated_image = None
            if hasattr(save_widget, "cleanup_all_threads_and_overlays"):
                save_widget.cleanup_all_threads_and_overlays()
            self.stop_camera()
            save_widget.on_toggle(True, self.selected_style)
            self.window().show_save_setting()
        else:
            self.stop_camera()
            save_widget.generated_image = None
            save_widget.selected_style = None
            self.window().show_save_setting()
