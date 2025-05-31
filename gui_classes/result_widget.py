# gui_classes/resultwidget.py
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import Qt
from gui_classes.gui_base_widget import PhotoBoothBaseWidget

class ResultWidget(PhotoBoothBaseWidget):
    def __init__(self, parent=None):
        super().__init__()
        
        # Configuration des boutons avec le même format que les autres widgets
        self.button_config = {
            "Save": "save",
            "Print": "print_image",
            "Back to Camera": ("set_view_camera", False)
        }
        
        # Utilise la méthode héritée pour créer les boutons
        self.setup_buttons_from_config()

    def show_image(self):
        """Affiche l'image générée."""
        if img := self.window().generated_image:
            super().show_image(img)

    def save(self):
        """Sauvegarde l'image générée."""
        if img := self.window().generated_image:
            dialog = QFileDialog(
                self.window(), 
                "Save Image", 
                "output.jpg", 
                "Images (*.png *.jpg)"
            )
            dialog.setOption(QFileDialog.DontUseNativeDialog, True)
            if dialog.exec():
                path = dialog.selectedFiles()[0]
                if path:
                    img.save(path)

    def print_image(self):
        """Imprime l'image (à implémenter)."""
        print("Printing image... (placeholder)")

    def set_view_camera(self):
        """Retourne à la vue caméra."""
        self.window().set_view(0)
