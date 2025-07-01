# main.py
from gui_classes.gui_object.constante import DEBUG
from PySide6.QtWidgets import QApplication
from gui_classes.gui_manager.window_manager import WindowManager
import sys

def main():    
    if DEBUG:
        print("[MAIN] Starting application with debug mode enabled.") 
    app = QApplication(sys.argv)
    manager = WindowManager()
    manager.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
