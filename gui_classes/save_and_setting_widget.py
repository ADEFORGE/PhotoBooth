import cv2
import numpy as np
import glob
import os
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QButtonGroup, QWidget, QLabel, QVBoxLayout, QPushButton, QTextEdit, QHBoxLayout
from PySide6.QtGui import QPixmap, QColor, QPainter, QBrush, QPen
from PySide6.QtCore import QSize

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

class ValidationOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        # Taille = 50% de la fenêtre parente
        if parent:
            pw, ph = parent.width(), parent.height()
            w, h = int(pw * 0.5), int(ph * 0.5)
            self.setFixedSize(w, h)
            # Centre la fenêtre dans le parent
            self.move(
                parent.x() + (pw - w) // 2,
                parent.y() + (ph - h) // 2
            )
        else:
            self.setFixedSize(600, 400)

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)

        # Image centrée
        img_label = QLabel(self)
        pix = QPixmap("gui_template/image.png")
        img_label.setPixmap(pix.scaled(int(self.width()*0.7), int(self.height()*0.4), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        img_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(img_label, alignment=Qt.AlignCenter)

        # Texte (rules.txt) en dessous
        text_edit = QTextEdit(self)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("background: transparent; color: black; font-size: 18px; border: none;")
        try:
            with open("rules.txt", "r") as f:
                text_edit.setText(f.read())
        except Exception as e:
            text_edit.setText(f"Error loading rules: {str(e)}")
        layout.addWidget(text_edit, alignment=Qt.AlignCenter)

        # Boutons en ligne (Accept + Close)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(24)

        # Bouton accepter avec icône
        accept_btn = QPushButton(self)
        accept_btn.setFixedSize(56, 56)
        accept_btn.setStyleSheet(
            "QPushButton {"
            "background-color: rgba(255,255,255,0.7);"
            "border: 2px solid #fff;"
            "border-radius: 28px;"
            "}"
            "QPushButton:hover {"
            "background-color: #e0ffe0;"
            "}"
        )
        accept_icon = QPixmap("gui_template/btn_icons/accept.png")
        accept_btn.setIcon(QIcon(accept_icon))
        accept_btn.setIconSize(QSize(32, 32))
        accept_btn.clicked.connect(self.close)
        btn_row.addWidget(accept_btn)

        # Bouton close avec icône
        close_btn = QPushButton(self)
        close_btn.setFixedSize(56, 56)
        close_btn.setStyleSheet(
            "QPushButton {"
            "background-color: rgba(255,255,255,0.7);"
            "border: 2px solid #fff;"
            "border-radius: 28px;"
            "}"
            "QPushButton:hover {"
            "background-color: #ffe0e0;"
            "}"
        )
        close_icon = QPixmap("gui_template/btn_icons/close.png")
        close_btn.setIcon(QIcon(close_icon))
        close_btn.setIconSize(QSize(32, 32))
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(10, 10, -10, -10)
        # Fond blanc semi-transparent
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 30, 30)
        # Bord blanc opaque
        pen = QPen(QColor(255, 255, 255, 255), 6)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, 30, 30)

class SaveAndSettingWidget(PhotoBoothBaseWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.selected_style = None
        self.generated_image = None
        self._thread = None
        self._worker = None

        # Première ligne : boutons Validate, Refuse (suppression du bouton take_selfie)
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
        # Affiche l'overlay de validation au lieu d'une box
        overlay = ValidationOverlay(self.window())
        overlay.show()

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
