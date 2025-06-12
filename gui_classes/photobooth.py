# gui_classes/photobooth.py
from PySide6.QtCore import QTimer, QThread
from gui_classes.gui_base_widget import PhotoBoothBaseWidget
from constante import CAMERA_ID
from gui_classes.camera_viewer import CameraViewer
from PySide6.QtGui import QPixmap, QImage
from gui_classes.overlay_manager import CountdownOverlayManager, ImageGenerationTask


class PhotoBooth(CameraViewer):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.countdown_overlay_manager = CountdownOverlayManager(self)
        self._generation_thread = None
        self._generation_task = None
        self._generation_in_progress = False

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
        self._cleanup_generation()

    def cleanup(self):
        """Full cleanup when widget is being destroyed."""
        print("[PHOTOBOOTH] Full cleanup")
        self.on_leave()  # Make sure we've stopped the camera
        super().cleanup()  # Call parent cleanup for thorough resource cleanup

    def _cleanup_generation(self):
        if self._generation_task:
            print("[PHOTOBOOTH] Arrêt du task de génération")
            self._generation_task.stop()
        # Correction : attendre l'arrêt du thread AVANT de deleteLater le task
        if self._generation_thread and self._generation_thread.isRunning():
            print("[PHOTOBOOTH] Arrêt du thread de génération")
            self._generation_thread.quit()
            self._generation_thread.wait(5000)  # attendre jusqu'à 5s
        # Correction : deleteLater du task SEULEMENT si le thread n'est plus running
        if self._generation_task:
            if not self._generation_thread or not self._generation_thread.isRunning():
                print("[PHOTOBOOTH] Suppression du task de génération")
                self._generation_task.deleteLater()
            else:
                print("[PHOTOBOOTH] ATTENTION: tentative de suppression du task alors que le thread tourne encore")
        self._generation_thread = None
        self._generation_task = None
        self._generation_in_progress = False

    def _on_style_toggle(self, checked, style_name):
        if checked:
            self.selected_style = style_name
        else:
            self.selected_style = None
        # Remplace le thread/generation direct par le manager si generate_image=True
        super().on_toggle(checked, style_name, generate_image=False)

    def _on_take_selfie(self):
        if not self.selected_style:
            take_selfie_btn = None
            if self.btns:
                for btn in self.btns.style1_btns:
                    if btn.objectName() == "take_selfie":
                        take_selfie_btn = btn
                        break
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
        print("[DEBUG] Démarrage du compte à rebours")
        # Lance d'abord le compte à rebours
        self.countdown_overlay_manager.start(self._after_countdown_finish)

    def _after_countdown_finish(self):
        """Callback appelé quand le compte à rebours est terminé"""
        print("[DEBUG] Compte à rebours terminé, capture de l'image")
        if self._last_frame is None:
            print("[ERROR] Pas de frame disponible")
            return
            
        qimg = QImage(self._last_frame)
        if qimg.isNull():
            print("[ERROR] Échec de la capture")
            return
            
        self.original_photo = qimg
        self.background_manager.set_captured_image(qimg)
        
        # Lance la génération avec le style sélectionné
        if self.selected_style:
            print(f"[DEBUG] Lancement génération avec style {self.selected_style}")
            self._generation_in_progress = True
            self._start_image_generation(self.selected_style, qimg.copy())

    def _start_image_generation(self, style_name, input_image):
        self._cleanup_generation()
        from gui_classes.overlay_manager import ImageGenerationTask
        from PySide6.QtCore import QThread

        self.show_loading()
        self._generation_thread = QThread()
        self._generation_task = ImageGenerationTask(style=style_name, input_image=input_image)
        self._generation_task.moveToThread(self._generation_thread)
        self._generation_thread.started.connect(self._generation_task.run)
        self._generation_task.finished.connect(self._on_image_generated_callback)
        # Correction : deleteLater du task seulement quand le thread est fini
        def cleanup_task():
            print("[PHOTOBOOTH] deleteLater sur task (thread fini)")
            self._generation_task.deleteLater()
        self._generation_thread.finished.connect(cleanup_task)
        self._generation_thread.finished.connect(self._generation_thread.deleteLater)
        self._generation_thread.start()

    def _on_image_generated_callback(self, qimg):
        print("[DEBUG] Callback _on_image_generated_callback appelé")
        self._generation_in_progress = False
        self.stop_camera()
        self.hide_loading()
        if qimg and not qimg.isNull():
            print("[DEBUG] Image générée valide (callback)")
            self.generated_image = qimg
        else:
            print("[DEBUG] Pas d'image générée (callback)")
            self.generated_image = None
        self.update_frame()
        self.set_state_validation()
        # Correction : cleanup après le callback, pour éviter de tuer le thread trop tôt
        self._cleanup_generation()

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
        """Met à jour l'affichage avec la bonne source via le BackgroundManager."""
        print("[PHOTOBOOTH] Mise à jour de l'affichage (BackgroundManager)")
        # Priorité : image générée > photo originale > frame caméra
        if self.generated_image and not isinstance(self.generated_image, str):
            self.background_manager.set_generated_image(self.generated_image)
        elif self.original_photo:
            self.background_manager.set_captured_image(self.original_photo)
        elif self._last_frame:
            self.background_manager.set_camera_pixmap(QPixmap.fromImage(self._last_frame))
        else:
            self.background_manager.clear_all()
        self.update()
