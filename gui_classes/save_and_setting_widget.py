import cv2
import numpy as np
import glob
import os
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QButtonGroup, QWidget, QLabel, QVBoxLayout, QPushButton, QTextEdit, QHBoxLayout
from PySide6.QtWidgets import QSizePolicy  # <-- Ajouté ici
from PySide6.QtGui import QPixmap, QColor, QPainter, QBrush, QPen
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtGui import QMovie  # <-- Ajouté ici

from gui_classes.gui_base_widget import PhotoBoothBaseWidget
from constante import dico_styles, VALIDATION_OVERLAY_MESSAGE  # Ajout de VALIDATION_OVERLAY_MESSAGE
from gui_classes.more_info_box import InfoDialog
from constante import BUTTON_STYLE
from comfy_classes.comfy_class_API_test_GUI import ImageGeneratorAPIWrapper
from gui_classes.qrcode_utils import QRCodeGenerator
from PySide6.QtGui import QImage
import io
from gui_classes.image_utils import ImageUtils
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

class QRCodeWorker(QObject):
    finished = Signal(QImage)

    def run(self):
        # Génère le QR code (toujours la même URL pour le test)
        img = QRCodeGenerator.generate_qrcode("https://youtu.be/xvFZjo5PgG0?si=pp6hBg7rL4zineRX")
        # Convertit PIL.Image en QImage
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        qimg = QImage.fromData(buf.getvalue())
        self.finished.emit(qimg)

class ValidationOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        # Taille = 60% de la fenêtre parente, minimum 600x600 pour le QR code
        if parent:
            pw, ph = parent.width(), parent.height()
            w, h = max(int(pw * 0.6), 600), max(int(ph * 0.6), 600)
            self.setFixedSize(w, h)
            self.move(
                parent.x() + (pw - w) // 2,
                parent.y() + (ph - h) // 2
            )
        else:
            self.setFixedSize(600, 600)

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)

        # --- Ajout du message configurable en haut ---
        if VALIDATION_OVERLAY_MESSAGE:
            msg_label = QLabel(VALIDATION_OVERLAY_MESSAGE, self)
            msg_label.setStyleSheet("color: black; font-size: 22px; font-weight: bold; background: transparent;")
            msg_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(msg_label, alignment=Qt.AlignCenter)

        # Image centrée (sera remplacée dynamiquement)
        self.img_label = QLabel(self)
        self.img_label.setAlignment(Qt.AlignCenter)
        # Largeur/hauteur minimum augmentée pour le QR code
        self.img_label.setMinimumSize(350, 350)
        layout.addWidget(self.img_label, alignment=Qt.AlignCenter)
        self._movie = None

        # Texte (rules.txt) en dessous
        text_edit = QTextEdit(self)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("background: transparent; color: black; font-size: 18px; border: none;")
        text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        text_edit.setMinimumHeight(int(self.height() * 0.18))
        text_edit.setMinimumWidth(int(self.width() * 0.8))
        try:
            with open("rules.txt", "r") as f:
                rules_text = f.read()
                html = f'<div align="center">{rules_text.replace(chr(10), "<br>")}</div>'
                text_edit.setHtml(html)
        except Exception as e:
            text_edit.setText(f"Error loading rules: {str(e)}")
        layout.addWidget(text_edit, stretch=2, alignment=Qt.AlignCenter)

        # Boutons en ligne (Valider + Fermer)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(24)

        # Bouton valider (passe à la caméra)
        validate_btn = QPushButton(self)
        validate_btn.setFixedSize(56, 56)
        validate_btn.setStyleSheet(
            "QPushButton {"
            "background-color: rgba(255,255,255,0.7);"
            "border: 2px solid #fff;"
            "border-radius: 28px;"
            "}"
            "QPushButton:hover {"
            "background-color: #e0ffe0;"
            "}"
        )
        validate_icon = QPixmap("gui_template/btn_icons/accept.png")
        validate_btn.setIcon(QIcon(validate_icon))
        validate_btn.setIconSize(QSize(32, 32))
        validate_btn.clicked.connect(self.go_to_camera)
        btn_row.addWidget(validate_btn)

        # Bouton refuser (retour caméra)
        refuse_btn = QPushButton(self)
        refuse_btn.setFixedSize(56, 56)
        refuse_btn.setStyleSheet(
            "QPushButton {"
            "background-color: rgba(255,255,255,0.7);"
            "border: 2px solid #fff;"
            "border-radius: 28px;"
            "}"
            "QPushButton:hover {"
            "background-color: #ffe0e0;"
            "}"
        )
        refuse_icon = QPixmap("gui_template/btn_icons/close.png")
        refuse_btn.setIcon(QIcon(refuse_icon))
        refuse_btn.setIconSize(QSize(32, 32))
        refuse_btn.clicked.connect(self.go_to_camera)
        btn_row.addWidget(refuse_btn)

        layout.addLayout(btn_row)

        self.show_gif_qrcode()

    def go_to_camera(self):
        self.close()
        if self.parent() is not None:
            self.parent().set_view(0)  # 0 = vue caméra

    def show_default_image(self):
        # Affiche le GIF de chargement par défaut
        self._movie = QMovie("gui_template/load.gif")
        self.img_label.setMovie(self._movie)
        self._movie.start()

    def start_qrcode_thread(self):
        self.show_default_image()
        self.qr_thread = QThread(self)
        self.qr_worker = QRCodeWorker()
        self.qr_worker.moveToThread(self.qr_thread)
        self.qr_thread.started.connect(self.qr_worker.run)
        self.qr_worker.finished.connect(self.display_qrcode)
        self.qr_worker.finished.connect(self.qr_thread.quit)
        self.qr_worker.finished.connect(self.qr_worker.deleteLater)
        self.qr_thread.finished.connect(self.qr_thread.deleteLater)
        self.qr_thread.start()

    def show_gif_qrcode(self):
        # Affiche le GIF puis lance le thread QR code automatiquement
        self.show_default_image()
        self.qr_thread = QThread(self)
        self.qr_worker = QRCodeWorker()
        self.qr_worker.moveToThread(self.qr_thread)
        self.qr_thread.started.connect(self.qr_worker.run)
        self.qr_worker.finished.connect(self.display_qrcode)
        self.qr_worker.finished.connect(self.qr_thread.quit)
        self.qr_worker.finished.connect(self.qr_worker.deleteLater)
        self.qr_thread.finished.connect(self.qr_thread.deleteLater)
        self.qr_thread.start()

    def display_qrcode(self, qimg: QImage):
        self.img_label.setMovie(None)
        self._movie = None
        if not qimg or qimg.isNull():
            self.img_label.setText("Erreur QR code")
            return
        pix = QPixmap.fromImage(qimg)
        self.img_label.setPixmap(pix.scaled(
            int(self.width() * 0.5), int(self.height() * 0.5),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        self.img_label.repaint()

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
        self.loading_overlay = None

        # Première ligne : boutons accept/close pour utiliser les icônes existantes
        self.first_buttons = [
            ("accept", "validate"),   # Utilise accept.png
            ("close", "refuse")       # Utilise close.png
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

    def show_loading(self):
        if not self.loading_overlay:
            self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.show()
        self.loading_overlay.raise_()

    def hide_loading(self):
        if self.loading_overlay:
            self.loading_overlay.hide()

    def on_toggle(self, checked: bool, style_name: str):
        if checked:
            self.selected_style = style_name
            self.generated_image = None
            self.show_loading()
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
        self.hide_loading()
        if image_path and os.path.exists(image_path):
            img = cv2.imread(image_path)
            self.generated_image = ImageUtils.cv_to_qimage(img)
        else:
            self.generated_image = None
        self.show_image()

    def validate(self):
        # Affiche le GIF de chargement dans l'overlay principal (pas dans l'affichage principal)
        overlay = ValidationOverlay(self.window())
        overlay.show_gif_qrcode()  # Lance le GIF + thread QR code dans l'overlay directement
        overlay.show()

    def refuse(self):
        # Retourne à la caméra (CameraWidget)
        self.window().set_view(0)
