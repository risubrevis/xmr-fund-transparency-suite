import json
import os
from pathlib import Path

from app.logging import get_logger

logger = get_logger("app.settings")

DEFAULT_SETTINGS = {
    "datetime_format": "YYYY-MM-DD HH:mm:ss",
    "locale": "en",
}

SETTINGS_FILE_PATH = os.environ.get("SETTINGS_FILE_PATH", "settings.json")


def _resolve_settings_path() -> Path:
    return Path(SETTINGS_FILE_PATH)


def load_settings() -> dict:
    """Load settings from JSON file, returning defaults if file doesn't exist."""
    path = _resolve_settings_path()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {**DEFAULT_SETTINGS, **data}
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("settings_load_error", error=str(e), path=str(path))
    return DEFAULT_SETTINGS.copy()


def save_settings(settings_dict: dict) -> None:
    """Save settings to JSON file."""
    path = _resolve_settings_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings_dict, f, indent=2, ensure_ascii=False)
    logger.info("settings_saved", path=str(path))


def ensure_settings_file() -> None:
    """Create settings file with defaults if it doesn't exist."""
    path = _resolve_settings_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("settings_file_not_found_creating", path=str(path))
        save_settings(DEFAULT_SETTINGS.copy())


def get_datetime_format() -> str:
    """Get the current datetime format pattern."""
    return load_settings().get("datetime_format", DEFAULT_SETTINGS["datetime_format"])


def set_datetime_format(format_str: str) -> str:
    """Set the datetime format pattern and persist it."""
    settings = load_settings()
    settings["datetime_format"] = format_str
    save_settings(settings)
    return format_str


def get_locale() -> str:
    """Get the configured UI locale code."""
    return load_settings().get("locale", DEFAULT_SETTINGS["locale"])


def set_locale(locale_code: str) -> str:
    """Persist the UI locale code."""
    settings = load_settings()
    settings["locale"] = locale_code
    save_settings(settings)
    return locale_code


def ensure_locale_default() -> None:
    """Write the default locale into settings.json if the key is missing."""
    settings = load_settings()
    if "locale" not in settings:
        settings["locale"] = DEFAULT_SETTINGS["locale"]
        save_settings(settings)
        logger.info("locale_default_written", locale=DEFAULT_SETTINGS["locale"])
