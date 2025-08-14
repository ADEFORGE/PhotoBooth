import logging
logger = logging.getLogger(__name__)
from PySide6.QtCore import Qt
from PySide6.QtGui import QResizeEvent, QShowEvent, QHideEvent
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from gui_classes.gui_window.base_window import BaseWindow
from gui_classes.gui_manager.language_manager import language_manager
from gui_classes.gui_object.constant import GRID_WIDTH, EASY_KID_ACCESS

from gui_classes.gui_object.constant import DEBUG, DEBUG_FULL
DEBUG_SleepScreenWindow: bool = DEBUG
DEBUG_SleepScreenWindow_FULL: bool = DEBUG_FULL

class SleepScreenWindow(BaseWindow):
    def __init__(self, parent: QWidget = None) -> None:
        """
        Initialize the SleepScreenWindow with an optional parent widget.
        """
        if DEBUG_SleepScreenWindow:
            logger.info(f"[DEBUG][SleepScreenWindow] Entering __init__: args={{'parent':{parent}}}")
        super().__init__(parent)
        self._default_texts = language_manager.get_texts('WelcomeWidget') or {}
        self.setWindowTitle("PhotoBooth - Veille")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.center_widget = QWidget(self.overlay_widget)
        self.center_widget.setAttribute(Qt.WA_TranslucentBackground)
    
        self.overlay_layout.addWidget(
            self.center_widget, 1, 0, 1, GRID_WIDTH, alignment=Qt.AlignCenter
        )

        self.center_layout = QVBoxLayout(self.center_widget)
        self.center_layout.setContentsMargins(40, 40, 40, 40)
        self.center_layout.setSpacing(30)
        self.center_layout.setAlignment(Qt.AlignCenter)
        self.title_label = QLabel(self.center_widget)
        self.title_label.setStyleSheet("color: white; font-size: 72px; font-weight: bold; font-family: Arial;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)
        self.message_label = QLabel(self.center_widget)
        self.message_label.setStyleSheet("color: white; font-size: 36px; font-family: Arial;")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)
        self.center_layout.addWidget(self.title_label)
        self.center_layout.addWidget(self.message_label)
        language_manager.subscribe(self.update_language)
        self.update_language()
        self.showFullScreen()
        if DEBUG_SleepScreenWindow:
            logger.info(f"[DEBUG][SleepScreenWindow] Exiting __init__: return=None")

    def update_language(self) -> None:
        """
        Update the displayed language texts for the title and message labels.
        """
        if DEBUG_SleepScreenWindow:
            logger.info(f"[DEBUG][SleepScreenWindow] Entering update_language: args={{}}")
        texts = language_manager.get_texts('WelcomeWidget') or {}
        self.title_label.setText(texts.get('title', self._default_texts.get('title', 'Bienvenue')))
        self.message_label.setText(texts.get('message', self._default_texts.get('message', '')))
        if DEBUG_SleepScreenWindow:
            logger.info(f"[DEBUG][SleepScreenWindow] Exiting update_language: return=None")

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Handle window resize events and update overlay geometry.
        """
        if DEBUG_SleepScreenWindow_FULL:
            logger.info(f"[DEBUG][SleepScreenWindow] Entering resizeEvent: args={{'event':{event}}}")
        super().resizeEvent(event)
        self.overlay_widget.setGeometry(self.rect())
        if DEBUG_SleepScreenWindow_FULL:
            logger.info(f"[DEBUG][SleepScreenWindow] Exiting resizeEvent: return=None")

    def showEvent(self, event: QShowEvent) -> None:
        """
        Handle the show event and display all buttons.
        """
        if DEBUG_SleepScreenWindow_FULL:
            logger.info(f"[DEBUG][SleepScreenWindow] Entering showEvent: args={{'event':{event}}}")
        super().showEvent(event)
        if DEBUG_SleepScreenWindow_FULL:
            logger.info(f"[DEBUG][SleepScreenWindow] Exiting showEvent: return=None")

    def hideEvent(self, event: QHideEvent) -> None:
        """
        Handle the hide event for the window.
        """
        if DEBUG_SleepScreenWindow_FULL:
            logger.info(f"[DEBUG][SleepScreenWindow] Entering hideEvent: args={{'event':{event}}}")
        super().hideEvent(event)
        if DEBUG_SleepScreenWindow_FULL:
            logger.info(f"[DEBUG][SleepScreenWindow] Exiting hideEvent: return=None")

    def cleanup(self) -> None:
        """
        Clean up resources and unsubscribe from language updates.
        """
        if DEBUG_SleepScreenWindow:
            logger.info(f"[DEBUG][SleepScreenWindow] Entering cleanup: args={{}}")

        language_manager.unsubscribe(self.update_language)
        super().cleanup()
        if DEBUG_SleepScreenWindow:
            logger.info(f"[DEBUG][SleepScreenWindow] Exiting cleanup: return=None")

    def on_camera_button_clicked(self) -> None:
        """
        Handle the camera button click event and switch to the main window.
        """
        if DEBUG_SleepScreenWindow:
            logger.info(f"[DEBUG][SleepScreenWindow] Entering on_camera_button_clicked: args={{}}")
        self.window().transition_window(1)
        if DEBUG_SleepScreenWindow:
            logger.info(f"[DEBUG][SleepScreenWindow] Exiting on_camera_button_clicked: return=None")

    def on_enter(self) -> None:
        """
        Called when entering the window, updates language and shows UI elements.
        """
        if DEBUG_SleepScreenWindow:
            logger.info(f"[DEBUG][SleepScreenWindow] Entering on_enter: args={{}}")
        language_manager.subscribe(self.update_language)
        self.update_language()

        self.title_label.show()
        self.message_label.show()

        if DEBUG_SleepScreenWindow:
            logger.info(f"[DEBUG][SleepScreenWindow] Exiting on_enter: return=None")

    def on_leave(self) -> None:
        """
        Called when leaving the window, hides UI elements and cleans up.
        """
        if DEBUG_SleepScreenWindow:
            logger.info(f"[DEBUG][SleepScreenWindow] Entering on_leave: args={{}}")
        self.title_label.hide()
        self.message_label.hide()

        language_manager.unsubscribe(self.update_language)
        super().on_leave()
        if DEBUG_SleepScreenWindow:
            logger.info(f"[DEBUG][SleepScreenWindow] Exiting on_leave: return=None")

    def mousePressEvent(self, event) -> None:
        """
        Handle mouse press events to trigger the camera button click.
        """
        if DEBUG_SleepScreenWindow:
            logger.info(f"[DEBUG][SleepScreenWindow] Entering mousePressEvent: args={{'event':{event}}}")
        self.on_camera_button_clicked()
        super().mousePressEvent(event)
        if DEBUG_SleepScreenWindow:
            logger.info(f"[DEBUG][SleepScreenWindow] Exiting mousePressEvent: return=None")
