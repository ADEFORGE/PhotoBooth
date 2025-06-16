# main.py
from constante import DEBUG


def main():
    """Main entry point of the application."""
    import sys
    import cProfile
    import pstats

    if DEBUG:
        print("[MAIN] Starting application with debug mode enabled.")

    from PySide6.QtWidgets import QApplication
    from gui_mainwindow import MainWindow

    app = QApplication(sys.argv)
    win = MainWindow()
    win.showFullScreen()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
