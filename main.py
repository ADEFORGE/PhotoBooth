# main.py
import sys
import cProfile
import pstats
from PySide6.QtWidgets import QApplication
from gui_mainwindow import MainWindow

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.showFullScreen()  # Affichage plein écran
    sys.exit(app.exec())

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()

    try:
        main()
    finally:
        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats("cumulative").print_stats(50)
