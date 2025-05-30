# main.py
import sys
from PySide6.QtWidgets import QApplication
from gui_mainwindow import PhotoBoothApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PhotoBoothApp()
    win.showFullScreen()
    sys.exit(app.exec())
