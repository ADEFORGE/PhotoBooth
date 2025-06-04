# gui_classes/resultwidget.py
from PySide6.QtWidgets import QWidget, QLabel, QGridLayout, QSizePolicy, QApplication, QPushButton
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt
from gui_classes.gui_base_widget import PhotoBoothBaseWidget
import gc, objgraph

class LoadingWidget(PhotoBoothBaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.clear_buttons()
        self.show_gif("./gui_template/load.gif")

    def __del__(self):
        print(f"[DEL] LoadingWidget détruit: {id(self)}")
        if hasattr(self, 'button_group'):
            for btn in self.button_group.buttons():
                try:
                    btn.clicked.disconnect()
                except Exception:
                    pass
        if hasattr(self, "_worker") and self._worker:
            try:
                self._worker.finished.disconnect()
            except Exception:
                pass

    def debug_refs(self):
        # Pour LoadingOverlay
        if hasattr(self, "loading_overlay") and self.loading_overlay:
            print("[DEBUG] LoadingOverlay backrefs:")
            objgraph.show_backrefs([self.loading_overlay], filename="loading_overlay_backrefs.png")
            print("[DEBUG] gc.get_referrers:", gc.get_referrers(self.loading_overlay))
        # Pour SaveAndSettingWidget
        objgraph.show_backrefs([self], filename="save_and_setting_widget_backrefs.png")
        print("[DEBUG] gc.get_referrers:", gc.get_referrers(self))

        for item in self.scene.items():
            self.scene.removeItem(item)
            del item
