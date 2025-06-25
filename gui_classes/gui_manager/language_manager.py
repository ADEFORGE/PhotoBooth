import os
import json
from typing import Callable, List, Dict, Any

DEBUG_LanguageManager = True

class LanguageManager:
    _instance = None

    @classmethod
    def get_instance(cls) -> "LanguageManager":
        if DEBUG_LanguageManager:
            print(f"[DEBUG][LanguageManager] Entering get_instance: args=()")
        if cls._instance is None:
            cls._instance = cls()
        if DEBUG_LanguageManager:
            print(f"[DEBUG][LanguageManager] Exiting get_instance: return={cls._instance}")
        return cls._instance

    def __init__(self) -> None:
        if DEBUG_LanguageManager:
            print(f"[DEBUG][LanguageManager] Entering __init__: args=()")
        self._subscribers: List[Callable] = []
        self._lang_code: str = 'uk'
        self._project_root: str = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self._lang_path: str = os.path.join(self._project_root, 'language_file', 'uk.json')
        self._lang_data: Dict[str, Any] = {}
        self.load_language(self._lang_code)
        if DEBUG_LanguageManager:
            print(f"[DEBUG][LanguageManager] Exiting __init__: return=None")

    def load_language(self, lang_code: str) -> None:
        if DEBUG_LanguageManager:
            print(f"[DEBUG][LanguageManager] Entering load_language: args=({lang_code!r})")
        self._lang_code = lang_code
        self._lang_path = os.path.join(self._project_root, 'language_file', f'{lang_code}.json')
        try:
            with open(self._lang_path, 'r', encoding='utf-8') as f:
                self._lang_data = json.load(f)
        except Exception as e:
            print(f"[LANG] Error loading language {lang_code}: {e}")
            self._lang_data = {}
        self.notify_subscribers()
        if DEBUG_LanguageManager:
            print(f"[DEBUG][LanguageManager] Exiting load_language: return=None")

    def get_texts(self, key: str) -> Any:
        if DEBUG_LanguageManager:
            print(f"[DEBUG][LanguageManager] Entering get_texts: args=({key!r})")
        value = self._lang_data.get(key, {})
        if DEBUG_LanguageManager:
            print(f"[DEBUG][LanguageManager] Exiting get_texts: return={value!r}")
        return value

    def subscribe(self, callback: Callable) -> None:
        if DEBUG_LanguageManager:
            print(f"[DEBUG][LanguageManager] Entering subscribe: args=({callback!r})")
        if callback not in self._subscribers:
            self._subscribers.append(callback)
        if DEBUG_LanguageManager:
            print(f"[DEBUG][LanguageManager] Exiting subscribe: return=None")

    def unsubscribe(self, callback: Callable) -> None:
        if DEBUG_LanguageManager:
            print(f"[DEBUG][LanguageManager] Entering unsubscribe: args=({callback!r})")
        if callback in self._subscribers:
            self._subscribers.remove(callback)
        if DEBUG_LanguageManager:
            print(f"[DEBUG][LanguageManager] Exiting unsubscribe: return=None")

    def notify_subscribers(self) -> None:
        if DEBUG_LanguageManager:
            print(f"[DEBUG][LanguageManager] Entering notify_subscribers: args=()")
        for callback in self._subscribers[:]:
            try:
                callback()
            except Exception as e:
                print(f"[LANG] Error notifying subscriber: {e}")
        if DEBUG_LanguageManager:
            print(f"[DEBUG][LanguageManager] Exiting notify_subscribers: return=None")

language_manager = LanguageManager.get_instance()
