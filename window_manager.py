# file: window_manager.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QApplication
from PySide6.QtCore import Qt
from gui_classes.photobooth import PhotoBooth
from gui_classes.sleepscreen_window import SleepScreenWindow
from gui_classes.background_manager import BackgroundManager
from constante import WINDOW_STYLE, DEBUG
import sys

DEBUG_MANAGER_WINDOWS = False  # ou True ou DEBUG

class WindowManager(QWidget):
    """
    Gère la navigation entre les écrans (veille et photobooth) et l'overlay de fond animé.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhotoBooth")
        self.setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Instancie le BackgroundManager pour gérer le scroll overlay
        self.background_manager = BackgroundManager()

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Stacked widget
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        layout.addWidget(self.stack)

        # Widgets enregistrés
        self.widgets = {
            0: SleepScreenWindow(self),
            1: PhotoBooth(self)
        }
        for w in self.widgets.values():
            self.stack.addWidget(w)

        # Variable pour transition
        self._pending_index = None

        # Affiche la vue initiale (veille)
        self.set_view(0, initial=True)
        # Démarre le scroll overlay au démarrage
        self.background_manager.start_scroll(self, on_started=None)

    def set_view(self, index: int, initial=False):
        """
        Change la page courante (0=veille, 1=photobooth).
        Nettoie l'ancienne vue et initialise la nouvelle.
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
        # Force le plein écran à chaque changement de vue
        self.showFullScreen()
        if DEBUG_MANAGER_WINDOWS:
            print(f"[WindowManager] switched to {type(new_widget).__name__}")
        # Appel on_enter si défini
        if hasattr(new_widget, 'on_enter'):
            new_widget.on_enter()
        # Gère le scroll overlay selon la vue
        if index == 0:
            # Sur l'écran de veille, démarre le scroll
            self.background_manager.start_scroll(self, on_started=None)

    def start(self):
        # Toujours forcer le plein écran au démarrage
        self.showFullScreen()
        if DEBUG_MANAGER_WINDOWS:
            print("[WindowManager] Application started in full screen")

    def start_change_view(self, index=0, callback=None):
        """
        Démarre la préparation du changement vers la vue `index`.
        On stoppe d'abord le scroll overlay (raise_), on change la vue, puis on lance l'animation de fin du scroll.
        """
        current_index = self.stack.currentIndex()
        if index == current_index or index not in self.widgets:
            return
        self._pending_index = index

        self.background_manager.stop_scroll(set_view=lambda: self.set_view(index))


    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Si l'overlay de scroll existe, on le resize dynamiquement
        if hasattr(self.background_manager, 'scroll_overlay') and self.background_manager.scroll_overlay:
            self.background_manager.scroll_overlay.setGeometry(0, 0, self.width(), self.height())


def main():
    app = QApplication(sys.argv)
    manager = WindowManager()
    manager.start()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
