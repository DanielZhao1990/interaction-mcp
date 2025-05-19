import json
import os
from threading import Lock

# Default language
_DEFAULT_LANG = 'en_US'
_LOCALES_DIR = os.path.join(os.path.dirname(__file__), 'locales')

class _LanguageManager:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self._lang = _DEFAULT_LANG
        self._lang_data = {}
        self._default_data = {}
        self._load_language(_DEFAULT_LANG)

    def _load_language(self, lang):
        # Load specified language pack
        lang_path = os.path.join(_LOCALES_DIR, f'{lang}.json')
        default_path = os.path.join(_LOCALES_DIR, f'{_DEFAULT_LANG}.json')
        try:
            with open(lang_path, 'r', encoding='utf-8') as f:
                self._lang_data = json.load(f)
        except Exception:
            self._lang_data = {}
        try:
            with open(default_path, 'r', encoding='utf-8') as f:
                self._default_data = json.load(f)
        except Exception:
            self._default_data = {}

    def set_language(self, lang):
        self._lang = lang
        self._load_language(lang)

    def get_text(self, key):
        # Priority: current language, then default language, finally the key itself
        return self._lang_data.get(key) or self._default_data.get(key) or "NotDefined"

# Global methods
_lang_mgr = _LanguageManager()

def set_language(lang_code):
    """Set global language"""
    _lang_mgr.set_language(lang_code)

def get_text(key):
    """Get text in current language"""
    return _lang_mgr.get_text(key)
