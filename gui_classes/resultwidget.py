# gui_classes/resultwidget.py
from PySide6.QtWidgets import QPushButton, QFileDialog
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from main_GUI import MainGUI

class ResultWidget(MainGUI):
    def __init__(self, parent=None):
        super().__init__()
        self.clear_buttons()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        print_btn = QPushButton("Print")
        print_btn.clicked.connect(self.print_image)
        finish_btn = QPushButton("Finish")
        finish_btn.clicked.connect(lambda: self.window().set_view(0))

        self.grid.addWidget(save_btn, 1, 0)
        self.grid.addWidget(print_btn, 1, 1)
        self.grid.addWidget(finish_btn, 2, 0, 1, 2)

    def show_image(self):
        if img := self.window().generated_image:
            self.show_image(img)

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
