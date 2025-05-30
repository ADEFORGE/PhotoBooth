# gui_classes/resultwidget.py
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QFileDialog, QGridLayout, QSizePolicy
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class ResultWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_label = QLabel(alignment=Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        print_btn = QPushButton("Print")
        print_btn.clicked.connect(self.print_image)
        finish_btn = QPushButton("Finish")
        finish_btn.clicked.connect(lambda: self.window().set_view(0))

        layout = QGridLayout(self)
        layout.addWidget(self.image_label, 0, 0, 1, 2)
        layout.addWidget(save_btn, 1, 0)
        layout.addWidget(print_btn, 1, 1)
        layout.addWidget(finish_btn, 2, 0, 1, 2)

    def show_image(self):
        if img := self.window().generated_image:
            self.image_label.setPixmap(QPixmap.fromImage(img))

    def save(self):
        if img := self.window().generated_image:
            dialog = QFileDialog(self.window(), "Save Image", "output.jpg", "Images (*.png *.jpg)")
            dialog.setOption(QFileDialog.DontUseNativeDialog, True)
            if dialog.exec():
                path = dialog.selectedFiles()[0]
                if path:
                    img.save(path)

    def print_image(self):
        print("Printing image... (this is a placeholder, implement actual printing logic here)")
