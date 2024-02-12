import os
from functools import lru_cache
from importlib import import_module


@lru_cache
def get_settings():
    settings_module = os.getenv("SETTINGS_MODULE", "config.settings.local")
    module = import_module(settings_module)
    Settings = getattr(module, "Settings")
    return Settings()


settings = get_settings()
