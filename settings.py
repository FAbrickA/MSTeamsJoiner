import json

from config import CONFIG_PATH

__all__ = [
    "settings",
]


def load_settings() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        settings_ = json.load(config_file)

    # check some fields
    assert settings_.get('email', '')
    assert settings_.get('password', '')

    return settings_


settings = load_settings()
