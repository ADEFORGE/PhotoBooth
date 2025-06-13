# gui_classes/overlay.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout, QHBoxLayout, QPushButton, QTextEdit, QSizePolicy, QGraphicsBlurEffect, QApplication
from PySide6.QtCore import Qt, QSize, QEvent, QThread, Signal, QObject, QTimer
from PySide6.QtGui import QMovie, QPixmap, QIcon, QImage, QPainter, QColor, QPen
from constante import DIALOG_BOX_STYLE, FIRST_BUTTON_STYLE
from gui_classes.btn import Btns
from gui_classes.toolbox import normalize_btn_name
import json
import os
UI_TEXTS_PATH = os.path.join(os.path.dirname(__file__), '..', 'ui_texts.json')
with open(UI_TEXTS_PATH, 'r', encoding='utf-8') as f:
    UI_TEXTS = json.load(f)

class Overlay(QWidget):
    def __init__(self, parent=None, center_on_screen=True):
        super().__init__(parent)
        self._is_visible = False
        self._is_alive = True
        print(f"[FLAG] Overlay created: _is_alive={self._is_alive}, _is_visible={self._is_visible}")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setVisible(False)
        from constante import GRID_WIDTH
        self.GRID_WIDTH = GRID_WIDTH
        self._center_on_screen = center_on_screen
        self._centered_once = False
        self._disabled_widgets = set()

    def setVisible(self, visible):
        if not self._is_alive:
            print(f"[PROTECT] setVisible({visible}) ignoré car _is_alive=False pour {self}")
            return
        super().setVisible(visible)
        self._is_visible = visible
        print(f"[FLAG] setVisible({visible}) called: _is_visible={self._is_visible}")

    def center_overlay(self):
        # Centre l'overlay sur l'écran principal en tenant compte de sa taille réelle
        screen = self.screen() if hasattr(self, 'screen') and self.screen() else None
        if screen is None:
            from PySide6.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            w, h = self.width(), self.height()
            x = geometry.x() + (geometry.width() - w) // 2
            y = geometry.y() + (geometry.height() - h) // 2
            self.move(x, y)

    def showEvent(self, event):
        super().showEvent(event)
        self._is_visible = True
        print(f"[FLAG] showEvent: _is_visible={self._is_visible}")
        # Centre l'overlay à l'affichage, pour tenir compte de la taille réelle
        if self._center_on_screen and not self._centered_once:
            self.center_overlay()
            self._centered_once = True
        self._disable_all_buttons_except_overlay()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._is_visible = False
        print(f"[FLAG] hideEvent: _is_visible={self._is_visible}")
        self._reenable_all_buttons()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 128))

    def setup_buttons(self, style1_names, style2_names, slot_style1=None, slot_style2=None, start_row=3):
        if hasattr(self, 'btns') and self.btns:
            self.btns.cleanup()
        self.btns = Btns(self, [], [], None, None)
        self.btns.setup_buttons(style1_names, style2_names, slot_style1, slot_style2, layout=self.overlay_layout, start_row=start_row)
        self.overlay_widget.raise_()
        self.raise_()

    def setup_buttons_style_1(self, style1_names, slot_style1=None, start_row=3):
        if hasattr(self, 'btns') and self.btns:
            self.btns.setup_buttons_style_1(style1_names, slot_style1, layout=self.overlay_layout, start_row=start_row)
            self.overlay_widget.raise_()
            self.raise_()

    def setup_buttons_style_2(self, style2_names, slot_style2=None, start_row=4):
        if hasattr(self, 'btns') and self.btns:
            self.btns.setup_buttons_style_2(style2_names, slot_style2, layout=self.overlay_layout, start_row=start_row)
            self.overlay_widget.raise_()
            self.raise_()

    def show_overlay(self):
        if not self._is_alive:
            print(f"[PROTECT] show_overlay ignoré car _is_alive=False pour {self}")
            return
        if self._is_visible:
            print(f"[PROTECT] show_overlay ignoré car déjà visible pour {self}")
            return
        self.setVisible(True)
        self.raise_()
        self._disable_all_buttons_except_overlay()

    def hide_overlay(self):
        if not self._is_alive:
            print(f"[PROTECT] hide_overlay ignoré car _is_alive=False pour {self}")
            return
        if not self._is_visible:
            print(f"[PROTECT] hide_overlay ignoré car déjà caché pour {self}")
            return
        self.setVisible(False)
        self._centered_once = False
        self._reenable_all_buttons()

    def clean_overlay(self):
        if not self._is_alive:
            print(f"[PROTECT] clean_overlay ignoré car déjà détruit pour {self}")
            return
        print(f"[DEBUG] Base Overlay.clean_overlay appelée pour {self}")
        try:
            self.hide_overlay()
            self._centered_once = False
            self._reenable_all_buttons()
            if hasattr(self, 'overlay_widget'):
                self.overlay_widget.hide()
                self.overlay_widget.setParent(None)
                self.overlay_widget.deleteLater()
            self._disabled_widgets.clear()
            self._is_alive = False
            print(f"[FLAG] clean_overlay: _is_alive={self._is_alive}")
            self.deleteLater()
            QApplication.processEvents()
        except Exception as e:
            print(f"[ERROR] Exception in base Overlay.clean_overlay: {e}")

    def __del__(self):
        self._is_alive = False
        print(f"[FLAG] __del__ called: _is_alive={self._is_alive}")

    def _disable_all_buttons_except_overlay(self):
        """Disable all buttons in the application except those in this overlay."""
        from PySide6.QtWidgets import QApplication, QPushButton
        app = QApplication.instance()
        if not app:
            return
            
        # Clear previously disabled widgets
        self._disabled_widgets.clear()
        
        try:
            # Disable all buttons except those in this overlay
            for widget in app.allWidgets():
                if isinstance(widget, QPushButton):
                    if not self.isAncestorOf(widget):
                        if widget.isEnabled():
                            widget.setEnabled(False)
                            self._disabled_widgets.add(widget)
            
            # Re-enable this overlay's buttons
            if hasattr(self, 'btns'):
                for btn in self.btns.style1_btns + self.btns.style2_btns:
                    btn.setEnabled(True)
                    btn.raise_()
        except Exception as e:
            print(f"[ERROR] Exception in _disable_all_buttons_except_overlay: {e}")

    def _reenable_all_buttons(self):
        from PySide6.QtWidgets import QApplication, QPushButton
        app = QApplication.instance()
        if app:
            for widget in app.allWidgets():
                if isinstance(widget, QPushButton):
                    widget.setEnabled(True)
        self._disabled_widgets.clear()

class OverlayGray(Overlay):
    def __init__(self, parent=None, center_on_screen=True):
        super().__init__(parent, center_on_screen)
        self.setStyleSheet("background-color: rgba(24,24,24,0.82); border-radius: 18px; border: 3px solid black;")

class OverlayWhite(Overlay):
    def __init__(self, parent=None, center_on_screen=True):
        super().__init__(parent, center_on_screen)
        self.setStyleSheet("background-color: rgba(255,255,255,0.85); border-radius: 18px; border: 3px solid white;")

class OverlayLoading(OverlayWhite):
    def __init__(self, parent=None):
        super().__init__(parent, center_on_screen=False)  # Désactive le centrage auto
        
        # Force l'overlay à occuper tout l'écran
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        
        self.setWindowState(Qt.WindowFullScreen)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(255,255,255,0.85);")
        
        # Widget principal qui occupe tout l'écran
        self.overlay_widget = QWidget(self)
        self.overlay_widget.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.overlay_widget.setGeometry(self.rect())
        
        # Layout pour centrer le GIF
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_layout.setSpacing(0)
        
        # GIF centré avec fond transparent
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet("background: transparent;")
        self._movie = QMovie("gui_template/load.gif")
        
        # Taille du GIF = 50% de l'écran
        screen_size = min(screen.geometry().width(), screen.geometry().height())
        self._gif_size = int(screen_size * 0.5)
        if self._gif_size < 64:
            self._gif_size = 128
            
        self._movie.setScaledSize(QSize(self._gif_size, self._gif_size))
        self.img_label.setMovie(self._movie)
        self.img_label.setFixedSize(self._gif_size, self._gif_size)
        
        # Centre le GIF
        self.overlay_layout.addWidget(self.img_label, 0, 0, alignment=Qt.AlignCenter)
        
        # Layout principal plein écran
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.overlay_widget)
        
        self.setFocusPolicy(Qt.NoFocus)

    def resizeEvent(self, event):
        screen = self.screen()
        if screen:
            self.setGeometry(screen.geometry())
            self.overlay_widget.setGeometry(self.rect())
        super().resizeEvent(event)

    def showEvent(self, event):
        print(f"[OverlayLoading] showEvent appelée pour {self}")
        super().showEvent(event)
        screen = self.screen()
        if screen:
            self.setGeometry(screen.geometry())
        if self._movie:
            self._movie.start()

    def hideEvent(self, event):
        print(f"[OverlayLoading] hideEvent appelée pour {self}")
        if hasattr(self, '_movie') and self._movie:
            self._movie.stop()
        if hasattr(self, 'img_label'):
            self.img_label.clear()
            self.img_label.hide()
        if hasattr(self, 'overlay_widget'):
            self.overlay_widget.hide()
        self.hide()
        QApplication.processEvents()
        super().hideEvent(event)

    def clean_overlay(self):
        print("[DEBUG] OverlayLoading.clean_overlay appelée")
        # Stop and clear the movie
        if hasattr(self, '_movie') and self._movie:
            self._movie.stop()
            self._movie.deleteLater()
            self._movie = None
        
        # Clear and hide the label
        if hasattr(self, 'img_label'):
            self.img_label.clear()
            self.img_label.hide()
            self.img_label.setParent(None)
            self.img_label.deleteLater()
        
        # Hide and cleanup the overlay widget
        if hasattr(self, 'overlay_widget'):
            self.overlay_widget.hide()
            self.overlay_widget.setParent(None)
            self.overlay_widget.deleteLater()
            
        self.hide()
        self.setParent(None)
        QApplication.processEvents()
        super().clean_overlay()

    def stop_animation(self):
        """Arrête toutes les animations et timers."""
        print(f"[OverlayLoading] stop_animation: arrêt des animations pour {self}")
        # Arrête le QMovie si utilisé
        if self._movie is not None:
            self._movie.stop()
            self._movie = None
        
    def hide_overlay(self):
        print("[DEBUG] OverlayLoading.hide_overlay appelée")
        if hasattr(self, '_movie') and self._movie:
            self._movie.stop()
        self.hide()
        self.overlay_widget.hide()
        QApplication.processEvents()
        super().hide_overlay()

    def __del__(self):
        print(f"[OverlayLoading] __del__ appelée pour {self}")

class OverlayRules(OverlayWhite):
    def __init__(self, parent=None, on_validate=None, on_close=None):
        super().__init__(parent)
        from constante import GRID_WIDTH
        self.setFixedSize(700, 540)
        self.overlay_widget = QWidget(self)
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(40, 32, 40, 32)
        self.overlay_layout.setSpacing(24)
        self.overlay_layout.setRowStretch(0, 0)
        self.overlay_layout.setRowStretch(1, 2)
        self.overlay_layout.setRowStretch(2, 1)
        self.overlay_layout.setRowStretch(3, 0)
        row = 0
        # Utilisation du JSON pour le titre et le message de validation
        rules_texts = UI_TEXTS["OverlayRules"]
        msg_label = QLabel(rules_texts["validation_message"], self.overlay_widget)
        msg_label.setStyleSheet("color: black; font-size: 22px; font-weight: bold; background: transparent;")
        msg_label.setAlignment(Qt.AlignCenter)
        self.overlay_layout.addWidget(msg_label, row, 0, 1, self.GRID_WIDTH, alignment=Qt.AlignCenter)
        row += 1
        self.text_edit = QTextEdit(self.overlay_widget)
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("background: transparent; color: black; font-size: 18px; border: none;")
        self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.text_edit.setMinimumHeight(80)
        self.text_edit.setMaximumHeight(180)
        self.text_edit.setMinimumWidth(int(self.width() * 0.85))
        # Charger le contenu depuis le fichier indiqué dans le JSON
        try:
            with open(rules_texts["content_file"], "r", encoding="utf-8") as f:
                rules_text = f.read()
                html = f'<div align="center">{rules_text.replace(chr(10), "<br>")}</div>'
                self.text_edit.setHtml(html)
        except Exception as e:
            self.text_edit.setText(f"Error loading rules: {str(e)}")
        self.overlay_layout.addWidget(self.text_edit, row, 0, 1, self.GRID_WIDTH)
        row += 1
        self.btns = Btns(self, [], [], None, None)
        self._on_validate = on_validate
        self._on_close = on_close
        self.setup_buttons_style_1([
            rules_texts["accept"],
            rules_texts["close"]
        ], slot_style1=self._on_accept_close, start_row=row)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.overlay_widget)
        self.setLayout(layout)

    def _on_accept_close(self):
        sender = self.sender()
        if sender and sender.objectName() == 'accept':
            if self._on_validate:
                self._on_validate()
            self.hide_overlay()
        elif sender and sender.objectName() == 'close':
            if self._on_close:
                self._on_close()
            self.hide_overlay()

class OverlayQrcode(OverlayWhite):
    def __init__(self, parent=None, qimage=None, on_close=None):
        super().__init__(parent)
        from constante import TITLE_LABEL_STYLE, GRID_WIDTH
        self.setFixedSize(700, 540)
        self.overlay_widget = QWidget(self)
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(40, 32, 40, 32)
        self.overlay_layout.setSpacing(24)
        self.overlay_layout.setRowStretch(0, 0)
        self.overlay_layout.setRowStretch(1, 2)
        self.overlay_layout.setRowStretch(2, 1)
        self.overlay_layout.setRowStretch(3, 0)
        row = 0
        # Utilisation du JSON pour le titre et le sous-titre
        qr_texts = UI_TEXTS["OverlayQrcode"]
        title_label = QLabel(qr_texts["title"], self.overlay_widget)
        title_label.setStyleSheet(TITLE_LABEL_STYLE + "color: black; border-bottom: none; text-decoration: none; background: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        self.overlay_layout.addWidget(title_label, row, 0, 1, self.GRID_WIDTH, alignment=Qt.AlignCenter)
        row += 1
        # QR code
        self.qr_label = QLabel(self.overlay_widget)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setMinimumSize(220, 220)
        self.qr_label.setMaximumSize(260, 260)
        self.qr_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if qimage and not qimage.isNull():
            pix = QPixmap.fromImage(qimage)
            scaled_pix = pix.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.qr_label.setPixmap(scaled_pix)
        else:
            self.qr_label.setText(qr_texts["error"])
            self.qr_label.setStyleSheet("background: #fcc; color: #a00; border: 1px solid #a00;")
        self.overlay_layout.addWidget(self.qr_label, row, 0, 1, self.GRID_WIDTH, alignment=Qt.AlignCenter)
        row += 1
        # Subtitle
        subtitle_label = QLabel(qr_texts["subtitle"], self.overlay_widget)
        subtitle_label.setStyleSheet("color: black; font-size: 18px; background: transparent;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        self.overlay_layout.addWidget(subtitle_label, row, 0, 1, self.GRID_WIDTH, alignment=Qt.AlignCenter)
        row += 1
        # Close button
        self.btns = Btns(self, [], [], None, None)
        self._on_close = on_close
        self.setup_buttons_style_1(['close'], slot_style1=self._on_close_btn, start_row=row)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.overlay_widget)
        self.setLayout(layout)

    def _on_close_btn(self):
        if self._on_close:
            self._on_close()
        self.hide_overlay()

class OverlayInfo(OverlayGray):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Information")
        self.setFixedSize(600, 400)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        from constante import GRID_WIDTH
        self.overlay_widget = QWidget(self)
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_layout.setSpacing(0)
        # Correction du centrage : calcul de la colonne centrale
        center_col = self.GRID_WIDTH // 2
        # Fond filtré
        bg = QLabel(self.overlay_widget)
        bg.setGeometry(0, 0, 600, 400)
        bg.setStyleSheet("background-color: rgba(24,24,24,0.82); border-radius: 18px;")
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(18)
        bg.setGraphicsEffect(blur)
        bg.lower()
        self.image_paths = [
            "gui_template/info1.png",
            "gui_template/info2.png",
            "gui_template/info3.png"
        ]
        self.current_index = 0
        self.image_label = QLabel(self.overlay_widget)
        self.image_label.setStyleSheet("background: transparent;")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.update_image()
        # Place l'image centrée sur la grille, sur toute la largeur
        self.overlay_layout.addWidget(self.image_label, 0, 0, 1, self.GRID_WIDTH, alignment=Qt.AlignCenter)
        # Place les boutons centrés sur la ligne suivante, sur toute la largeur
        self.btns = Btns(self, [], [], None, None)
        self.setup_buttons_style_1(['previous', 'close', 'next'], slot_style1=self._on_info_btn, start_row=1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.overlay_widget)
        self.setLayout(layout)

    def _on_info_btn(self):
        sender = self.sender()
        if sender and sender.objectName() == 'previous':
            if self.current_index > 0:
                self.current_index -= 1
                self.update_image()
                self.update_buttons_state()
        elif sender and sender.objectName() == 'next':
            if self.current_index < len(self.image_paths) - 1:
                self.current_index += 1
                self.update_image()
                self.update_buttons_state()
        elif sender and sender.objectName() == 'close':
            self.hide_overlay()
            self.deleteLater()

    def update_image(self):
        current_path = self.image_paths[self.current_index]
        pixmap = QPixmap(current_path)
        if not pixmap.isNull():
            self.image_label.setPixmap(pixmap.scaled(
                500, 300,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))

    def update_buttons_state(self):
        # Optionnel : désactive les boutons si besoin
        pass

class OverlayCountdown(Overlay):
    def __init__(self, parent=None, start=None):
        super().__init__(parent)
        from constante import COUNTDOWN_START, COUNTDOWN_FONT_STYLE
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        self.setWindowTitle("Countdown")
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Widget principal qui occupe tout l'écran
        self.overlay_widget = QWidget(self)
        self.overlay_widget.setStyleSheet("background-color: rgba(255,255,255,0);")
        self.overlay_layout = QVBoxLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_layout.setSpacing(0)
        # Label géant centré
        self.label = QLabel("", self.overlay_widget)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(COUNTDOWN_FONT_STYLE)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Ajoute un effet d'ombre blanche (contour)
        shadow = QGraphicsDropShadowEffect(self.label)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor("white"))
        shadow.setOffset(0, 0)
        self.label.setGraphicsEffect(shadow)
        self.overlay_layout.addWidget(self.label, alignment=Qt.AlignCenter)
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.overlay_widget)
        self.setLayout(layout)
        self._anim_timer = QTimer(self)
        self._anim_timer.setSingleShot(True)
        self._anim_timer.timeout.connect(self._hide_number)
        # Appel à showFullScreen APRÈS la création des widgets
        self.showFullScreen()
        # Force la géométrie à l'écran principal
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            self.setGeometry(geometry)
            self.overlay_widget.setGeometry(self.rect())

    def center_overlay(self):
        # Désactive le centrage hérité (sinon recadre sur une petite taille)
        pass

    def resizeEvent(self, event):
        # S'assure que l'overlay_widget occupe tout l'espace
        self.overlay_widget.setGeometry(self.rect())
        super().resizeEvent(event)

    def show_overlay(self):
        super().show_overlay()
        self.overlay_widget.setStyleSheet("background-color: rgba(255,255,255,0);")
        self.label.setVisible(False)

    def show_number(self, value):
        self.label.setText(str(value))
        opacity = 0.65 if value > 0 else 1.0
        self.overlay_widget.setStyleSheet(f"background-color: rgba(255,255,255,{int(opacity*255)});")
        self.label.setVisible(True)
        self._anim_timer.start(500)  # Show the number for 0.5s

    def _hide_number(self):
        if self.label.text() != "0":
            self.overlay_widget.setStyleSheet("background-color: rgba(255,255,255,0);")
        self.label.setVisible(False)

    def set_full_white(self):
        self.overlay_widget.setStyleSheet("background-color: rgba(255,255,255,1);")
        self.label.setVisible(False)

    def clean_overlay(self):
        self._anim_timer.stop()
        super().clean_overlay()

    def hide_overlay(self):
        self._anim_timer.stop()
        super().hide_overlay()
