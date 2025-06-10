from PySide6.QtWidgets import (
    QWidget, QLabel, QGridLayout, QPushButton, QHBoxLayout, QButtonGroup, QVBoxLayout
)
from PySide6.QtGui import QPixmap, QMovie, QImage, QFont, QIcon, QPainter, QPen, QColor, QPainterPath
from PySide6.QtCore import Qt, QSize, QThread, Signal, QObject
import cv2
import os
from gui_classes.overlay import OverlayLoading, OverlayRules, OverlayInfo
from gui_classes.toolbox import ImageUtils, normalize_btn_name
from comfy_classes.comfy_class_API_test_GUI import ImageGeneratorAPIWrapper
from constante import (
    GRID_WIDTH, GRID_VERTICAL_SPACING, GRID_HORIZONTAL_SPACING,
    GRID_LAYOUT_MARGINS, GRID_LAYOUT_SPACING, GRID_ROW_STRETCHES,
    dico_styles, ICON_BUTTON_STYLE, GENERIC_BUTTON_STYLE, TITLE_LABEL_TEXT,
    TITLE_LABEL_FONT_SIZE, TITLE_LABEL_FONT_FAMILY, TITLE_LABEL_BOLD,
    TITLE_LABEL_ITALIC, TITLE_LABEL_COLOR, TITLE_LABEL_BORDER_COLOR,
    TITLE_LABEL_BORDER_WIDTH, LOGO_SIZE, INFO_BUTTON_SIZE
)
from gui_classes.btn import Btns
from gui_classes.toolbox import GenerationWorker

class PhotoBoothBaseWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(*GRID_LAYOUT_MARGINS)
        self.overlay_layout.setSpacing(GRID_LAYOUT_SPACING)
        self.overlay_layout.setVerticalSpacing(GRID_VERTICAL_SPACING)
        self.overlay_layout.setHorizontalSpacing(GRID_HORIZONTAL_SPACING)
        self.overlay_widget.setVisible(True)
        self.overlay_widget.setGeometry(0, 0, 1920, 1080)  # Force une taille très grande
        self.overlay_widget.raise_()
        self.setup_logos()
        self.setup_title()
        self.button_config = {}
        self.first_buttons = []
        self.setup_row_stretches()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.overlay_widget)
        self.overlay_widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.btns = None

        # Connecte les boutons info/rules
        self._info_btn.clicked.connect(self.show_info_dialog)
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
        img = None
        if self._background_pixmap:
            img = self._background_pixmap
        elif self._background_qimage:
            img = QPixmap.fromImage(self._background_qimage)
        elif self._background_movie:
            img = self._background_movie.currentPixmap()
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
                painter.fillRect(self.rect(), Qt.black)
                x = (widget_w - scaled_w) // 2
                painter.drawPixmap(x, 0, scaled_w, scaled_h, scaled_img)
        else:
            painter.fillRect(self.rect(), Qt.black)

    def show_image(self, qimage: QImage):
        if qimage and not qimage.isNull():
            qimage = qimage.scaled(1200, 1200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._background_qimage = qimage
        self._background_pixmap = None
        self._background_movie = None
        self.update()

    def show_pixmap(self, pixmap: QPixmap):
        self._background_pixmap = pixmap
        self._background_qimage = None
        self._background_movie = None
        self.update()

    def show_gif(self, gif_path: str):
        self._background_movie = QMovie(gif_path)
        self._background_movie.frameChanged.connect(self.update)
        self._background_movie.start()
        self._background_pixmap = None
        self._background_qimage = None
        self.update()

    def clear_display(self):
        self._background_pixmap = None
        self._background_qimage = None
        self._background_movie = None
        self.update()

    def clear_buttons(self):
        """Clear all buttons with proper cleanup."""
        print("[WIDGET] Clearing buttons")
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

    def get_grid_width(self):
        return GRID_WIDTH

    def setup_logos(self):
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(10)
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
        top_bar.addWidget(logo_widget, alignment=Qt.AlignLeft | Qt.AlignTop)
        top_bar.addStretch(1)

        # Setup des boutons info et rules avec stockage des références
        info_btn = QPushButton()
        info_btn.setStyleSheet(ICON_BUTTON_STYLE)
        icon = QPixmap("gui_template/moreinfo.png")
        info_btn.setIcon(QIcon(icon))
        info_btn.setIconSize(QSize(INFO_BUTTON_SIZE, INFO_BUTTON_SIZE))
        info_btn.setFixedSize(INFO_BUTTON_SIZE + 16, INFO_BUTTON_SIZE + 16)
        info_btn.raise_()
        self._info_btn = info_btn  # Stockage référence

        rules_btn = QPushButton()
        rules_btn.setStyleSheet(ICON_BUTTON_STYLE)
        rules_btn.setFixedSize(INFO_BUTTON_SIZE + 16, INFO_BUTTON_SIZE + 16)
        rules_icon = QPixmap("gui_template/rule_ico.png")
        rules_btn.setIcon(QIcon(rules_icon))
        rules_btn.setIconSize(QSize(INFO_BUTTON_SIZE, INFO_BUTTON_SIZE))
        rules_btn.raise_()
        self._rules_btn = rules_btn  # Stockage référence

        # Ajout des boutons au layout
        btn_layout = QVBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)
        btn_layout.addWidget(info_btn, alignment=Qt.AlignRight | Qt.AlignTop)
        btn_layout.addWidget(rules_btn, alignment=Qt.AlignRight | Qt.AlignTop)
        btn_layout.addStretch(1)

        btn_widget = QWidget()
        btn_widget.setLayout(btn_layout)
        btn_widget.setAttribute(Qt.WA_TranslucentBackground)
        btn_widget.setStyleSheet("background: rgba(0,0,0,0);")
        top_bar.addWidget(btn_widget, alignment=Qt.AlignRight | Qt.AlignTop)

        container = QWidget()
        container.setLayout(top_bar)
        container.setAttribute(Qt.WA_TranslucentBackground)
        container.setStyleSheet("background: rgba(0,0,0,0);")
        self.overlay_layout.addWidget(container, 0, 0, 1, GRID_WIDTH)

    def setup_title(self):
        self.title_label = QLabel(TITLE_LABEL_TEXT)
        self.title_label.setStyleSheet("background: transparent;")
        font = QFont(TITLE_LABEL_FONT_FAMILY, TITLE_LABEL_FONT_SIZE)
        font.setBold(TITLE_LABEL_BOLD)
        font.setItalic(TITLE_LABEL_ITALIC)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.overlay_layout.addWidget(self.title_label, 0, 0, 1, GRID_WIDTH, alignment=Qt.AlignCenter)

    def setup_row_stretches(self):
        for row, stretch in GRID_ROW_STRETCHES.items():
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
            if generate_image:
                self._set_style_buttons_enabled(False)
                self._generation_in_progress = True
                self.generated_image = None
                self.show_loading()
                self._cleanup_thread()
                self._thread = QThread()
                input_img = getattr(self.window(), "captured_image", None)
                self._worker = GenerationWorker(style_name, input_img)
                self._worker.moveToThread(self._thread)
                self._thread.started.connect(self._worker.run)
                self._worker.finished.connect(self.on_generation_finished)
                self._worker.finished.connect(self._thread.quit)
                self._worker.finished.connect(self._worker.deleteLater)
                self._thread.finished.connect(self._thread.deleteLater)
                self._thread.finished.connect(self._on_thread_finished)
                self._thread.start()

    def on_generation_finished(self, qimg):
        self._generation_in_progress = False
        self._set_style_buttons_enabled(True)
        self.hide_loading()
        if qimg and not qimg.isNull():
            self.generated_image = qimg
            self.show_image(qimg)
        else:
            self.generated_image = None

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

    def show_info_dialog(self):
        """Affiche la boîte d'information via OverlayInfo"""
        overlay = OverlayInfo(self)
        overlay.show_overlay()

    def show_rules_dialog(self):
        """Affiche la boîte de dialogue des règles via OverlayRules puis QR code uniquement si une image a été générée. Sinon, ferme simplement l'overlay."""
        from constante import VALIDATION_OVERLAY_MESSAGE
        from gui_classes.overlay import OverlayRules, OverlayQrcode
        from gui_classes.toolbox import QRCodeUtils
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        parent = app.activeWindow() if app else self

        def show_qrcode_overlay():
            # Vérifie si une image a été générée
            if getattr(self, 'generated_image', None) is not None:
                data = "https://youtu.be/xvFZjo5PgG0?si=pp6hBg7rL4zineRX"  # TODO: Replace with real data if needed
                pil_img = QRCodeUtils.generate_qrcode(data)
                qimg = QRCodeUtils.pil_to_qimage(pil_img)
                overlay_qr = OverlayQrcode(
                    parent=parent,
                    title_text="Scannez le QR code pour continuer",
                    qimage=qimg,
                    subtitle_text="Merci d'avoir accepté les règles.",
                    on_close=None
                )
                overlay_qr.show_overlay()
            # Sinon, ne rien faire (l'OverlayRules sera fermé par défaut)

        overlay = OverlayRules(
            parent=parent,
            VALIDATION_OVERLAY_MESSAGE=VALIDATION_OVERLAY_MESSAGE,
            on_validate=show_qrcode_overlay,
            on_close=None
        )
        overlay.show_overlay()
