"""Persistent local game settings backed by settings.json."""
import json
from pathlib import Path


DEFAULT_SETTINGS = {
    'sfx_volume': 0.65,
    'music_volume': 0.35,
    'mobile_controls': False,
}


class Settings:
    def __init__(self, path=None):
        self.path = Path(path) if path else Path(__file__).with_name('settings.json')
        self.values = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        """Load valid JSON settings and retain defaults for missing values."""
        try:
            with self.path.open('r', encoding='utf-8') as settings_file:
                loaded = json.load(settings_file)
            if isinstance(loaded, dict):
                self.values.update({key: value for key, value in loaded.items()
                                    if key in DEFAULT_SETTINGS})
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self.save()
        return self.values.copy()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('w', encoding='utf-8') as settings_file:
            json.dump(self.values, settings_file, indent=2)
            settings_file.write('\n')

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        if key not in DEFAULT_SETTINGS:
            raise KeyError(f'Unknown setting: {key}')
        self.values[key] = value
