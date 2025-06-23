import sys
import os
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel

from gui_classes.background_manager import BackgroundManager
from gui_classes.scroll_widget import InfiniteScrollWidget
from gui_classes.language_manager import language_manager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        central = QWidget()
        self.setCentralWidget(central)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("")

        # Utiliser BackgroundManager pour afficher le retour caméra en fond
        self.background_manager = BackgroundManager(self)
        cam_image_path = os.path.join(os.path.dirname(__file__), "./gui_template/nocam.png")
        if os.path.exists(cam_image_path):
            cam_pixmap = QPixmap(cam_image_path)
            self.background_manager.set_camera_pixmap(cam_pixmap)
        self.bg_label = QLabel(central)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.bg_label.setScaledContents(True)
        bg = self.background_manager.get_background()
        if bg:
            self.bg_label.setPixmap(bg.scaled(self.width(), self.height(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            self.bg_label.setStyleSheet("background: black;")
        self.bg_label.lower()
        self.bg_label.show()

        # Overlay transparent pour le scroll qui prend toute la fenêtre
        self.scroll_overlay = QWidget(self)
        self.scroll_overlay.setAttribute(Qt.WA_TranslucentBackground)
        self.scroll_overlay.setStyleSheet("background: transparent;")
        self.scroll_overlay.setGeometry(0, 0, self.width(), self.height())
        self.scroll_overlay.raise_()
        self.scroll_overlay.show()
        overlay_layout = QVBoxLayout(self.scroll_overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)
        self.scroll_widget = InfiniteScrollWidget(
            './gui_template/sleep_picture',
            scroll_speed=2,
            fps=60,
            margin_x=1,
            margin_y=1,
            angle=15
        )
        overlay_layout.addWidget(self.scroll_widget)
        self.scroll_widget.start()
        QTimer.singleShot(3000, lambda: self.scroll_widget.begin_stop(6))
        QTimer.singleShot(15000, lambda: self.scroll_widget.start())

        # Ajout des labels et du bouton (par-dessus le scroll)
        self.text_overlay = QWidget(self)
        self.text_overlay.setAttribute(Qt.WA_TranslucentBackground)
        self.text_overlay.setGeometry(0, 0, self.width(), self.height())
        self.text_overlay.raise_()
        self.text_overlay.show()
        text_layout = QVBoxLayout(self.text_overlay)
        text_layout.setContentsMargins(40, 40, 40, 40)
        text_layout.setSpacing(30)
        text_layout.setAlignment(Qt.AlignCenter)

        self.title_label = QLabel(self.text_overlay)
        self.title_label.setStyleSheet("color: white; font-size: 72px; font-weight: bold; font-family: Arial;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)
        text_layout.addWidget(self.title_label)

        self.message_label = QLabel(self.text_overlay)
        self.message_label.setStyleSheet("color: white; font-size: 36px; font-family: Arial;")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        text_layout.addWidget(self.message_label)

        self.camera_btn = QLabel("[CAMERA]", self.text_overlay)
        self.camera_btn.setStyleSheet("color: white; font-size: 32px; background: #222; border-radius: 20px; padding: 20px; text-align: center;")
        self.camera_btn.setAlignment(Qt.AlignCenter)
        text_layout.addWidget(self.camera_btn)

        language_manager.subscribe(self.update_language)
        self.update_language()

    def update_language(self):
        texts = language_manager.get_texts('WelcomeWidget') or {}
        self.title_label.setText(texts.get('title', 'Bienvenue'))
        self.message_label.setText(texts.get('message', ''))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scroll_overlay.setGeometry(0, 0, self.width(), self.height())
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.text_overlay.setGeometry(0, 0, self.width(), self.height())
        bg = self.background_manager.get_background()
        if bg:
            self.bg_label.setPixmap(bg.scaled(self.width(), self.height(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))

    def closeEvent(self, event):
        language_manager.unsubscribe(self.update_language)
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication([])
    win = MainWindow()
    win.show()
    app.exec()
