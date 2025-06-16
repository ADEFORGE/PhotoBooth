from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QApplication
from PySide6.QtCore import Qt, QEvent
from gui_classes.photobooth import PhotoBooth
from gui_classes.welcome_widget import WelcomeWidget
from constante import WINDOW_STYLE, DEBUG
import gc
import objgraph
import psutil
import os
import sys


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
        print(f"[DEBUG][MAINWINDOW] set_view(index={index}, initial={initial}) called")
        if DEBUG:
            print(f"[MAINWINDOW] Switching to view {index}")
        if not initial:
            current_index = self.stack.currentIndex()
            print(f"[DEBUG][MAINWINDOW] stack.currentIndex()={self.stack.currentIndex()}, widget at index={type(self.stack.currentWidget())}")
            # Diagnostic : affiche tous les widgets et leurs index
            for i in range(self.stack.count()):
                print(f"[DEBUG][MAINWINDOW] stack index {i}: {type(self.stack.widget(i))}")
            current_widget = self.widgets.get(current_index)
            print(f"[DEBUG][MAINWINDOW] current_widget={type(current_widget)}")
            if current_widget:
                if DEBUG:
                    print(f"[MAINWINDOW] Cleaning up view {current_index}")
                if hasattr(current_widget, "on_leave"):
                    print(f"[DEBUG][MAINWINDOW] Calling on_leave on {type(current_widget)}")
                    current_widget.on_leave()
                if hasattr(current_widget, "cleanup"):
                    print(f"[DEBUG][MAINWINDOW] Calling cleanup on {type(current_widget)}")
                    current_widget.cleanup()
                if index not in self.widgets or not isinstance(self.widgets[index], type(current_widget)):
                    print(f"[DEBUG][MAINWINDOW] Deleting current_widget instance {type(current_widget)}")
                    current_widget.setParent(None)
                    current_widget.deleteLater()
                    del self.widgets[current_index]
        try:
            if not initial:
                if index == 0:
                    if not isinstance(self.widgets.get(0), WelcomeWidget):
                        old = self.widgets.get(0)
                        if old:
                            print(f"[DEBUG][MAINWINDOW] Replacing WelcomeWidget instance {type(old)}")
                            old.setParent(None)
                            old.deleteLater()
                            del self.widgets[0]
                        self.widgets[0] = WelcomeWidget(self)
                elif index == 1:
                    if not isinstance(self.widgets.get(1), PhotoBooth):
                        old = self.widgets.get(1)
                        if old:
                            print(f"[DEBUG][MAINWINDOW] Replacing PhotoBooth instance {type(old)}")
                            old.setParent(None)
                            old.deleteLater()
                            del self.widgets[1]
                        self.widgets[1] = PhotoBooth(self)
                else:
                    if DEBUG:
                        print(f"[ERROR] Invalid view index: {index}")
                    return
                new_widget = self.widgets[index]
                if self.stack.indexOf(new_widget) == -1:
                    print(f"[DEBUG][MAINWINDOW] Adding new_widget {type(new_widget)} to stack")
                    self.stack.addWidget(new_widget)
            else:
                new_widget = self.widgets[index]
            print(f"[DEBUG][MAINWINDOW] stack.currentIndex() before set: {self.stack.currentIndex()}")
            print(f"[DEBUG][MAINWINDOW] indexOf(new_widget): {self.stack.indexOf(new_widget)}")
            self.stack.setCurrentWidget(new_widget)
            print(f"[DEBUG][MAINWINDOW] stack.currentIndex() after set: {self.stack.currentIndex()}")
            print(f"[DEBUG][MAINWINDOW] currentWidget after set: {type(self.stack.currentWidget())}")
            if DEBUG:
                print(f"[MAINWINDOW] Configuring new view {index}")
            if hasattr(new_widget, "on_enter"):
                print(f"[DEBUG][MAINWINDOW] Calling on_enter on {type(new_widget)}")
                new_widget.on_enter()
        except Exception as e:
            if DEBUG:
                print(f"[ERROR] Error while switching view: {e}")
            import traceback; traceback.print_exc()
        if DEBUG:
            print("[MAINWINDOW] View switch complete")
        print(f"[DEBUG][MAINWINDOW] set_view finished for index={index}")

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


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.showFullScreen()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
