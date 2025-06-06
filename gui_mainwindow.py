from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Qt, QEvent
from gui_classes.photobooth import PhotoBooth
from gui_classes.welcome_widget import WelcomeWidget
from constante import WINDOW_STYLE
import gc
import objgraph
import psutil
import os


class MainWindow(QWidget):
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

        # Stack widget
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(WINDOW_STYLE)
        layout.addWidget(self.stack)

        # Dictionnaire des widgets par index
        self.widgets = {}
        self.widgets[0] = WelcomeWidget(self)
        self.widgets[1] = PhotoBooth(self)

        for idx, w in self.widgets.items():
            self.stack.addWidget(w)
        # Affiche la vue initiale
        self.set_view(0, initial=True)

    def set_view(self, index: int, initial=False):
        """Gère la transition entre les vues Welcome et PhotoBooth."""
        print(f"[MAINWINDOW] Changement vers la vue {index}")

        if not initial:
            current_index = self.stack.currentIndex()
            if current_index == index:
                return
            current_widget = self.widgets.get(current_index)
            if current_widget:
                print(f"[MAINWINDOW] Nettoyage de la vue {current_index}")
                if hasattr(current_widget, "on_leave"):
                    current_widget.on_leave()
                if hasattr(current_widget, "cleanup"):
                    current_widget.cleanup()
                # Supprime l'ancien widget si on ne veut pas le réutiliser
                # sinon, commente ces lignes pour garder en cache
                if index not in self.widgets or not isinstance(self.widgets[index], type(current_widget)):
                    current_widget.setParent(None)
                    current_widget.deleteLater()
                    del self.widgets[current_index]

        try:
            # Créer ou récupérer le widget approprié
            if not initial:
                if index == 0:
                    if not isinstance(self.widgets.get(0), WelcomeWidget):
                        old = self.widgets.get(0)
                        if old:
                            old.setParent(None)
                            old.deleteLater()
                            del self.widgets[0]
                        self.widgets[0] = WelcomeWidget(self)
                elif index == 1:
                    if not isinstance(self.widgets.get(1), PhotoBooth):
                        old = self.widgets.get(1)
                        if old:
                            old.setParent(None)
                            old.deleteLater()
                            del self.widgets[1]
                        self.widgets[1] = PhotoBooth(self)
                else:
                    print(f"[ERROR] Index de vue invalide: {index}")
                    return
                new_widget = self.widgets[index]
                # Si pas déjà dans la stack, l'ajoute
                if self.stack.indexOf(new_widget) == -1:
                    self.stack.addWidget(new_widget)
            else:
                new_widget = self.widgets[index]

            # Activer la nouvelle vue
            self.stack.setCurrentWidget(new_widget)
            print(f"[MAINWINDOW] Configuration de la nouvelle vue {index}")
            if hasattr(new_widget, "on_enter"):
                new_widget.on_enter()
        except Exception as e:
            print(f"[ERROR] Erreur lors du changement de vue: {e}")
            import traceback; traceback.print_exc()

        print("[MAINWINDOW] Changement de vue terminé")

    def _cleanup_widget(self, widget):
        # Méthode d'analyse/debug, non appelée en production
        print("[CLEANUP] Début nettoyage widget")
        gc.collect()
        # Affiche qui référence le widget
        print(f"[DEBUG] Références vers {widget.__class__.__name__}:")
        refs = gc.get_referrers(widget)
        for ref in refs:
            print(f"  - {type(ref)}")
        print(f"[DEBUG] Parent du widget: {widget.parent()}")

        # Nettoyage threads et overlays si présent
        if hasattr(widget, "_cleanup_thread"):
            widget._cleanup_thread()
        if hasattr(widget, "loading_overlay") and widget.loading_overlay:
            print(f"[DEBUG] Parent de loading_overlay: {widget.loading_overlay.parent()}")
            objgraph.show_backrefs([widget.loading_overlay], max_depth=3,
                                     filename=f'loading_overlay_refs_before.png')
            print("[DEBUG] Graphique généré: loading_overlay_refs_before.png")
            widget.loading_overlay.hide()
            widget.loading_overlay.setParent(None)
            widget.loading_overlay.deleteLater()
            widget.loading_overlay = None
            gc.collect()
            overlays = objgraph.by_type('LoadingOverlay')
            if overlays:
                print(f"[WARNING] Il reste encore {len(overlays)} LoadingOverlay en mémoire")
                objgraph.show_backrefs([overlays[-1]], max_depth=3,
                                         filename='loading_overlay_refs_after.png')
                print("[DEBUG] Graphique généré: loading_overlay_refs_after.png")

        print("[CLEANUP] Fin nettoyage widget")

    def log_resource_usage(self):
        # Affiche les 20 types d'objets les plus courants
        print("=== Objgraph: objets vivants ===")
        objgraph.show_most_common_types(limit=20)
        # Affiche la mémoire et le CPU utilisés par le process
        process = psutil.Process(os.getpid())
        print(f"Memory: {process.memory_info().rss / 1024 ** 2:.2f} MB")
        print(f"CPU: {process.cpu_percent(interval=1)}%")

    def debug_memory(self):
        # Mode debug : growth + backrefs
        gc.collect()
        print("[DEBUG] Objgraph growth:")
        objgraph.show_growth(limit=20)
        print("[DEBUG] Objgraph most common types:")
        objgraph.show_most_common_types(limit=20)
        objs = objgraph.by_type('SaveAndSettingWidget')
        if objs:
            objgraph.show_backrefs([objs[-1]], max_depth=3,
                                     filename='saveandsettingwidget_refs.png')
            print("Graphique généré: saveandsettingwidget_refs.png")
        if hasattr(self, "timer") and self.timer:
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None

    def debug_all_refs(self):
        gc.collect()
        print("[DEBUG] SaveAndSettingWidget backrefs:")
        if hasattr(self, 'save_setting_widget'):
            objgraph.show_backrefs([self.save_setting_widget],
                                     filename="save_and_setting_widget_backrefs.png")
            print("Graphique généré: save_and_setting_widget_backrefs.png")
        print("[DEBUG] LoadingWidget backrefs:")
        if hasattr(self, 'load_widget'):
            objgraph.show_backrefs([self.load_widget],
                                     filename="loading_widget_backrefs.png")
            print("Graphique généré: loading_widget_backrefs.png")
        print("[DEBUG] gc.get_referrers SaveAndSettingWidget:", gc.get_referrers(getattr(self, 'save_setting_widget', None)))
        print("[DEBUG] gc.get_referrers LoadingWidget:", gc.get_referrers(getattr(self, 'load_widget', None)))
