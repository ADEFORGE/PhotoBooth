# gui_classes/camerawidget.py
import cv2
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QPushButton, QApplication
from gui_classes.gui_base_widget import PhotoBoothBaseWidget
from constante import CAMERA_ID, dico_styles

class CameraWidget(PhotoBoothBaseWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.cap = None
        self.timer = QTimer(self, timeout=self.update_frame)

        # Bouton principal sur la première ligne
        self.first_buttons = [
            ("📸 Take Picture", "capture")
        ]
        # Boutons de style sur la seconde ligne
        self.button_config = {}
        for style in dico_styles:
            self.button_config[style] = ("toggle_style", True)  # Toggle pour chaque style

        self.setup_buttons_from_config()


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

    def capture(self):
        if not self.cap:
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
        self.window().captured_image = qimg
        self.stop_camera()
        self.window().show_choose_style()

    def on_toggle(self, checked: bool, style_name: str):
        # Optionnel : gestion du style sélectionné si besoin
        if checked:
            self.selected_style = style_name
