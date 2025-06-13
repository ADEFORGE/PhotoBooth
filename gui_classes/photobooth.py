# gui_classes/photobooth.py
from PySide6.QtCore import QTimer, QThread
from gui_classes.gui_base_widget import PhotoBoothBaseWidget
from constante import CAMERA_ID, DEBUG, TOOLTIP_STYLE, TOOLTIP_DURATION_MS
from gui_classes.camera_viewer import CameraViewer
from PySide6.QtGui import QPixmap, QImage
from gui_classes.overlay_manager import CountdownOverlayManager, ImageGenerationTask


class PhotoBooth(CameraViewer):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.countdown_overlay_manager = CountdownOverlayManager(self, 3)  # Correction ici
        self._generation_task = None
        self._generation_in_progress = False
        self._countdown_callback_active = False  # Anti-reentrance flag
        if DEBUG:
            print("[INIT] Generation task and flags initialized")

    def on_enter(self):
        """Called when PhotoBooth view becomes active."""
        # print("[PHOTOBOOTH] Entering view")  # Suppression de l'affichage du titre
        # Clear any previous state
        self.generated_image = None
        self.original_photo = None
        self.selected_style = None
        
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
        self.clean()

        # Hide any overlays
        self.hide_loading()
        # Robust overlay cleanup with protection and debug prints
        if hasattr(self, '_countdown_overlay') and self._countdown_overlay:
            try:
                if getattr(self._countdown_overlay, '_is_alive', True):
                    print(f"[DEBUG] Cleaning countdown overlay: {self._countdown_overlay}")
                    self._countdown_overlay.clean_overlay()
                else:
                    print(f"[PROTECT] Countdown overlay already destroyed: {self._countdown_overlay}")
            except Exception as e:
                print(f"[ERROR] Exception during countdown overlay cleanup: {e}")
            self._countdown_overlay = None
        self.countdown_overlay_manager.clear_all()

    def clean(self):
        """Wrapper: délègue le cleanup à ImageGenerationTask."""
        if DEBUG:
            print(f"[GEN] Cleaning up - in_progress: {self._generation_in_progress}, task: {self._generation_task}")
        self._generation_in_progress = False
        if self._generation_task:
            if hasattr(self._generation_task, 'finished'):
                try:
                    if DEBUG:
                        print("[GEN] Disconnecting previous task signals")
                    self._generation_task.finished.disconnect()
                except Exception as e:
                    if DEBUG:
                        print(f"[GEN] Warning: Could not disconnect signals: {e}")
            self._generation_task.clean()
            self._generation_task = None
        if DEBUG:
            print("[GEN] Cleanup complete")

    def cleanup(self):
        """Full cleanup when widget is being destroyed."""
        print("[PHOTOBOOTH] Full cleanup")
        self.clean()  # Clean generation task first
        self.on_leave()  # Make sure we've stopped the camera
        super().cleanup()  # Call parent cleanup

    def start(self, style_name, input_image):
        """Start image generation via ImageGenerationTask. Ne force plus le flag et ne gère plus l'overlay ici."""
        if DEBUG:
            print(f"[GEN] Starting generation with style: {style_name}")
            print(f"[GEN] Current state - in_progress: {self._generation_in_progress}, task: {self._generation_task}")
        # self.show_loading()  # SUPPRIMÉ : overlay de loading géré uniquement par overlay_manager.py
        from gui_classes.overlay_manager import ImageGenerationTask
        # Toujours nettoyer l'ancienne tâche, même si in_progress
        if self._generation_task:
            if DEBUG:
                print("[GEN] WARNING: Previous generation task exists, cleaning up first")
            self.clean()
        # On force la création d'une nouvelle tâche, même si l'état précédent n'est pas propre
        self._generation_task = ImageGenerationTask(style=style_name, input_image=input_image, parent=self)
        self._generation_task.finished.connect(self._on_image_generated_callback)
        if DEBUG:
            print("[GEN] New generation task created and connected")
        self._generation_task.start()

    def finish(self):
        """Wrapper: termine la génération via ImageGenerationTask."""
        if self._generation_task:
            self._generation_task.finish()

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
        from constante import DEBUG
        import threading
        print(f"[TRACE] _after_countdown_finish called. Thread: {threading.current_thread().name}, id(self): {id(self)}, flag: {self._countdown_callback_active}")
        print(f"[DEBUG_FLAGS] _after_countdown_finish: _countdown_callback_active={self._countdown_callback_active}, _generation_in_progress={self._generation_in_progress}, _generation_task={self._generation_task}, selected_style={self.selected_style}, _last_frame={'OK' if self._last_frame is not None else 'None'}")
        if self._countdown_callback_active:
            print(f"[TRACE] _after_countdown_finish: Already running, skipping. Thread: {threading.current_thread().name}, id(self): {id(self)}")
            if DEBUG:
                print("[GEN] _after_countdown_finish: Already running, skipping reentrant call.")
            return

        self._countdown_callback_active = True
        try:
            if DEBUG:
                print(f"[GEN] Countdown finished - in_progress: {self._generation_in_progress}")
                print(f"[GEN] Selected style: {self.selected_style}")
            print(f"[TRACE] _after_countdown_finish: Entered main logic. Thread: {threading.current_thread().name}, id(self): {id(self)}")
            print(f"[DEBUG_FLAGS] Entered main logic: _countdown_callback_active={self._countdown_callback_active}, _generation_in_progress={self._generation_in_progress}, _generation_task={self._generation_task}, selected_style={self.selected_style}, _last_frame={'OK' if self._last_frame is not None else 'None'}")

            self.clean()  # This will set _generation_in_progress to False

            if self._last_frame is None:
                print(f"[TRACE] _after_countdown_finish: No frame available. Thread: {threading.current_thread().name}, id(self): {id(self)}")
                if DEBUG:
                    print("[GEN] Error: No frame available")
                self._countdown_callback_active = False
                print(f"[DEBUG_FLAGS] Early return: _countdown_callback_active={self._countdown_callback_active}, _generation_in_progress={self._generation_in_progress}, _generation_task={self._generation_task}, selected_style={self.selected_style}")
                return

            qimg = QImage(self._last_frame)
            if qimg.isNull():
                print(f"[TRACE] _after_countdown_finish: QImage is null. Thread: {threading.current_thread().name}, id(self): {id(self)}")
                if DEBUG:
                    print("[GEN] Error: Failed to capture image")
                self._countdown_callback_active = False
                print(f"[DEBUG_FLAGS] Early return: _countdown_callback_active={self._countdown_callback_active}, _generation_in_progress={self._generation_in_progress}, _generation_task={self._generation_task}, selected_style={self.selected_style}")
                return

            self.original_photo = qimg
            self.background_manager.set_captured_image(qimg)

            # Ne pas nettoyer l'overlay countdown ici ! Le manager s'en occupe.
            print(f"[TRACE] _after_countdown_finish: Clearing countdown overlay via manager.")
            try:
                self.countdown_overlay_manager.clear_overlay("countdown")
            except Exception as e:
                print(f"[ERROR] Exception during countdown overlay manager cleanup: {e}")

            # CORRECTION: Only allow generation if not already in progress
            if self.selected_style and not self._generation_in_progress:
                print(f"[TRACE] _after_countdown_finish: Starting generation with style: {self.selected_style}")
                if DEBUG:
                    print(f"[GEN] Starting generation with style: {self.selected_style}")
                # self._generation_in_progress = True  # SUPPRIMÉ : le flag est géré dans le callback de génération
                print(f"[DEBUG_FLAGS] Before start: _countdown_callback_active={self._countdown_callback_active}, _generation_in_progress={self._generation_in_progress}, _generation_task={self._generation_task}, selected_style={self.selected_style}")
                self.start(self.selected_style, qimg.copy())
            else:
                print(f"[TRACE] _after_countdown_finish: Generation already in progress or no style selected. Skipping start.")
        except Exception as e:
            import traceback
            print(f"[TRACE] _after_countdown_finish: Exception: {e}")
            traceback.print_exc()
            if DEBUG:
                print(f"[GEN] Exception in _after_countdown_finish: {e}")
        finally:
            print(f"[TRACE] _after_countdown_finish: Resetting flag. Thread: {threading.current_thread().name}, id(self): {id(self)}")
            print(f"[DEBUG_FLAGS] Finally: _countdown_callback_active={self._countdown_callback_active}, _generation_in_progress={self._generation_in_progress}, _generation_task={self._generation_task}, selected_style={self.selected_style}")
            self._countdown_callback_active = False

    def _on_image_generated_callback(self, qimg):
        """Callback when image generation is complete."""
        from constante import DEBUG
        if DEBUG:
            print(f"[GEN] Generation callback - in_progress: {self._generation_in_progress}")
            print(f"[GEN] Generated image valid: {qimg and not qimg.isNull()}")
        
        # Reset generation state
        self._generation_task = None
        self._generation_in_progress = False  # Important: reset flag here
        
        self.stop_camera()
        if qimg and not qimg.isNull():
            if DEBUG:
                print("[GEN] Valid image generated, updating display")
            self.generated_image = qimg
        else:
            if DEBUG:
                print("[GEN] No valid image generated")
            self.generated_image = None
        self.update_frame()
        if DEBUG:
            print("[GEN] Moving to validation state")
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
                    qimage=qimg,  # Correction ici : qimage -> qimg
                    on_close=on_qrcode_close
                )
                overlay_qr.show_overlay()
            def on_rules_refused():
                self.set_state_default()
            overlay = OverlayRules(
                parent=self.window(),
                on_validate=on_rules_validated,
                on_close=on_rules_refused
            )
            overlay.show_overlay()
        else:
            self.set_state_default()

    def reset_generation_state(self):
        """Reset the generation state and related flags."""
        from constante import DEBUG
        if DEBUG:
            print("[PHOTOBOOTH] Resetting generation state and flags")
        self._generation_in_progress = False
        self._generation_task = None
        self.generated_image = None
        self.original_photo = None

    def reset_to_default_state(self):
        self.set_state_default()

    def set_state_default(self):
        """État d'accueil : webcam, bouton take_selfie, boutons de styles."""
        from constante import DEBUG
        if DEBUG:
            print("[PHOTOBOOTH] Back to default state")
        # Reset generation state and flags
        self.reset_generation_state()
        self.selected_style = None
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
            self.btns.set_disabled_bw_style2()  # Désactive et grise les boutons style2 (N&B, non cliquables)
            # Suppression de l'appel à disable_style2_btns, car set_disabled_bw_style2 suffit
        self.update_frame()

    def set_state_wait(self):
        """État attente : image/photo affichée, aucun bouton style1 ni style2."""
        self._capture_connected = False
        self.stop_camera()
        if hasattr(self, 'btns'):
            self.btns.set_disabled_bw_style2()
 
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
