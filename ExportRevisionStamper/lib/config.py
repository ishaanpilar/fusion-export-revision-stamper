"""Persisted add-in settings (filename template, last output folder, log filename)."""
import json
import os

_SETTINGS_FILENAME = "settings.json"

DEFAULTS = {
    "template": "{name}_Rev{revletter}_{date}.{ext}",
    "last_folder": "",
    "log_filename": "handoff_log.csv",
}


def _settings_path() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), _SETTINGS_FILENAME)


def load() -> dict:
    path = _settings_path()
    if not os.path.isfile(path):
        return dict(DEFAULTS)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)
    merged = dict(DEFAULTS)
    merged.update(data)
    return merged


def save(settings: dict) -> None:
    path = _settings_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
