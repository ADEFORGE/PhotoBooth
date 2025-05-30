# gui_classes/resultwidget.py
from PySide6.QtWidgets import QWidget, QLabel, QGridLayout, QSizePolicy, QApplication, QPushButton
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt
from main_GUI import MainGUI

class LoadWidget(MainGUI):
    def __init__(self, parent=None):
        super().__init__()
        self.clear_buttons()
        # Affiche un GIF animé dans le label central
        self.show_gif("./gui_template/load.gif")
