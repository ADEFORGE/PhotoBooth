# gui_app.py
# Nouveau point d'entrée principal pour l'application PhotoBooth
# Utilise PhotoBoothBaseWidget comme gestionnaire de vues

import sys
from PySide6.QtWidgets import QApplication
from gui_classes.gui_base_widget import PhotoBoothBaseWidget
from gui_classes.welcome_widget import WelcomeWidget
from gui_classes.photobooth import PhotoBooth

def run_app():
    app = QApplication(sys.argv)
    base = PhotoBoothBaseWidget()
    base.add_view(WelcomeWidget(base), 0)
    base.add_view(PhotoBooth(base), 1)
    base.set_view(0, initial=True)
    base.showFullScreen()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_app()
