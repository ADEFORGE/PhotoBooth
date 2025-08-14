# main.py

import logging
import sys
import traceback

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logging.getLogger().addHandler(console_handler)

logger = logging.getLogger(__name__)

def log_uncaught_exceptions(exctype, value, tb):
    logger = logging.getLogger(__name__)
    logger.error("Uncaught exception", exc_info=(exctype, value, tb))

sys.excepthook = log_uncaught_exceptions

from gui_classes.gui_object.constant import DEBUG
from PySide6.QtWidgets import QApplication
from gui_classes.gui_manager.window_manager import WindowManager

def main():    
    if DEBUG:
        logger.info("[MAIN] Starting application with debug mode enabled.")
    app = QApplication(sys.argv)
    manager = WindowManager()
    manager.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
