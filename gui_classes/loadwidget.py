# gui_classes/resultwidget.py
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QFileDialog, QGridLayout, QSizePolicy
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class LoadWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)        
        layout = QGridLayout(self)        

        self.load_animation_label = QLabel(alignment=Qt.AlignCenter)
        self.load_animation_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        pixmap = QPixmap("./gui_template/load.gif")
        pixmap = pixmap.scaled(self.load_animation_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.load_animation_label.setPixmap(pixmap)

        layout.addWidget(self.load_animation_label, 0, 0, 1, 2)

    def fct(self):
        return
