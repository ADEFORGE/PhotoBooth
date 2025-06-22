from PySide6.QtWidgets import (
    QWidget, QLabel, QGridLayout, QPushButton, QHBoxLayout, QButtonGroup, QVBoxLayout
)
from PySide6.QtGui import QPixmap, QMovie, QImage, QFont, QIcon, QPainter, QPen, QColor, QPainterPath
from PySide6.QtCore import Qt, QSize, QThread, Signal, QObject
import cv2
import os
from gui_classes.overlay import OverlayLoading, OverlayRules, OverlayInfo
from gui_classes.toolbox import ImageUtils, normalize_btn_name
from comfy_classes.comfy_class_API import ImageGeneratorAPIWrapper
from constante import (
    GRID_WIDTH, GRID_VERTICAL_SPACING, GRID_HORIZONTAL_SPACING,
    GRID_LAYOUT_MARGINS, GRID_LAYOUT_SPACING, GRID_ROW_STRETCHES,
    dico_styles, ICON_BUTTON_STYLE, GENERIC_BUTTON_STYLE, TITLE_LABEL_TEXT,
    TITLE_LABEL_FONT_SIZE, TITLE_LABEL_FONT_FAMILY, TITLE_LABEL_BOLD,
    TITLE_LABEL_ITALIC, TITLE_LABEL_COLOR, TITLE_LABEL_BORDER_COLOR,
    TITLE_LABEL_BORDER_WIDTH, LOGO_SIZE, INFO_BUTTON_SIZE
)
from gui_classes.btn import Btns
from gui_classes.background_manager import BackgroundManager

class PhotoBoothBaseWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")
        self._thread = None
        self._worker = None
        self._generation_in_progress = False
        self.loading_overlay = None
        self.selected_style = None
        self.generated_image = None
        self._background_pixmap = None
        self._background_movie = None
        self._background_qimage = None
        self.overlay_widget = QWidget(self)
        self.overlay_widget.setObjectName("overlay_widget")
        self.overlay_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        self.overlay_widget.setStyleSheet("background: transparent;")
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(*GRID_LAYOUT_MARGINS)
        self.overlay_layout.setSpacing(GRID_LAYOUT_SPACING)
        self.overlay_layout.setVerticalSpacing(GRID_VERTICAL_SPACING)
        self.overlay_layout.setHorizontalSpacing(GRID_HORIZONTAL_SPACING)
        self.overlay_widget.setVisible(True)
        self.overlay_widget.setGeometry(0, 0, 1920, 1080)  # Force une taille très grande
        self.overlay_widget.raise_()
        self.setupcontainer()
        self.button_config = {}
        self.first_buttons = []
        self.setup_row_stretches()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.overlay_widget)
        self.overlay_widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.btns = None
        self.background_manager = BackgroundManager(self)

        # Connecte les boutons langue/rules
        self._lang_btn.clicked.connect(self.show_lang_dialog)
        self._rules_btn.clicked.connect(self.show_rules_dialog)

        # Correction : s'assure que l'overlay_widget est toujours au-dessus de tout
        self.overlay_widget.raise_()
        self.raise_()

    def resizeEvent(self, event):
        self.update()
        # Force la taille de l'overlay_widget à chaque resize
        self.overlay_widget.setGeometry(0, 0, self.width(), self.height())
        self.overlay_widget.setVisible(True)
        # Correction : force overlay_widget au-dessus de tout à chaque resize
        self.overlay_widget.raise_()
        if self.btns:
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.raise_()
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        bg = self.background_manager.get_background()
        img = None
        if isinstance(bg, QImage):
            img = QPixmap.fromImage(bg)
        elif isinstance(bg, QPixmap):
            img = bg
        elif isinstance(bg, QMovie):
            img = bg.currentPixmap()
        if img and not img.isNull():
            widget_w = self.width()
            widget_h = self.height()
            img_w = img.width()
            img_h = img.height()
            scale = widget_h / img_h
            scaled_w = int(img_w * scale)
            scaled_h = widget_h
            scaled_img = img.scaled(scaled_w, scaled_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if scaled_w > widget_w:
                x_offset = (scaled_w - widget_w) // 2
                target_rect = self.rect()
                source_rect = scaled_img.rect().adjusted(x_offset, 0, -x_offset, 0)
                painter.drawPixmap(target_rect, scaled_img, source_rect)
            else:
                x = (widget_w - scaled_w) // 2
                painter.drawPixmap(x, 0, scaled_w, scaled_h, scaled_img)
        else:
            pass  # Ne rien dessiner pour laisser la transparence native

    # Wrappers simples pour le background_manager
    def show_image(self, qimage: QImage):
        self.background_manager.set_captured_image(qimage)
        self.update()

    def show_pixmap(self, pixmap: QPixmap):
        self.background_manager.set_camera_pixmap(pixmap)
        self.update()

    def show_generated_image(self, qimage: QImage):
        self.background_manager.set_generated_image(qimage)
        self.update()

    def clear_display(self):
        print("[DEBUG][BASEWIDGET] clear_display called")
        print(f"[DEBUG][BASEWIDGET] clear_display: parent={self.parent()}, isVisible={self.isVisible()}, geometry={self.geometry()}")
        if hasattr(self, 'background_manager'):
            print(f"[DEBUG][BASEWIDGET] clear_display: background_manager={self.background_manager}")
        self.background_manager.clear_all()
        self.update()
        print("[DEBUG][BASEWIDGET] clear_display finished")
        print(f"[DEBUG][BASEWIDGET] clear_display: parent={self.parent()}, isVisible={self.isVisible()}, geometry={self.geometry()}")

    def clear_buttons(self):
        print("[DEBUG][BASEWIDGET] clear_buttons called")
        """Clear all buttons with proper cleanup."""
        if hasattr(self, 'button_group'):
            for btn in self.button_group.buttons():
                btn.setParent(None)
                btn.deleteLater()
            self.button_group = None
            
        # Clean up style buttons
        if hasattr(self, 'btns') and self.btns:
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                if btn is not None:
                    btn.hide()
                    btn.setParent(None)
                    btn.deleteLater()
            
        # Remove items from layout
        for i in reversed(range(2, self.overlay_layout.rowCount())):
            for j in range(self.overlay_layout.columnCount()):
                item = self.overlay_layout.itemAtPosition(i, j)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.hide()
                        widget.setParent(None)
                        widget.deleteLater()
                    self.overlay_layout.removeItem(item)
        print("[DEBUG][BASEWIDGET] clear_buttons finished")

    def get_grid_width(self):
        return GRID_WIDTH

    def setup_logo(self):
        logo_layout = QVBoxLayout()
        logo1 = QLabel()
        logo2 = QLabel()
        for logo, path in [(logo1, "gui_template/logo1.png"), (logo2, "gui_template/logo2.png")]:
            pix = QPixmap(path)
            logo.setPixmap(pix.scaled(LOGO_SIZE, LOGO_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo.setAttribute(Qt.WA_TranslucentBackground)
            logo.setStyleSheet("background: rgba(0,0,0,0);")
            logo_layout.addWidget(logo)
        logo_widget = QWidget()
        logo_widget.setLayout(logo_layout)
        logo_widget.setAttribute(Qt.WA_TranslucentBackground)
        logo_widget.setStyleSheet("background: rgba(0,0,0,0);")
        return logo_widget

    def setup_interaction_btn(self):
        # Setup du bouton de langue (lang_btn) et du bouton rules
        lang_btn = QPushButton()
        lang_btn.setStyleSheet(ICON_BUTTON_STYLE)
        lang_icon = QPixmap("gui_template/language.png")
        lang_btn.setIcon(QIcon(lang_icon))
        lang_btn.setIconSize(QSize(INFO_BUTTON_SIZE, INFO_BUTTON_SIZE))
        lang_btn.setFixedSize(INFO_BUTTON_SIZE + 16, INFO_BUTTON_SIZE + 16)
        lang_btn.raise_()
        self._lang_btn = lang_btn  # Stockage référence

        rules_btn = QPushButton()
        rules_btn.setStyleSheet(ICON_BUTTON_STYLE)
        rules_btn.setFixedSize(INFO_BUTTON_SIZE + 16, INFO_BUTTON_SIZE + 16)
        rules_icon = QPixmap("gui_template/rule_ico.png")
        rules_btn.setIcon(QIcon(rules_icon))
        rules_btn.setIconSize(QSize(INFO_BUTTON_SIZE, INFO_BUTTON_SIZE))
        rules_btn.raise_()
        self._rules_btn = rules_btn  # Stockage référence

        btn_layout = QVBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)
        btn_layout.addWidget(lang_btn, alignment=Qt.AlignRight | Qt.AlignTop)
        btn_layout.addWidget(rules_btn, alignment=Qt.AlignRight | Qt.AlignTop)
        btn_layout.addStretch(1)

        btn_widget = QWidget()
        btn_widget.setLayout(btn_layout)
        btn_widget.setAttribute(Qt.WA_TranslucentBackground)
        btn_widget.setStyleSheet("background: rgba(0,0,0,0);")
        return btn_widget

    def setupcontainer(self):
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(10)
        top_bar.addWidget(self.setup_logo(), alignment=Qt.AlignLeft | Qt.AlignTop)
        top_bar.addStretch(1)
        top_bar.addWidget(self.setup_interaction_btn(), alignment=Qt.AlignRight | Qt.AlignTop)
        container = QWidget()
        container.setLayout(top_bar)
        container.setAttribute(Qt.WA_TranslucentBackground)
        container.setStyleSheet("background: rgba(0,0,0,0);")
        # Ajout du container (barre du haut)
        self.overlay_layout.addWidget(container, 0, 0, 1, GRID_WIDTH)

    def setup_row_stretches(self):
        for row, stretch in GRID_ROW_STRETCHES.items():
            # On saute la ligne 'title' (0) car il n'y a plus de titre
            if row == 'title':
                continue
            row_index = {"title": 0, "display": 1, "buttons": 2}[row]
            self.overlay_layout.setRowStretch(row_index, stretch)

    def _set_style_buttons_enabled(self, enabled: bool):
        if hasattr(self, 'button_group'):
            for btn in self.button_group.buttons():
                btn.setEnabled(enabled)

    def _cleanup_thread(self):
        if hasattr(self, "_thread") and self._thread is not None:
            try:
                if not self._thread.isRunning():
                    self._thread = None
                    self._worker = None
            except Exception as e:
                print(f"[CLEANUP] Exception in _cleanup_thread: {e}")

    def _ensure_overlay(self):
        if not hasattr(self, 'loading_overlay') or self.loading_overlay is None:
            self.loading_overlay = OverlayLoading(self)
            self.loading_overlay.resize(self.size())
        return self.loading_overlay

    def show_loading(self):
        overlay = self._ensure_overlay()
        overlay.resize(self.size())
        overlay.show()
        overlay.raise_()

    def hide_loading(self):
        if hasattr(self, 'loading_overlay') and self.loading_overlay:
            self.loading_overlay.hide()

    def on_toggle(self, checked: bool, style_name: str, generate_image: bool = False):
        if self._generation_in_progress:
            return
        if checked:
            self.selected_style = style_name
            # La génération d'image et la gestion de thread sont déléguées ailleurs

    def setup_buttons(self, style1_names, style2_names, slot_style1=None, slot_style2=None):
        """Set up buttons with improved cleanup."""
        print("[WIDGET] Setting up buttons")
        # Clean up existing buttons first
        self.clear_buttons()
        
        if hasattr(self, 'btns') and self.btns:
            self.btns.cleanup()
            self.btns = None
            
        # Create new buttons
        from gui_classes.btn import Btns
        self.btns = Btns(self, [], [], None, None)
        self.btns.setup_buttons(
            style1_names, 
            style2_names, 
            slot_style1, 
            slot_style2, 
            layout=self.overlay_layout, 
            start_row=3
        )
        
        # Ensure proper Z-order
        self.overlay_widget.raise_()
        if self.btns:
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.raise_()
                btn.show()
        self.raise_()

    def setup_buttons_style_1(self, style1_names, slot_style1=None):
        if self.btns:
            self.btns.setup_buttons_style_1(style1_names, slot_style1, layout=self.overlay_layout, start_row=3)
            self.overlay_widget.raise_()
            self.raise_()

    def setup_buttons_style_2(self, style2_names, slot_style2=None):
        if self.btns:
            self.btns.setup_buttons_style_2(style2_names, slot_style2, layout=self.overlay_layout, start_row=4)
            self.overlay_widget.raise_()
            self.raise_()

    def showEvent(self, event):
        super().showEvent(event)
        # Correction : force overlay_widget au-dessus de tout à chaque show
        self.overlay_widget.raise_()
        if self.btns:
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.raise_()
        # ...autres actions showEvent si besoin...

    def cleanup(self):
        print("[DEBUG][BASEWIDGET] cleanup called")
        """Perform thorough cleanup of resources"""
        # Clean up thread and worker
        if hasattr(self, '_thread') and self._thread:
            if self._thread.isRunning():
                self._thread.quit()
                self._thread.wait()
            self._thread.deleteLater()
            self._thread = None
            
        if hasattr(self, '_worker') and self._worker:
            self._worker.deleteLater()
            self._worker = None
            
        # Clean up loading overlay
        if hasattr(self, 'loading_overlay') and self.loading_overlay:
            self.loading_overlay.hide()
            self.loading_overlay.setParent(None)
            self.loading_overlay.deleteLater()
            self.loading_overlay = None
            
        # Clean up buttons
        if hasattr(self, "btns") and self.btns:
            self.btns.cleanup()
            self.btns = None
            
        # Clean up images
        self._background_pixmap = None
        self._background_qimage = None
        if self._background_movie:
            self._background_movie.stop()
            self._background_movie = None
            
        # Clear display
        self.clear_display()
        
        # Clear generation status
        self._generation_in_progress = False
        print("[DEBUG][BASEWIDGET] cleanup finished")

    def show_info_dialog(self):
        """Affiche la boîte d'information via OverlayInfo"""
        overlay = OverlayInfo(self)
        overlay.show_overlay()

    def show_rules_dialog(self):
        """Affiche la boîte de dialogue des règles via OverlayRules puis QR code uniquement si une image a été générée. Sinon, ferme simplement l'overlay."""
        from gui_classes.overlay import OverlayRules, OverlayQrcode
        from gui_classes.toolbox import QRCodeUtils
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        parent = app.activeWindow() if app else self

        def show_qrcode_overlay():
            # Vérifie si une image a été générée
            if getattr(self, 'generated_image', None) is not None:
                from gui_classes.overlay import UI_TEXTS
                data = "https://youtu.be/xvFZjo5PgG0?si=pp6hBg7rL4zineRX"  # TODO: Replace with real data if needed
                pil_img = QRCodeUtils.generate_qrcode(data)
                qimg = QRCodeUtils.pil_to_qimage(pil_img)
                overlay_qr = OverlayQrcode(
                    parent=parent,
                    qimage=qimg,
                    on_close=None
                )
                overlay_qr.show_overlay()
            # Sinon, ne rien faire (l'OverlayRules sera fermé par défaut)

        overlay = OverlayRules(
            parent=parent,
            on_validate=show_qrcode_overlay,
            on_close=None
        )
        overlay.show_overlay()

    def show_lang_dialog(self):
        """Affiche la boîte de sélection de langue via OverlayLang"""
        from gui_classes.overlay import OverlayLang
        overlay = OverlayLang(self)
        overlay.show_overlay()
