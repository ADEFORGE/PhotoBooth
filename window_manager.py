# file: window_manager.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QApplication
from PySide6.QtCore import Qt
from gui_classes.photobooth import PhotoBooth
from gui_classes.sleepscreen_window import SleepScreenWindow
from constante import WINDOW_STYLE, DEBUG
import os, sys

DEBUG_MANAGER_WINDOWS = False # ou True ou DEBUG

class WindowManager(QWidget):
    """
    Gère la navigation entre les écrans (veille et photobooth).
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhotoBooth")
        self.setStyleSheet(WINDOW_STYLE)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Stacked widget
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(WINDOW_STYLE)
        layout.addWidget(self.stack)

        # Widgets enregistrés
        self.widgets = {
            0: SleepScreenWindow(self),
            1: PhotoBooth(self)
        }
        for w in self.widgets.values():
            self.stack.addWidget(w)

        # Affiche la vue initiale (veille)
        self.set_view(0, initial=True)

    def set_view(self, index: int, initial=False):
        """
        Change la page courante (0=veille, 1=photobooth).
        """
        if DEBUG_MANAGER_WINDOWS:
            print(f"[WindowManager] set_view(index={index}, initial={initial})")
        # Nettoyage de l'écran actuel
        if not initial:
            current = self.stack.currentWidget()
            if DEBUG_MANAGER_WINDOWS:
                print(f"[WindowManager] cleaning up {type(current).__name__}")
            if hasattr(current, 'on_leave'):
                current.on_leave()
            if hasattr(current, 'cleanup'):
                current.cleanup()

        # Changement de vue
        new_widget = self.widgets[index]
        self.stack.setCurrentWidget(new_widget)
        if DEBUG_MANAGER_WINDOWS:
            print(f"[WindowManager] switched to {type(new_widget).__name__}")
        # Appel on_enter si défini
        if hasattr(new_widget, 'on_enter'):
            new_widget.on_enter()

    def show(self):
        super().showFullScreen()
        if DEBUG_MANAGER_WINDOWS:
            print("[WindowManager] Application started in full screen")


def main():
    app = QApplication(sys.argv)
    manager = WindowManager()
    manager.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
