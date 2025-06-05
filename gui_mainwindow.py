# gui_main.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Qt
from gui_classes.camera_widget import CameraWidget
from gui_classes.save_and_setting_widget import SaveAndSettingWidget
from gui_classes.loading_widget import LoadingWidget
from gui_classes.welcome_widget import WelcomeWidget
from constante import WINDOW_STYLE
import gc
import objgraph
import psutil
import os

class PhotoBoothApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhotoBooth")
        self.setStyleSheet(WINDOW_STYLE)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.captured_image = None
        self.generated_image = None

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Stack widget avec style
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(WINDOW_STYLE)
        layout.addWidget(self.stack)

        # Ajoute WelcomeWidget comme vue 0
        self.welcome_widget = WelcomeWidget(self)
        self.camera_widget = CameraWidget(self)
        self.save_setting_widget = SaveAndSettingWidget(self)
        self.load_widget = LoadingWidget(self)

        self.widgets = [
            self.welcome_widget,
            self.camera_widget,
            self.save_setting_widget,
            self.load_widget
        ]

        for w in self.widgets:
            self.stack.addWidget(w)
        # Appelle la vue d'accueil sans cleanup
        self.firstview(0)

    def firstview(self, index: int):
        """Affiche la vue d'accueil sans cleanup (pour éviter la destruction immédiate des boutons)."""
        print(f"[FIRSTVIEW] Affichage initial de la vue {index} sans cleanup")
        self.stack.setCurrentIndex(index)
        # Démarre la caméra si besoin
        if index == 1:
            self.camera_widget.start_camera()

    def _cleanup_widget(self, widget):
        # --- 3. Vérification des objets suspects avec objgraph ---
        print("[CLEANUP] Début nettoyage widget")
        import gc, objgraph
        gc.collect()
        
        # --- 4. Utilisation de gc.get_referrers pour voir qui référence l'objet ---
        print(f"[DEBUG] Références vers {widget.__class__.__name__}:")
        refs = gc.get_referrers(widget)
        for ref in refs:
            print(f"  - {type(ref)}")

        # --- 5. Vérification du parent ---
        print(f"[DEBUG] Parent du widget: {widget.parent()}")
        
        # Nettoyage threads et overlays
        if hasattr(widget, "_cleanup_thread"):
            widget._cleanup_thread()
            
        if hasattr(widget, "loading_overlay") and widget.loading_overlay:
            print(f"[DEBUG] Parent de loading_overlay: {widget.loading_overlay.parent()}")
            
            # Génère un graphique des références avant suppression
            objgraph.show_backrefs([widget.loading_overlay], 
                                 max_depth=3, 
                                 filename=f'loading_overlay_refs_before.png')
            print("[DEBUG] Graphique généré: loading_overlay_refs_before.png")
            
            # Nettoie l'overlay
            widget.loading_overlay.hide()
            widget.loading_overlay.setParent(None)
            widget.loading_overlay.deleteLater()
            widget.loading_overlay = None
            
            # Force le garbage collector
            gc.collect()
            
            # Vérifie s'il reste des overlays en mémoire
            overlays = objgraph.by_type('LoadingOverlay')
            if overlays:
                print(f"[WARNING] Il reste encore {len(overlays)} LoadingOverlay en mémoire")
                objgraph.show_backrefs([overlays[-1]], 
                                     max_depth=3, 
                                     filename='loading_overlay_refs_after.png')
                print("[DEBUG] Graphique généré: loading_overlay_refs_after.png")

        print("[CLEANUP] Fin nettoyage widget")

    def show_save_setting(self):
        self.set_view(2)
        self.save_setting_widget.show_image()

    def show_result(self):
        self.set_view(3)
        self.result_widget.show_image()

    def show_load_widget(self):
        self.set_view(4)

    def set_view(self, index: int):
        print(f"[MEM] Avant set_view({index})")
        import gc, objgraph
        gc.collect()
        objgraph.show_growth(limit=10)
        prev_index = self.stack.currentIndex()
        prev_widget = self.widgets[prev_index] if 0 <= prev_index < len(self.widgets) else None
        next_widget = self.widgets[index] if 0 <= index < len(self.widgets) else None

        # Appelle cleanup si dispo
        if prev_widget and hasattr(prev_widget, "cleanup"):
            prev_widget.cleanup()

        # Cas particulier : passage direct CameraWidget -> SaveAndSettingWidget (garde le thread)
        if not (prev_index == 1 and index == 2):
            if prev_widget:
                self._cleanup_widget(prev_widget)

        if prev_index == 1 and index != 1:
            self.camera_widget.stop_camera()

        self.stack.setCurrentIndex(index)
        print(f"[MEM] Après set_view({index})")
        gc.collect()
        objgraph.show_growth(limit=10)

        if index == 1:
            self.camera_widget.start_camera()

    def log_resource_usage(self):
        # Affiche les 20 types d'objets les plus courants
        print("=== Objgraph: objets vivants ===")
        objgraph.show_most_common_types(limit=20)
        # Affiche la mémoire et le CPU utilisés par le process
        process = psutil.Process(os.getpid())
        print(f"Memory: {process.memory_info().rss / 1024 ** 2:.2f} MB")
        print(f"CPU: {process.cpu_percent(interval=1)}%")

    def debug_memory(self):
        import gc, objgraph
        gc.collect()
        print("[DEBUG] Objgraph growth:")
        objgraph.show_growth(limit=20)
        print("[DEBUG] Objgraph most common types:")
        objgraph.show_most_common_types(limit=20)
        objs = objgraph.by_type('SaveAndSettingWidget')
        if objs:
            objgraph.show_backrefs([objs[-1]], max_depth=3, filename='saveandsettingwidget_refs.png')
            print("Graphique généré: saveandsettingwidget_refs.png")
        if hasattr(self, "timer") and self.timer:
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None

    def debug_all_refs(self):
        import gc, objgraph
        gc.collect()
        print("[DEBUG] SaveAndSettingWidget backrefs:")
        objgraph.show_backrefs([self.save_setting_widget], filename="save_and_setting_widget_backrefs.png")
        print("[DEBUG] LoadingWidget backrefs:")
        objgraph.show_backrefs([self.load_widget], filename="loading_widget_backrefs.png")
        print("[DEBUG] gc.get_referrers SaveAndSettingWidget:", gc.get_referrers(self.save_setting_widget))
        print("[DEBUG] gc.get_referrers LoadingWidget:", gc.get_referrers(self.load_widget))

    def debug_loadingwidget_refs(self):
        import gc, objgraph
        gc.collect()
        print("[DEBUG] LoadingWidget backrefs (PNG):")
        objgraph.show_backrefs([self.load_widget], max_depth=3, filename="loadingwidget_backrefs.png")
        print("[DEBUG] Fichier généré: loadingwidget_backrefs.png")
        print("[DEBUG] gc.get_referrers LoadingWidget:")
        refs = gc.get_referrers(self.load_widget)
        print(refs)
