import cv2
import numpy as np
import glob
import os
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QButtonGroup, QWidget, QLabel, QVBoxLayout, QPushButton, QTextEdit, QHBoxLayout, QSizePolicy, QGridLayout
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

        # Taille = 70% largeur, 65% hauteur de la fenêtre parente, minimum 700x700
        if parent:
            pw, ph = parent.width(), parent.height()
            w, h = max(int(pw * 0.7), 700), max(int(ph * 0.65), 700)
            y_offset = int(ph * 0.08)
            self.setFixedSize(w, h)
            self.move(
                parent.x() + (pw - w) // 2,
                parent.y() + (ph - h) // 2 - y_offset
            )
        else:
            self.setFixedSize(700, 700)

        # Layout principal en grille avec marges
        grid = QGridLayout(self)
        grid.setContentsMargins(40, 32, 40, 32)
        grid.setSpacing(24)
        grid.setRowStretch(0, 0)
        grid.setRowStretch(1, 2)  # Plus d'espace pour le QR code
        grid.setRowStretch(2, 1)  # Moins d'espace pour le texte
        grid.setRowStretch(3, 0)

        row = 0

        # --- Ajout du message configurable en haut ---
        if VALIDATION_OVERLAY_MESSAGE:
            msg_label = QLabel(VALIDATION_OVERLAY_MESSAGE, self)
            msg_label.setStyleSheet("color: black; font-size: 22px; font-weight: bold; background: transparent;")
            msg_label.setAlignment(Qt.AlignCenter)
            grid.addWidget(msg_label, row, 0, 1, 1, alignment=Qt.AlignCenter)
            row += 1

        # Image centrée (sera remplacée dynamiquement)
        self.img_label = QLabel(self)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setMinimumSize(220, 220)  # Réduit la taille minimale du QR code
        self.img_label.setMaximumSize(260, 260)  # Limite la taille maximale aussi
        self.img_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        grid.addWidget(self.img_label, row, 0, 1, 1, alignment=Qt.AlignCenter)
        row += 1

        # Texte (rules.txt) en dessous
        text_edit = QTextEdit(self)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("background: transparent; color: black; font-size: 18px; border: none;")
        text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        text_edit.setMinimumHeight(80)
        text_edit.setMaximumHeight(180)
        text_edit.setMinimumWidth(int(self.width() * 0.85))
        try:
            with open("rules.txt", "r") as f:
                rules_text = f.read()
                html = f'<div align="center">{rules_text.replace(chr(10), "<br>")}</div>'
                text_edit.setHtml(html)
        except Exception as e:
            text_edit.setText(f"Error loading rules: {str(e)}")
        grid.addWidget(text_edit, row, 0, 1, 1)
        row += 1

        # Boutons en ligne (Valider + Fermer)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(32)

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

        btn_container = QWidget(self)
        btn_container.setLayout(btn_row)
        grid.addWidget(btn_container, row, 0, 1, 1, alignment=Qt.AlignCenter)

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
        # Affiche le QR code à une taille réduite
        pix = QPixmap.fromImage(qimg)
        target_size = min(self.img_label.width(), self.img_label.height(), 240)
        self.img_label.setPixmap(pix.scaled(
            target_size, target_size,
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
        self._generation_in_progress = False

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

    def showEvent(self, event):
        # Synchronise le bouton de style sélectionné avec self.selected_style
        super().showEvent(event)
        if hasattr(self, 'button_group') and self.selected_style:
            for btn in self.button_group.buttons():
                btn.setChecked(btn.text() == self.selected_style)
                # Réactive les boutons si besoin
                btn.setEnabled(not self._generation_in_progress)
        self.show_image()
        # Nettoyage des threads terminés pour éviter fuite mémoire
        self._cleanup_thread()

    def show_loading(self):
        if not self.loading_overlay:
            self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.show()
        self.loading_overlay.raise_()

    def hide_loading(self):
        if self.loading_overlay:
            self.loading_overlay.hide()

    def on_toggle(self, checked: bool, style_name: str):
        if self._generation_in_progress:
            return
        if checked:
            self.selected_style = style_name
            self.generated_image = None
            self._set_style_buttons_enabled(False)
            self._generation_in_progress = True
            self.show_loading()
            # Nettoyage thread précédent si besoin
            self._cleanup_thread()
            self._thread = QThread()
            self._worker = GenerationWorker(style_name)
            self._worker.moveToThread(self._thread)
            self._thread.started.connect(self._worker.run)
            self._worker.finished.connect(self.on_generation_finished)
            self._worker.finished.connect(self._thread.quit)
            self._worker.finished.connect(self._worker.deleteLater)
            self._thread.finished.connect(self._thread.deleteLater)
            self._thread.finished.connect(self._on_thread_finished)
            self._thread.start()
        elif self._generation_in_progress:
            self._set_style_buttons_enabled(False)

    def _set_style_buttons_enabled(self, enabled: bool):
        if hasattr(self, 'button_group'):
            for btn in self.button_group.buttons():
                btn.setEnabled(enabled)

    def _cleanup_thread(self):
        # Libère proprement les threads terminés pour éviter accumulation
        if self._thread is not None:
            try:
                if self._thread.isRunning():
                    self._thread.requestInterruption()
                    self._thread.quit()
                    self._thread.wait()
            except Exception:
                pass
            self._thread = None
        self._worker = None

    def closeEvent(self, event):
        # S'assure que le thread est bien arrêté lors de la fermeture du widget
        self._cleanup_thread()
        super().closeEvent(event)

    def _on_thread_finished(self):
        # Nettoyage supplémentaire après la fin du thread
        self._thread = None
        self._worker = None

    def on_generation_finished(self, image_path):
        self._generation_in_progress = False
        self._set_style_buttons_enabled(True)
        self.hide_loading()
        # Nettoyage thread après génération
        self._on_thread_finished()
        if image_path and os.path.exists(image_path):
            img = cv2.imread(image_path)
            self.generated_image = ImageUtils.cv_to_qimage(img)
        else:
            self.generated_image = None
        self.show_image()

    def validate(self):
        # Arrête le thread de génération si en cours avant d'afficher l'overlay
        self._cleanup_thread()
        overlay = ValidationOverlay(self.window())
        overlay.show_gif_qrcode()
        overlay.show()

    def refuse(self):
        # Arrête le thread de génération si en cours avant de retourner à la caméra
        self._cleanup_thread()
        self.window().set_view(0)
