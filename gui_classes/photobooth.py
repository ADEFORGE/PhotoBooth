# gui_classes/photobooth.py
from PySide6.QtCore import QTimer, QThread
from gui_classes.gui_base_widget import PhotoBoothBaseWidget, GenerationWorker
from constante import CAMERA_ID
from gui_classes.camera_viewer import CameraViewer


class PhotoBooth(CameraViewer):
    def __init__(self, parent=None):
        super().__init__(parent)
        from constante import dico_styles
        self.setup_buttons(
            style1_names=["take_selfie"],
            style2_names=list(dico_styles.keys()),
            slot_style1=self._on_take_selfie,
            slot_style2=lambda checked, btn=None: self._on_style_toggle(checked, btn.text() if btn else None)
        )
        self.overlay_widget.raise_()
        self.btns.raise_()
        self.selected_style = None

    def _on_style_toggle(self, checked, style_name):
        if checked:
            self.selected_style = style_name
        else:
            self.selected_style = None
        super().on_toggle(checked, style_name, generate_image=False)

    def _on_take_selfie(self):
        from constante import TOOLTIP_DURATION_MS, TOOLTIP_STYLE
        # Trouve le bouton take_selfie
        take_selfie_btn = None
        if self.btns:
            for btn in self.btns.style1_btns:
                if btn.objectName() == "take_selfie":
                    take_selfie_btn = btn
                    break
        if not self.selected_style:
            # Applique le style QToolTip à l'application sans écraser le style global
            if take_selfie_btn:
                from PySide6.QtWidgets import QToolTip, QApplication
                from PySide6.QtCore import QPoint
                app = QApplication.instance()
                if app is not None:
                    old_style = app.styleSheet() or ""
                    # Supprime tout ancien bloc QToolTip pour éviter les doublons
                    import re
                    new_style = re.sub(r"QToolTip\s*\{[^}]*\}", "", old_style)
                    app.setStyleSheet(new_style + "\n" + TOOLTIP_STYLE)
                global_pos = take_selfie_btn.mapToGlobal(take_selfie_btn.rect().center())
                QToolTip.showText(global_pos, "Select a style first", take_selfie_btn, take_selfie_btn.rect(), TOOLTIP_DURATION_MS)
            return
        self.capture_photo(self.selected_style)

    def showEvent(self, event):
        super().showEvent(event)
        if self.btns:
            self.btns.raise_()
        if self.generated_image is not None:
            self.update_frame()

    def on_generation_finished(self, qimg):
        self._generation_in_progress = False
        self.hide_loading()
        self.stop_camera()
        if qimg and not qimg.isNull():
            self.generated_image = qimg
        else:
            self.generated_image = self.original_photo
        self.update_frame()
        # Remplace le bouton 'take_selfie' par 'accept' et 'close' via la nouvelle méthode de placement
        self.setup_buttons_style_1(['accept', 'close'], slot_style1=self._on_accept_close)
        if self.btns:
            self.btns.raise_()

    def _on_accept_close(self):
        sender = self.sender()
        if sender and sender.objectName() == 'accept':
            if self.window() and hasattr(self.window(), 'set_view'):
                self.window().set_view(1)
        elif sender and sender.objectName() == 'close':
            if self.window() and hasattr(self.window(), 'set_view'):
                self.window().set_view(0)
