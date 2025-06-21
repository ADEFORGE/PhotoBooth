# main.py
from constante import DEBUG

def main():
    import sys
    if DEBUG:
        print("[MAIN] Starting application with debug mode enabled.")
   
    from PySide6.QtWidgets import QApplication
    from window_manager import WindowManager

    app = QApplication(sys.argv)
    manager = WindowManager()
    manager.show()  # already full-screen in WindowManager.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
