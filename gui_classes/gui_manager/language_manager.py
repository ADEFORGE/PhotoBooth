import os
import json
from typing import Callable, List, Dict, Any

import logging
logger = logging.getLogger(__name__)

from gui_classes.gui_object.constant import DEBUG, DEBUG_FULL


DEBUG_LanguageManager = DEBUG
DEBUG_LanguageManager_FULL = DEBUG_FULL

class LanguageManager:
    _instance = None

    @classmethod
    def get_instance(cls) -> "LanguageManager":
        """
        Return the singleton instance of LanguageManager.
        """
        if DEBUG_LanguageManager:
            logger.info(f"[DEBUG][LanguageManager] Entering get_instance: args=()")
        if cls._instance is None:
            cls._instance = cls()
        if DEBUG_LanguageManager:
            logger.info(f"[DEBUG][LanguageManager] Exiting get_instance: return={cls._instance}")
        return cls._instance

    def __init__(self) -> None:
        """
        Initialize the LanguageManager and load the default language.
        """
        if DEBUG_LanguageManager:
            logger.info(f"[DEBUG][LanguageManager] Entering __init__: args=()")
        self._subscribers: List[Callable] = []
        self._lang_code: str = 'uk'
        self._project_root: str = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self._lang_path: str = os.path.join(self._project_root, 'language_file', 'uk.json')
        self._lang_data: Dict[str, Any] = {}
        self.load_language(self._lang_code)
        if DEBUG_LanguageManager:
            logger.info(f"[DEBUG][LanguageManager] Exiting __init__: return=None")

    def load_language(self, lang_code: str) -> None:
        """
        Load the language file for the specified language code.
        """
        if DEBUG_LanguageManager:
            logger.info(f"[DEBUG][LanguageManager] Entering load_language: args=({lang_code!r})")
        self._lang_code = lang_code
        self._lang_path = os.path.join(self._project_root, 'language_file', f'{lang_code}.json')
        try:
            with open(self._lang_path, 'r', encoding='utf-8') as f:
                self._lang_data = json.load(f)
        except Exception as e:
            logger.info(f"[LANG] Error loading language {lang_code}: {e}")
            self._lang_data = {}
        self.notify_subscribers()
        if DEBUG_LanguageManager:
            logger.info(f"[DEBUG][LanguageManager] Exiting load_language: return=None")

    def get_texts(self, key: str) -> Any:
        """
        Return the value associated with the given key from the loaded language data.
        """
        parts = key.split('.')
        node = self._lang_data
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                return {}
            node = node[part]
        return node

    def subscribe(self, callback: Callable) -> None:
        """
        Subscribe a callback to be notified when the language changes.
        """
        if DEBUG_LanguageManager:
            logger.info(f"[DEBUG][LanguageManager] Entering subscribe: args=({callback!r})")
        if callback not in self._subscribers:
            self._subscribers.append(callback)
        if DEBUG_LanguageManager:
            logger.info(f"[DEBUG][LanguageManager] Exiting subscribe: return=None")

    def unsubscribe(self, callback: Callable) -> None:
        """
        Unsubscribe a callback from language change notifications.
        """
        if DEBUG_LanguageManager:
            logger.info(f"[DEBUG][LanguageManager] Entering unsubscribe: args=({callback!r})")
        if callback in self._subscribers:
            self._subscribers.remove(callback)
        if DEBUG_LanguageManager:
            logger.info(f"[DEBUG][LanguageManager] Exiting unsubscribe: return=None")

    def notify_subscribers(self) -> None:
        """
        Notify all subscribed callbacks about a language change.
        """
        if DEBUG_LanguageManager:
            logger.info(f"[DEBUG][LanguageManager] Entering notify_subscribers: args=()")
        for callback in self._subscribers[:]:
            try:
                callback()
            except Exception as e:
                logger.info(f"[LANG] Error notifying subscriber: {e}")
        if DEBUG_LanguageManager:
            logger.info(f"[DEBUG][LanguageManager] Exiting notify_subscribers: return=None")

language_manager = LanguageManager.get_instance()
