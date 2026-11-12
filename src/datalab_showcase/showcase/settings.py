# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Showcase settings file
======================

The :mod:`datalab_showcase.showcase.settings` module locates the settings of the
showcase (see :mod:`datalab_showcase.core.settings`) in the configuration folder
of DataLab.
"""

from __future__ import annotations

from datalab.config import get_config_path

from datalab_showcase.core import settings as core_settings
from datalab_showcase.core.settings import ShowcaseSettings


def get_settings_path() -> str:
    """Return the path of the settings file, in the configuration folder of DataLab

    Returns:
        Path of ``showcase.json``
    """
    return get_config_path(core_settings.SETTINGS_FILENAME)


def load_settings() -> ShowcaseSettings:
    """Load the settings of the showcase

    Returns:
        Settings (default settings if the file is missing or corrupted)
    """
    return core_settings.load_settings(get_settings_path())


def save_settings(settings: ShowcaseSettings) -> bool:
    """Save the settings of the showcase

    Args:
        settings: Settings

    Returns:
        True if the settings are saved
    """
    return core_settings.save_settings(settings, get_settings_path())


__all__ = ["ShowcaseSettings", "get_settings_path", "load_settings", "save_settings"]
