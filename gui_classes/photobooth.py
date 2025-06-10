# gui_classes/photobooth.py
from PySide6.QtCore import QTimer, QThread
from gui_classes.gui_base_widget import PhotoBoothBaseWidget, GenerationWorker
from constante import CAMERA_ID
from gui_classes.camera_viewer import CameraViewer


class PhotoBooth(CameraViewer):
    def __init__(self, parent=None):
        super().__init__(parent)
        from gui_classes.overlay_manager import CountdownOverlayManager, GenerationOverlayManager
        self.countdown_overlay_manager = CountdownOverlayManager(self)
        self.generation_overlay_manager = GenerationOverlayManager(self)
        # Ne pas démarrer la caméra ici

    def on_enter(self):
        """Called when PhotoBooth view becomes active."""
        print("[PHOTOBOOTH] Entering view")
        # Clear any previous state
        self.generated_image = None
        self.original_photo = None
        self.selected_style = None
        self._generation_in_progress = False
        
        # Reset UI to default state
        self._capture_connected = True
        self.set_state_default()
        
        # Start camera if needed
        self.start_camera()
        
        # Update display with last frame if available
        if self._last_frame:
            self.show_image(self._last_frame)
            self.update()
            
    def on_leave(self):
        """Called when leaving PhotoBooth view."""
        print("[PHOTOBOOTH] Leaving view")
        # Stop camera first
        self._capture_connected = False
        self.stop_camera()
        
        # Clean up any ongoing operations
        if self._generation_in_progress:
            if self._thread and self._thread.isRunning():
                self._thread.quit()
                self._thread.wait()
        
        # Hide any overlays
        self.hide_loading()
        if hasattr(self, '_countdown_overlay') and self._countdown_overlay:
            self._countdown_overlay.clean_overlay()
            self._countdown_overlay = None
            
        self.countdown_overlay_manager.clear_all()

    def cleanup(self):
        """Full cleanup when widget is being destroyed."""
        print("[PHOTOBOOTH] Full cleanup")
        self.on_leave()  # Make sure we've stopped the camera
        super().cleanup()  # Call parent cleanup for thorough resource cleanup

    def _on_style_toggle(self, checked, style_name):
        if checked:
            self.selected_style = style_name
        else:
            self.selected_style = None
        # Remplace le thread/generation direct par le manager si generate_image=True
        super().on_toggle(checked, style_name, generate_image=False)

    def start_image_generation(self, style_name, input_image):
        """Démarre la génération d'image via le manager."""
        from gui_classes.gui_base_widget import GenerationWorker
        worker = GenerationWorker(style_name, input_image)
        self._generation_in_progress = True
        self.generation_overlay_manager.start_generation(worker, self.on_generation_finished)

    def _on_take_selfie(self):
        from constante import TOOLTIP_DURATION_MS, TOOLTIP_STYLE, COUNTDOWN_START
        from PySide6.QtCore import QThread, Signal, QObject
        take_selfie_btn = None
        if self.btns:
            for btn in self.btns.style1_btns:
                if btn.objectName() == "take_selfie":
                    take_selfie_btn = btn
                    break
        if not self.selected_style:
            if take_selfie_btn:
                from PySide6.QtWidgets import QToolTip, QApplication
                from PySide6.QtCore import QPoint
                app = QApplication.instance()
                if app is not None:
                    old_style = app.styleSheet() or ""
                    import re
                    new_style = re.sub(r"QToolTip\s*\{[^}]*\}", "", old_style)
                    app.setStyleSheet(new_style + "\n" + TOOLTIP_STYLE)
                global_pos = take_selfie_btn.mapToGlobal(take_selfie_btn.rect().center())
                QToolTip.showText(global_pos, "Select a style first", take_selfie_btn, take_selfie_btn.rect(), TOOLTIP_DURATION_MS)
            return
        self._start_countdown_thread_and_capture()

    def _start_countdown_thread_and_capture(self):
        """Démarre le compte à rebours et capture la photo à la fin."""
        print("[DEBUG] Démarrage du countdown")
        from constante import COUNTDOWN_START
        self.countdown_overlay_manager.start(self.capture_photo_callback, start_value=COUNTDOWN_START)

    def capture_photo_callback(self):
        """Callback appelé à la fin du countdown - appelle simplement capture_photo"""
        print("[DEBUG] Callback du countdown appelé")
        print(f"[DEBUG] Style sélectionné: {self.selected_style}")
        print(f"[DEBUG] Last frame disponible: {self._last_frame is not None}")
        self.capture_photo(self.selected_style)

    def showEvent(self, event):
        super().showEvent(event)

    def on_generation_finished(self, qimg):
        print("[DEBUG] Génération terminée")
        self._generation_in_progress = False
        self.stop_camera()
        if qimg and not qimg.isNull():
            print("[DEBUG] Image générée valide")
            self.generated_image = qimg
        else:
            print("[DEBUG] Pas d'image générée")
            self.generated_image = None
        self.update_frame()
        self.set_state_validation()

    def _on_accept_close(self):
        sender = self.sender()
        if sender and sender.objectName() == 'accept':
            self.set_state_wait()
            from constante import VALIDATION_OVERLAY_MESSAGE
            from gui_classes.overlay import OverlayRules, OverlayQrcode
            from gui_classes.toolbox import QRCodeUtils
            def on_rules_validated():
                def on_qrcode_close():
                    self.set_state_default()
                data = "https://youtu.be/xvFZjo5PgG0?si=pp6hBg7rL4zineRX"
                pil_img = QRCodeUtils.generate_qrcode(data)
                qimg = QRCodeUtils.pil_to_qimage(pil_img)
                overlay_qr = OverlayQrcode(
                    parent=self.window(),
                    title_text="Scannez le QR code pour continuer",
                    qimage=qimg,
                    subtitle_text="Merci d'avoir accepté les règles.",
                    on_close=on_qrcode_close
                )
                overlay_qr.show_overlay()
            def on_rules_refused():
                self.set_state_default()
            overlay = OverlayRules(
                parent=self.window(),
                VALIDATION_OVERLAY_MESSAGE=VALIDATION_OVERLAY_MESSAGE,
                on_validate=on_rules_validated,
                on_close=on_rules_refused
            )
            overlay.show_overlay()
        else:
            self.set_state_default()

    def reset_to_default_state(self):
        self.set_state_default()

    def set_state_default(self):
        """État d'accueil : webcam, bouton take_selfie, boutons de styles."""
        print("[PHOTOBOOTH] Retour à l'état par défaut")
        # Nettoyer l'état précédent
        self.selected_style = None
        self.generated_image = None
        self.original_photo = None
        self._last_frame = None
        
        # Nettoyer l'affichage
        self.clear_display()
        
        # Configurer les boutons
        from constante import dico_styles
        self.setup_buttons(
            style1_names=["take_selfie"],
            style2_names=list(dico_styles.keys()),
            slot_style1=self._on_take_selfie,
            slot_style2=lambda checked, btn=None: self._on_style_toggle(checked, btn.text() if btn else None)
        )
        
        # S'assurer que les boutons sont visibles et actifs
        if hasattr(self, 'overlay_widget'):
            self.overlay_widget.raise_()
        if hasattr(self, 'btns'):
            self.btns.raise_()
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.show()
                btn.setEnabled(True)
                
        # Réactiver la caméra
        self._capture_connected = True
        self.start_camera()

    def set_state_validation(self):
        """État validation : image/photo affichée, boutons accept/close (style1), plus de boutons de styles."""
        self._capture_connected = False
        self.stop_camera()
        self.setup_buttons_style_1(['accept', 'close'], slot_style1=self._on_accept_close)
        if hasattr(self, 'btns'):
            self.btns.raise_()
            for btn in self.btns.style1_btns:
                btn.show()
                btn.setEnabled(True)
        self.update_frame()

    def set_state_wait(self):
        """État attente : image/photo affichée, aucun bouton style1 ni style2."""
        self._capture_connected = False
        self.stop_camera()
        if hasattr(self, 'btns'):
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.hide()
        self.update_frame()

    def update_frame(self):
        """Met à jour l'affichage avec l'image générée ou la photo originale."""
        print("[PHOTOBOOTH] Mise à jour de l'affichage")
        if self.generated_image and not isinstance(self.generated_image, str):
            self.show_image(self.generated_image)
        elif self.original_photo:
            self.show_image(self.original_photo)
        self.update()
