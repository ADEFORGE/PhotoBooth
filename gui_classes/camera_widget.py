# gui_classes/camerawidget.py
import cv2
import os
from PySide6.QtCore import QTimer, Qt, QThread, Signal, QObject
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QPushButton, QApplication
from gui_classes.gui_base_widget import PhotoBoothBaseWidget, GenerationWorker
from constante import CAMERA_ID, dico_styles
from comfy_classes.comfy_class_API_test_GUI import ImageGeneratorAPIWrapper
from gui_classes.image_utils import ImageUtils  # Add this import
from gui_classes.loading_overlay import LoadingOverlay
from gui_classes.btn import Btns
import objgraph


class CameraWidget(PhotoBoothBaseWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.cap = None
        self.timer = QTimer(self, timeout=self.update_frame)
        self.selected_style = None  # Style sélectionné
        self.loading_overlay = None

        # Utilisation de Btns pour les boutons
        from constante import dico_styles
        # Configure les boutons avec les styles disponibles
        self.setup_buttons(
            style1_names=["take_selfie"],
            style2_names=list(dico_styles.keys()),
            slot_style1=self.capture,
            slot_style2=lambda checked, btn=None: self.on_toggle(checked, btn.text() if btn else None)
        )
        self.overlay_widget.raise_()
        self.btns.raise_()  # Force les boutons au premier plan

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

        # Sauvegarder l'image capturée avant tout
        input_path = "../ComfyUI/input/input.png"
        cv2.imwrite(input_path, frame)

        # Convertir pour l'affichage
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
        self.window().captured_image = qimg

        save_widget = self.window().save_setting_widget
        
        if self.selected_style:
            self.show_loading()
            self._thread = QThread()
            self._worker = GenerationWorker(self.selected_style)  # Ne pas passer l'image
            self._worker.moveToThread(self._thread)
            self._thread.started.connect(self._worker.run)
            self._worker.finished.connect(self.on_generation_finished)
            self._worker.finished.connect(self.hide_loading)
            self._worker.finished.connect(self._thread.quit)
            self._worker.finished.connect(self._worker.deleteLater)
            self._thread.finished.connect(self._thread.deleteLater)
            self._thread.start()
        else:
            self.stop_camera()
            save_widget.generated_image = None
            save_widget.selected_style = None
            self.window().show_save_setting()

    def on_generation_finished(self, qimg):
        self.stop_camera()
        if qimg and not qimg.isNull():
            self.window().save_setting_widget.generated_image = qimg
            self.window().save_setting_widget.selected_style = self.selected_style
        else:
            self.window().save_setting_widget.generated_image = None
            self.window().save_setting_widget.selected_style = None
        self.window().show_save_setting()

    def cleanup(self):
        if hasattr(self, "btns") and self.btns:
            self.btns.cleanup()
            self.btns = None
        # ...existing cleanup code...

    def showEvent(self, event):
        super().showEvent(event)
        if self.btns:
            self.btns.raise_()  # S'assure que les boutons sont visibles
