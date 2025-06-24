import os
import json
from typing import Callable, List

class LanguageManager:
    _instance = None
    _subscribers: List[Callable] = []
    _lang_code = 'uk'
    _lang_data = {}
    _lang_path = os.path.join(os.path.dirname(__file__), '../language_file/uk.json')

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._subscribers = []
        self._lang_code = 'uk'
        self._lang_path = os.path.join(os.path.dirname(__file__), '../language_file/uk.json')
        self._lang_data = {}
        self.load_language(self._lang_code)

    def load_language(self, lang_code):
        self._lang_code = lang_code
        self._lang_path = os.path.join(os.path.dirname(__file__), f'../language_file/{lang_code}.json')
        try:
            with open(self._lang_path, 'r', encoding='utf-8') as f:
                self._lang_data = json.load(f)
        except Exception as e:
            print(f"[LANG] Error loading language {lang_code}: {e}")
            self._lang_data = {}
        self.notify_subscribers()

    def get_texts(self, key):
        return self._lang_data.get(key, {})

    def subscribe(self, callback: Callable):
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable):
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def notify_subscribers(self):
        for callback in self._subscribers:
            try:
                callback()
            except Exception as e:
                print(f"[LANG] Error notifying subscriber: {e}")

# Helper for global access
language_manager = LanguageManager.get_instance()
