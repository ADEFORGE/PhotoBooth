import cv2
import numpy as np
import glob
import os
import objgraph
import gc
from PySide6.QtCore import Qt, QThread, Signal, QObject, QEvent  # Ajout de QEvent
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QButtonGroup, QWidget, QLabel, QVBoxLayout, QPushButton, QTextEdit, QHBoxLayout, QSizePolicy, QGridLayout
from PySide6.QtGui import QPixmap, QColor, QPainter, QBrush, QPen
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtGui import QMovie  # <-- Ajouté ici

from gui_classes.gui_base_widget import PhotoBoothBaseWidget, GenerationWorker
from constante import dico_styles, VALIDATION_OVERLAY_MESSAGE  # Ajout de VALIDATION_OVERLAY_MESSAGE
from gui_classes.more_info_box import InfoDialog
from constante import BUTTON_STYLE
from comfy_classes.comfy_class_API import ImageGeneratorAPIWrapper
from gui_classes.qrcode_utils import QRCodeGenerator
from PySide6.QtGui import QImage
import io
from gui_classes.image_utils import ImageUtils
from gui_classes.loading_overlay import LoadingOverlay


DEBUG_MEM = False  # Passe à True pour activer objgraph/gc.collect()

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
            parent.installEventFilter(self)
        else:
            self.setFixedSize(700, 700)

        # Layout principal en grille avec marges
        grid = QGridLayout(self)
        grid.setContentsMargins(40, 32, 40, 32)
        grid.setSpacing(24)
        grid.setRowStretch(0, 0)
        grid.setRowStretch(1, 2)
        grid.setRowStretch(2, 1)
        grid.setRowStretch(3, 0)

        row = 0

        # Message configurable en haut
        if VALIDATION_OVERLAY_MESSAGE:
            msg_label = QLabel(VALIDATION_OVERLAY_MESSAGE, self)
            msg_label.setStyleSheet("color: black; font-size: 22px; font-weight: bold; background: transparent;")
            msg_label.setAlignment(Qt.AlignCenter)
            grid.addWidget(msg_label, row, 0, 1, 1, alignment=Qt.AlignCenter)
            row += 1

        # Image centrée (QR ou GIF)
        self.img_label = QLabel(self)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setMinimumSize(220, 220)
        self.img_label.setMaximumSize(260, 260)
        self.img_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        grid.addWidget(self.img_label, row, 0, 1, 1, alignment=Qt.AlignCenter)
        row += 1

        # Précharge le QMovie une seule fois
        self._movie = QMovie("gui_template/load.gif")
        self.img_label.setMovie(self._movie)

        # Texte (rules.txt)
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
        validate_btn.clicked.connect(self.on_validate_clicked)  # Change ici
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
        refuse_btn.clicked.connect(self.on_refuse_clicked)
        btn_row.addWidget(refuse_btn)

        btn_container = QWidget(self)
        btn_container.setLayout(btn_row)
        grid.addWidget(btn_container, row, 0, 1, 1, alignment=Qt.AlignCenter)

    def show(self):
        if self._movie:
            self._movie.start()
        super().show()

    def hide(self):
        if self._movie:
            self._movie.stop()
        super().hide()

    def eventFilter(self, watched, event):
        if watched is self.parent() and event.type() == QEvent.Resize:
            pw, ph = watched.width(), watched.height()
            w, h = max(int(pw * 0.7), 700), max(int(ph * 0.65), 700)
            y_offset = int(ph * 0.08)
            self.setFixedSize(w, h)
            self.move(
                watched.x() + (pw - w) // 2,
                watched.y() + (ph - h) // 2 - y_offset
            )
        return super().eventFilter(watched, event)

    def show_default_image(self):
        # Affiche le GIF de chargement (préchargé)
        if self._movie:
            self.img_label.setMovie(self._movie)
            self._movie.start()

    def display_qrcode(self, qimg: QImage):
        # Stoppe le GIF et affiche le QR code
        if self._movie:
            self._movie.stop()
        self.img_label.setMovie(None)
        if not qimg or qimg.isNull():
            self.img_label.setText("Erreur QR code")
            return
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
        painter.fillRect(rect, QColor(255, 255, 255, 220))
        pen = QPen(QColor(255, 255, 255), 6)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, 30, 30)

    def closeEvent(self, event):
        if self._movie:
            self._movie.stop()
        super().closeEvent(event)

    def on_validate_clicked(self):
        """Gère le clic sur le bouton valider"""
        if self.parent():
            self.parent().window().set_view(1)  # Retour à la caméra
        self.close()
        
    def on_refuse_clicked(self):
        """Gère le clic sur le bouton refuser"""
        self.close()

    def show_gif_qrcode(self):
        """Affiche le GIF puis le QR code"""
        self.show_default_image()
        # Lance la génération du QR code en arrière-plan
        self.qr_thread = QThread()
        self.qr_worker = QRCodeWorker()
        self.qr_worker.moveToThread(self.qr_thread)
        self.qr_thread.started.connect(self.qr_worker.run)
        self.qr_worker.finished.connect(self.display_qrcode)
        self.qr_worker.finished.connect(self.qr_thread.quit)
        self.qr_worker.finished.connect(self.qr_worker.deleteLater)
        self.qr_thread.finished.connect(self.qr_thread.deleteLater)
        self.qr_thread.start()

class SaveAndSettingWidget(PhotoBoothBaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_style = None
        self.generated_image = None
        self._thread = None
        self._worker = None
        self.loading_overlay = None  # On ne crée pas l'overlay ici
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

    def _create_loading_overlay(self):
        """Crée ou recrée l'overlay si nécessaire"""
        if not hasattr(self, 'loading_overlay') or self.loading_overlay is None:
            self.loading_overlay = LoadingOverlay(self)
            self.loading_overlay.hide()

    def _ensure_overlay(self):
        """Assure qu'un overlay valide existe"""
        if self.loading_overlay is None:
            self.loading_overlay = LoadingOverlay(self)
            self.loading_overlay.resize(self.size())
        return self.loading_overlay

    def show_loading(self):
        overlay = self._ensure_overlay()
        overlay.resize(self.size())  # Force la taille
        overlay.show()
        overlay.raise_()

    def hide_loading(self):
        if self.loading_overlay is not None:
            self.loading_overlay.hide()

    def on_toggle(self, checked: bool, style_name: str):
        # Appelle la méthode parente avec generate_image=True
        super().on_toggle(checked, style_name, generate_image=True)

    def on_generation_finished(self, qimg):
        self._generation_in_progress = False
        self._set_style_buttons_enabled(True)
        self.hide_loading()
        self.kill_generation_thread()  # <-- Ajout ici
        if qimg and not qimg.isNull():
            self.generated_image = qimg
        else:
            self.generated_image = None
        self.show_image()

    def cleanup_all_threads_and_overlays(self):
        print("[CLEANUP] Nettoyage threads/overlays SaveAndSettingWidget")
        if self.loading_overlay is not None:
            self.hide_loading()
        # ...autres nettoyages (thread, worker, etc.)...
        if DEBUG_MEM:
            import gc, objgraph
            gc.collect()
            objgraph.show_growth(limit=10)

    def closeEvent(self, event):
        # Ne tente pas d'arrêter brutalement le thread, laisse Qt le gérer
        # On ne supprime pas la référence si le thread tourne encore
        self._cleanup_thread()
        super().closeEvent(event)

    def _on_thread_finished(self):
        # Nettoyage supplémentaire après la fin du thread
        # On ne supprime la référence que si le thread est terminé
        if self._thread and not self._thread.isRunning():
            self._thread = None
            self._worker = None

    def validate(self):
        self._cleanup_thread()
        overlay = ValidationOverlay(self.window())
        overlay.show_gif_qrcode()
        overlay.show()

    def refuse(self):
        # Nettoyage radical sur refuse
        self.cleanup_all_threads_and_overlays()
        self.window().set_view(0)

    def _set_style_buttons_enabled(self, enabled: bool):
        if hasattr(self, 'button_group'):
            for btn in self.button_group.buttons():
                btn.setEnabled(enabled)

    def _cleanup_thread(self):
        if hasattr(self, "_thread") and self._thread is not None:
            try:
                print(f"[CLEANUP] _cleanup_thread: thread running? {self._thread.isRunning()}")
                if not self._thread.isRunning():
                    print(f"[CLEANUP] Thread terminé, suppression références")
                    self._thread = None
                    self._worker = None
            except Exception as e:
                print(f"[CLEANUP] Exception in _cleanup_thread: {e}")

    def cleanup(self):
        print("[CLEANUP] SaveAndSettingWidget: Début du nettoyage")

        # Déconnecte les signaux des boutons si besoin
        if hasattr(self, 'button_group'):
            for btn in self.button_group.buttons():
                try:
                    btn.clicked.disconnect()
                except TypeError:
                    pass

        # Déconnecte les signaux du worker/thread si besoin
        if hasattr(self, "_worker") and self._worker:
            try:
                self._worker.finished.disconnect()
            except Exception:
                pass

        # Arrête le thread de génération s'il existe
        if hasattr(self, "_thread") and self._thread and self._thread.isRunning():
            print("[CLEANUP] Tentative d'arrêt du thread de génération...")
            self._thread.quit()
            self._thread.wait(2000)
            self._thread.deleteLater()
            if self._thread.isRunning():
                print("[CLEANUP] Échec d'arrêt du thread.")
            else:
                print("[CLEANUP] Thread arrêté avec succès.")

        # Ne pas supprimer l'overlay, juste le cacher
        if hasattr(self, "loading_overlay") and self.loading_overlay:
            self.loading_overlay.hide()
            
        # Libère les autres références
        self._thread = None
        self._worker = None
        # Ne pas mettre loading_overlay à None
        
        # Forcer le garbage collector et inspecter les références
        import gc, objgraph
        gc.collect()
        overlays = objgraph.by_type('LoadingOverlay')
        if overlays:
            objgraph.show_backrefs([overlays[-1]], max_depth=3, filename='refs_loading_overlay.png')
            print("[DEBUG] Graphique généré: refs_loading_overlay.png")

        print("[CLEANUP] SaveAndSettingWidget: Nettoyage terminé")

        # Forcer le garbage collector et afficher la croissance des objets
        gc.collect()
        objgraph.show_growth(limit=10)

        # Traque des overlays orphelins
        overlays = objgraph.by_type('LoadingOverlay')
        if overlays:
            print(f"[DEBUG] Nombre de LoadingOverlay vivants: {len(overlays)}")
            objgraph.show_backrefs([overlays[-1]], max_depth=3, filename='loading_overlay_refs.png')
            print("[DEBUG] Graphique généré: loading_overlay_refs.png")

    def __del__(self):
        print(f"[DEL] SaveAndSettingWidget détruit: {id(self)}")
        if hasattr(self, 'button_group'):
            for btn in self.button_group.buttons():
                try:
                    btn.clicked.disconnect()
                except Exception:
                    pass
        if hasattr(self, "_worker") and self._worker:
            try:
                self._worker.finished.disconnect()
            except Exception:
                pass

    def kill_generation_thread(self):
        """Tente d'arrêter et de supprimer complètement le thread de génération."""
        print("[THREAD] Tentative de kill du thread de génération")
        if hasattr(self, "_thread") and self._thread:
            try:
                if self._thread.isRunning():
                    print("[THREAD] Thread encore actif, on quitte...")
                    self._thread.quit()
                    self._thread.wait(2000)
                self._thread.deleteLater()
            except Exception as e:
                print(f"[THREAD] Exception lors du kill: {e}")
            finally:
                self._thread = None
        if hasattr(self, "_worker") and self._worker:
            try:
                self._worker.deleteLater()
            except Exception:
                pass
            self._worker = None
        import gc
        gc.collect()
        print("[THREAD] Thread et worker supprimés et GC forcé")
