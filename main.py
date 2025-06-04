# main.py
import sys
import cProfile
import pstats
from PySide6.QtWidgets import QApplication
from gui_mainwindow import PhotoBoothApp

def main():
    app = QApplication(sys.argv)
    win = PhotoBoothApp()
    win.showFullScreen()
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
