# initialisation.py
import sys
from PySide6.QtWidgets import QApplication
from gui_main import MainWindow

def run():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.showFullScreen()
    sys.exit(app.exec())
