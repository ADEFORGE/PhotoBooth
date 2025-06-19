from PySide6.QtWidgets import QPushButton, QButtonGroup, QWidget, QApplication
from PySide6.QtGui import QIcon, QPixmap, QImage, QGuiApplication
from PySide6.QtCore import QSize, Qt, QEvent
import os
from PIL import Image, ImageQt
import io

from constante import BTN_STYLE_ONE, BTN_STYLE_TWO


def _compute_dynamic_size(original_size: QSize) -> QSize:
    screen = QGuiApplication.primaryScreen()
    h = screen.availableGeometry().height()
    w = screen.availableGeometry().width()
    # On prend le plus petit côté pour garantir un carré qui rentre partout
    target = int(min(h, w) * 0.07)
    return QSize(target, target)


class Btn(QPushButton):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self._connected_slots = []
        self.setObjectName(name)
        self._icon_path = None
        self._setup_timer_sleep_events()

    def _setup_timer_sleep_events(self):
        p = self.parent()
        while p:
            if hasattr(p, '_timer_sleep') and p._timer_sleep:
                self._timer_sleep = p._timer_sleep
                break
            p = p.parent() if hasattr(p, 'parent') else None
        else:
            self._timer_sleep = None

        if self._timer_sleep:
            self.installEventFilter(self)
            self.clicked.connect(self._on_btn_clicked_reset_stop_timer)

    def eventFilter(self, obj, ev):
        if obj is self and self._timer_sleep:
            if ev.type() == QEvent.Enter and hasattr(self._timer_sleep, 'set_and_start'):
                self._timer_sleep.set_and_start()
            elif ev.type() == QEvent.MouseButtonPress:
                if hasattr(self._timer_sleep, 'set_and_start'):
                    self._timer_sleep.set_and_start()
                if hasattr(self._timer_sleep, 'stop'):
                    self._timer_sleep.stop()
        return super().eventFilter(obj, ev)

    def _on_btn_clicked_reset_stop_timer(self):
        if self._timer_sleep:
            if hasattr(self._timer_sleep, 'set_and_start'):
                self._timer_sleep.set_and_start()
            if hasattr(self._timer_sleep, 'stop'):
                self._timer_sleep.stop()

    def initialize(self, style=None, icon_path=None, size=None, checkable=False):
        if style:
            self.setStyleSheet(style)

        dyn_size = _compute_dynamic_size(size) if size else None

        if dyn_size:
            # Force le carré
            side = max(dyn_size.width(), dyn_size.height())
            square = QSize(side, side)
            self.setMinimumSize(square)
            self.setMaximumSize(square)

        self.setCheckable(checkable)

        if icon_path and os.path.exists(icon_path):
            self._icon_path = icon_path
            self.setIcon(QIcon(self._icon_path))

    def resizeEvent(self, event):
        # Force le carré même si le layout tente de changer la taille
        side = min(self.width(), self.height())
        self.resize(side, side)
        if self._icon_path:
            pad = 0.75
            icon_side = int(side * pad)
            self.setIconSize(QSize(icon_side, icon_side))
        super().resizeEvent(event)

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
            self.connect_slot(getattr(obj, method_name), signal)

    def cleanup(self):
        for sig, sl in self._connected_slots:
            try: getattr(self, sig).disconnect(sl)
            except: pass
        self._connected_slots.clear()
        self.setParent(None)
        self.deleteLater()

    def set_disabled_bw(self):
        self.setEnabled(False)
        self.blockSignals(True)
        self.setCheckable(False)
        self.setChecked(False)
        self.setFocusPolicy(Qt.NoFocus)

        def to_bw(path):
            if os.path.exists(path):
                with Image.open(path) as img:
                    buf = io.BytesIO()
                    img.convert('L').save(buf, 'PNG')
                    return QPixmap.fromImage(QImage.fromData(buf.getvalue()))
            return None

        if isinstance(self, BtnStyleOne):
            p = f"gui_template/btn_icons/{self.name}.png"
            pix = to_bw(p)
            if pix: self.setIcon(QIcon(pix))

        elif isinstance(self, BtnStyleTwo):
            p = f"gui_template/btn_textures copy/{self.name}.png"
            pix = to_bw(p)
            if pix:
                tmp = f"/tmp/bw_{self.name}.png"
                pix.save(tmp)
                style = f"""
                    QPushButton {{
                        border:2px solid black; border-radius:5px;
                        background-image:url({tmp}); background-position:center;
                        background-repeat:no-repeat; color:black;
                    }}
                    QPushButton:disabled {{
                        border:2px solid black; border-radius:5px;
                        background-image:url({tmp}); background-position:center;
                        background-repeat:no-repeat; color:black;
                    }}
                """
                self.setStyleSheet(style)

    def set_enabled_color(self):
        self.setEnabled(True)
        p = f"gui_template/btn_icons/{self.name}.png"
        if os.path.exists(p):
            self.setIcon(QIcon(p))
        self.setStyleSheet(self.styleSheet().replace(";opacity:0.5;", ""))


class BtnStyleOne(Btn):
    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self._icon_path_passive = f"gui_template/btn_icons/{name}_passive.png"
        self._icon_path_pressed = f"gui_template/btn_icons/{name}_pressed.png"
        dyn = _compute_dynamic_size(QSize(80, 80))
        side = max(dyn.width(), dyn.height(), 120)
        square = QSize(side, side)
        self._btn_side = side
        self._icon_pad = 1.0
        self.setStyleSheet("QPushButton { background: transparent; border: none; }")
        # Par défaut, icône passive
        self._set_passive_icon()
        self.setMinimumSize(square)
        self.setMaximumSize(square)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setVisible(True)
        self.raise_()
        self.pressed.connect(self._set_pressed_icon)
        self.released.connect(self._set_passive_icon)
        self.toggled.connect(self._on_toggled)

    def _set_pressed_icon(self):
        if os.path.exists(self._icon_path_pressed):
            pix = QPixmap(self._icon_path_pressed)
            if not pix.isNull():
                size = int(self._btn_side * self._icon_pad)
                self.setIcon(QIcon(pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
                self.setIconSize(QSize(size, size))

    def _set_passive_icon(self):
        if os.path.exists(self._icon_path_passive):
            pix = QPixmap(self._icon_path_passive)
            if not pix.isNull():
                size = int(self._btn_side * self._icon_pad)
                self.setIcon(QIcon(pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
                self.setIconSize(QSize(size, size))

    def _on_toggled(self, checked):
        if checked:
            self._set_pressed_icon()
        else:
            self._set_passive_icon()

    def resizeEvent(self, event):
        side = min(self.width(), self.height())
        self._btn_side = side
        if self.isDown() or self.isChecked():
            self._set_pressed_icon()
        else:
            self._set_passive_icon()
        super().resizeEvent(event)


class BtnStyleTwo(Btn):
    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        texture_path = f"gui_template/btn_textures copy/{name}.png"
        style = BTN_STYLE_TWO.format(texture=texture_path)
        # Utilise la même logique de dimensionnement que BtnStyleOne
        dyn = _compute_dynamic_size(QSize(80, 80))
        side = max(dyn.width(), dyn.height(), 120)
        square = QSize(side, side)
        self.setText(name)
        self.initialize(style=style, icon_path=None, size=square, checkable=True)
        self.setMinimumSize(square)
        self.setMaximumSize(square)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setVisible(True)
        self.raise_()


# La classe Btns ne change pas ici. Utilise la version existante sans modification.
# Seul Btn et ses enfants ont besoin d'un ajustement pour iconSize.

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
