from PySide6.QtWidgets import QPushButton, QButtonGroup, QWidget, QApplication
from PySide6.QtGui import QIcon, QPixmap, QImage, QGuiApplication
from PySide6.QtCore import QSize, Qt, QEvent
import os
from PIL import Image, ImageQt
import io

from constante import BTN_STYLE_ONE, BTN_STYLE_TWO


def _compute_dynamic_size(original_size: QSize) -> QSize:
    """
    Compute a new QSize where height is 10% of screen height
    and width is scaled to maintain the original aspect ratio.
    """
    screen = QGuiApplication.primaryScreen()
    screen_height = screen.availableGeometry().height()
    target_height = int(screen_height * 0.1)
    aspect_ratio = original_size.width() / original_size.height() if original_size.height() > 0 else 1
    target_width = int(target_height * aspect_ratio)
    return QSize(target_width, target_height)

class Btn(QPushButton):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self._connected_slots = []
        self.setObjectName(name)
        self._setup_timer_sleep_events()

    def _setup_timer_sleep_events(self):
        parent = self.parent()
        timer_sleep = None
        while parent is not None:
            if hasattr(parent, '_timer_sleep') and parent._timer_sleep:
                timer_sleep = parent._timer_sleep
                break
            parent = parent.parent() if hasattr(parent, 'parent') else None
        self._timer_sleep = timer_sleep
        if self._timer_sleep:
            self.installEventFilter(self)
            self.clicked.connect(self._on_btn_clicked_reset_stop_timer)

    def eventFilter(self, obj, event):
        if obj is self and self._timer_sleep:
            if event.type() == QEvent.Enter:
                if hasattr(self._timer_sleep, 'set_and_start'):
                    self._timer_sleep.set_and_start()
            elif event.type() == QEvent.MouseButtonPress:
                if hasattr(self._timer_sleep, 'set_and_start'):
                    self._timer_sleep.set_and_start()
                if hasattr(self._timer_sleep, 'stop'):
                    self._timer_sleep.stop()
        return super().eventFilter(obj, event)

    def _on_btn_clicked_reset_stop_timer(self):
        if self._timer_sleep:
            if hasattr(self._timer_sleep, 'set_and_start'):
                self._timer_sleep.set_and_start()
            if hasattr(self._timer_sleep, 'stop'):
                self._timer_sleep.stop()

    def initialize(self, style=None, icon_path=None, size=None, checkable=False):
        if style:
            self.setStyleSheet(style)
        # Determine dynamic size if original provided
        if size:
            dyn_size = _compute_dynamic_size(size)
        else:
            dyn_size = None
        # Set icon if exists
        if icon_path and os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setIcon(icon)
            if dyn_size:
                self.setIconSize(dyn_size)
        # Set both minimum and maximum to enforce fixed size
        if dyn_size:
            self.setMinimumSize(dyn_size)
            self.setMaximumSize(dyn_size)
        self.setCheckable(checkable)

    def place(self, layout, row, col, alignment=Qt.AlignCenter):
        layout.addWidget(self, row, col, alignment=alignment)
        self.setVisible(True)
        self.raise_()

    def connect_slot(self, slot, signal="clicked"):
        if hasattr(self, signal):
            getattr(self, signal).connect(slot)
            self._connected_slots.append((signal, slot))

    def connect_by_name(self, obj, method_name, signal="clicked"):
        if hasattr(obj, method_name):
            slot = getattr(obj, method_name)
            self.connect_slot(slot, signal)

    def cleanup(self):
        for signal, slot in self._connected_slots:
            try:
                getattr(self, signal).disconnect(slot)
            except Exception:
                pass
        self._connected_slots.clear()
        if self.parent():
            self.setParent(None)
        self.deleteLater()

    def set_disabled_bw(self):
        """
        Désactive complètement le bouton et force un affichage noir et blanc.
        - Garde les textures mais les convertit en noir et blanc avec PIL
        - Garde les bordures noires comme en état normal
        - Supprime toutes les interactions (hover, pressed, checked)
        """
        # Désactive les interactions
        self.setEnabled(False)
        self.blockSignals(True)
        self.setCheckable(False)
        self.setChecked(False)
        self.setFocusPolicy(Qt.NoFocus)

        def convert_to_bw(image_path):
            """Convertit une image en noir et blanc avec PIL"""
            if os.path.exists(image_path):
                with Image.open(image_path) as img:
                    # Utilise convert('L') pour une vraie conversion en niveaux de gris
                    bw_img = img.convert('L')
                    # Convertit l'image PIL en QPixmap
                    buffer = io.BytesIO()
                    bw_img.save(buffer, format='PNG')
                    buffer.seek(0)
                    return QPixmap.fromImage(QImage.fromData(buffer.getvalue()))
            return None

        # Convertit l'icône en noir et blanc si présente pour BtnStyleOne
        if isinstance(self, BtnStyleOne):
            icon_path = f"gui_template/btn_icons/{self.name}.png"
            bw_pixmap = convert_to_bw(icon_path)
            if bw_pixmap:
                self.setIcon(QIcon(bw_pixmap))

        # Convertit la texture en noir et blanc pour BtnStyleTwo
        elif isinstance(self, BtnStyleTwo):
            texture_path = f"gui_template/btn_textures copy/{self.name}.png"
            bw_pixmap = convert_to_bw(texture_path)
            if bw_pixmap:
                # Sauvegarde temporaire de l'image N&B
                temp_path = f"/tmp/bw_{self.name}.png"
                bw_pixmap.save(temp_path)
                
                # Style avec bordure noire et texture N&B pour tous les états
                style = """
                    QPushButton {
                        border: 2px solid black;
                        border-radius: 5px;
                        background-image: url(%s);
                        background-position: center;
                        background-repeat: no-repeat;
                        color: black;
                    }
                    QPushButton:disabled {
                        border: 2px solid black;
                        border-radius: 5px;
                        background-image: url(%s);
                        background-position: center;
                        background-repeat: no-repeat;
                        color: black;
                    }
                    QPushButton:hover:disabled,
                    QPushButton:pressed:disabled,
                    QPushButton:checked:disabled {
                        border: 2px solid black;
                        border-radius: 5px;
                        background-image: url(%s);
                        background-position: center;
                        background-repeat: no-repeat;
                        color: black;
                    }
                """ % (temp_path, temp_path, temp_path)
                self.setStyleSheet(style)

    def set_enabled_color(self):
        """Réactive le bouton et restaure l'icône couleur."""
        self.setEnabled(True)
        # Recharge l'icône couleur d'origine si possible
        icon_path = f"gui_template/btn_icons/{self.name}.png"
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        # Restaure l'opacité
        self.setStyleSheet(self.styleSheet().replace(";opacity:0.5;", ""))

class BtnStyleOne(Btn):
    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        icon_path = f"gui_template/btn_icons/{name}.png"
        original_size = QSize(80, 80)
        self.initialize(
            style=BTN_STYLE_ONE,
            icon_path=icon_path,
            size=original_size,
            checkable=False
        )
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setVisible(True)
        self.raise_()

class BtnStyleTwo(Btn):
    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        texture_path = f"gui_template/btn_textures copy/{name}.png"
        style = BTN_STYLE_TWO.format(texture=texture_path)
        self.setText(name)
        # Determine text-based hint then dyn size
        # Using temporary hint size to preserve proportions
        self.adjustSize()
        hint_size = self.sizeHint()
        original_size = QSize(max(hint_size.width() + 32, 120), hint_size.height())
        self.initialize(
            style=style,
            icon_path=None,
            size=original_size,
            checkable=True
        )
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setVisible(True)
        self.raise_()

class Btns:
    def __init__(self, parent: QWidget, style1_names, style2_names, slot_style1=None, slot_style2=None):
        self.parent = parent
        overlay = getattr(parent, "overlay_widget", parent)
        self.style1_btns = []
        self.style2_btns = []
        self.button_group = QButtonGroup(overlay)
        self.button_group.setExclusive(True)
        self.setup_buttons(style1_names, style2_names, slot_style1, slot_style2)

    def lower_(self):
        for btn in self.style1_btns + self.style2_btns:
            btn.setVisible(False)

    def setup_buttons(self, style1_names, style2_names, slot_style1=None, slot_style2=None, layout=None, start_row=3):
        self.lower_()
        self.clear_style1_btns()
        self.clear_style2_btns()
        for name in style1_names:
            self.add_style1_btn(name, slot_style1)
        for name in style2_names:
            self.add_style2_btn(name, slot_style2)
        if layout:
            self.place_all(layout, start_row)
        self.raise_()

    def setup_buttons_style_1(self, style1_names, slot_style1=None, layout=None, start_row=3):
        self.lower_()
        self.clear_style1_btns()
        for name in style1_names:
            self.add_style1_btn(name, slot_style1)
        if layout:
            self.place_style1(layout, start_row)
        self.raise_()

    def setup_buttons_style_2(self, style2_names, slot_style2=None, layout=None, start_row=4):
        self.lower_()
        self.clear_style2_btns()
        for name in style2_names:
            self.add_style2_btn(name, slot_style2)
        if layout:
            self.place_style2(layout, start_row)
        self.raise_()

    def add_style1_btn(self, name, slot_style1=None):
        overlay = getattr(self.parent, "overlay_widget", self.parent)
        btn = BtnStyleOne(name, parent=overlay)
        if slot_style1 and isinstance(slot_style1, str):
            btn.connect_by_name(self.parent, slot_style1)
        elif callable(slot_style1):
            btn.clicked.connect(slot_style1)
        self.style1_btns.append(btn)
        return btn

    def add_style2_btn(self, name, slot_style2=None):
        overlay = getattr(self.parent, "overlay_widget", self.parent)
        btn = BtnStyleTwo(name, parent=overlay)
        if slot_style2 and isinstance(slot_style2, str):
            btn.connect_by_name(self.parent, slot_style2)
        elif callable(slot_style2):
            btn.clicked.connect(lambda checked, b=btn: slot_style2(checked, b))
        self.button_group.addButton(btn)
        self.style2_btns.append(btn)
        return btn

    def remove_style1_btn(self, name):
        for btn in self.style1_btns:
            if btn.name == name:
                btn.cleanup()
                self.style1_btns.remove(btn)
                break

    def remove_style2_btn(self, name):
        for btn in self.style2_btns:
            if btn.name == name:
                btn.cleanup()
                self.button_group.removeButton(btn)
                self.style2_btns.remove(btn)
                break

    def clear_style1_btns(self):
        for btn in self.style1_btns:
            btn.cleanup()
        self.style1_btns.clear()

    def clear_style2_btns(self):
        for btn in self.style2_btns:
            btn.cleanup()
            self.button_group.removeButton(btn)
        self.style2_btns.clear()

    def place_style1(self, layout, start_row=3):
        col_max = layout.columnCount() if hasattr(layout, "columnCount") else 7
        n1 = len(self.style1_btns)
        if n1 > 0:
            if n1 % 2 == 0:
                left = (col_max - n1 - 1) // 2
                for i, btn in enumerate(self.style1_btns):
                    col = left + i if i < n1 // 2 else left + i + 1
                    btn.place(layout, start_row, col)
            else:
                col1 = (col_max - n1) // 2
                for i, btn in enumerate(self.style1_btns):
                    btn.place(layout, start_row, col1 + i)

    def place_style2(self, layout, start_row=4):
        col_max = layout.columnCount() if hasattr(layout, "columnCount") else 7
        n2 = len(self.style2_btns)
        if n2 > 0:
            if n2 % 2 == 0:
                left = (col_max - n2 - 1) // 2
                for i, btn in enumerate(self.style2_btns):
                    col = left + i if i < n2 // 2 else left + i + 1
                    btn.place(layout, start_row, col)
            else:
                col2 = (col_max - n2) // 2
                for i, btn in enumerate(self.style2_btns):
                    btn.place(layout, start_row, col2 + i)

    def place_all(self, layout, start_row=3):
        self.place_style1(layout, start_row)
        self.place_style2(layout, start_row + 1)

    def set_style1_btns(self, names, slot_style1=None, layout=None, start_row=3):
        self.clear_style1_btns()
        for name in names:
            self.add_style1_btn(name, slot_style1)
        if layout:
            self.place_style1(layout, start_row)

    def set_style2_btns(self, names, slot_style2=None, layout=None, start_row=4):
        self.clear_style2_btns()
        for name in names:
            self.add_style2_btn(name, slot_style2)
        if layout:
            self.place_style2(layout, start_row)

    def set_all_btns(self, style1_names, style2_names, slot_style1=None, slot_style2=None, layout=None, start_row=3):
        self.set_style1_btns(style1_names, slot_style1, layout, start_row)
        self.set_style2_btns(style2_names, slot_style2, layout, start_row + 1)

    def set_all_disabled_bw(self):
        """Désactive et met tous les boutons du groupe en noir et blanc."""
        for btn in self.style1_btns + self.style2_btns:
            btn.set_disabled_bw()

    def set_all_enabled_color(self):
        """Réactive et remet tous les boutons du groupe en couleur."""
        for btn in self.style1_btns + self.style2_btns:
            btn.set_enabled_color()

    def set_disabled_bw_style1(self):
        """Désactive et met en noir et blanc uniquement les boutons style 1."""
        for btn in self.style1_btns:
            btn.set_disabled_bw()

    def set_disabled_bw_style2(self):
        """Désactive et met en noir et blanc uniquement les boutons style 2."""
        for btn in self.style2_btns:
            btn.set_disabled_bw()

    def set_enabled_color_style1(self):
        """Réactive et remet en couleur uniquement les boutons style 1."""
        for btn in self.style1_btns:
            btn.set_enabled_color()

    def set_enabled_color_style2(self):
        """Réactive et remet en couleur uniquement les boutons style 2."""
        for btn in self.style2_btns:
            btn.set_enabled_color()

    def cleanup(self):
        for btn in self.style1_btns + self.style2_btns:
            btn.cleanup()
        self.style1_btns.clear()
        self.style2_btns.clear()
        self.button_group.setParent(None)
        self.button_group.deleteLater()

    def raise_(self):
        for btn in self.style1_btns + self.style2_btns:
            btn.raise_()
            btn.setVisible(True)
