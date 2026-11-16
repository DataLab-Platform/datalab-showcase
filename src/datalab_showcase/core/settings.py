# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Showcase settings
=================

The choices of the **Showcase mode** dialog are remembered in a small JSON file
(``showcase.json``, in the configuration folder of DataLab), not in the
configuration of DataLab: the plugin may be removed without leaving any option
in it.

A missing, unreadable or corrupted file gives the default settings, and an
invalid value gives the default value of its setting: the showcase always
starts.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import os
import os.path as osp
import tempfile
from dataclasses import dataclass, field

logger = logging.getLogger("datalab_showcase")

#: Name of the settings file, in the configuration folder of DataLab
SETTINGS_FILENAME = "showcase.json"

#: Paces proposed in the Showcase mode dialog
PACES = ("slow", "normal", "fast")


@dataclass
class ShowcaseSettings:
    """Settings of the showcase mode

    Args:
        excluded_scenarios: IDs of the demos deselected in the Showcase mode dialog
        loop: True to play the demos in a loop
        pace: Pace of the demos: ``'slow'``, ``'normal'`` or ``'fast'``
        fullscreen: True to show DataLab in full screen
        screen: Index of the screen showing the showcase (-1: current screen)
        web_enabled: True to end each loop with a DataLab Web interlude
        web_url: URL of the DataLab Web showcase (empty: public host page)
        web_ids: Comma-separated IDs of the DataLab Web demos played by the
         interlude (empty: all the demos)
        web_timeout: Maximum duration (minutes) of the DataLab Web interlude: the
         browser window is closed afterwards
    """

    excluded_scenarios: list[str] = field(default_factory=list)
    loop: bool = False
    pace: str = "normal"
    fullscreen: bool = True
    screen: int = -1
    web_enabled: bool = False
    web_url: str = ""
    web_ids: str = ""
    web_timeout: int = 15

    @classmethod
    def from_dict(cls, data: object) -> ShowcaseSettings:
        """Return settings from a dictionary, ignoring unknown or invalid values

        Args:
            data: Dictionary (e.g. read from the JSON file)

        Returns:
            Settings (default values for the missing or invalid ones)
        """
        settings = cls()
        if not isinstance(data, dict):
            return settings
        for item in dataclasses.fields(cls):
            if item.name not in data:
                continue
            value = data[item.name]
            default = getattr(settings, item.name)
            if _is_valid(item.name, value, default):
                setattr(
                    settings,
                    item.name,
                    list(value) if isinstance(value, list) else value,
                )
            else:
                logger.warning(
                    "Invalid showcase setting ignored: %s=%r", item.name, value
                )
        return settings

    def to_dict(self) -> dict[str, object]:
        """Return the settings as a dictionary (JSON serializable)"""
        return dataclasses.asdict(self)


def _is_valid(name: str, value: object, default: object) -> bool:
    """Return True if a value is valid for a setting

    Args:
        name: Setting name
        value: Value
        default: Default value of the setting (gives its type)

    Returns:
        True if the value is valid
    """
    if isinstance(default, bool):
        return isinstance(value, bool)
    if isinstance(default, int):
        return isinstance(value, int) and not isinstance(value, bool)
    if isinstance(default, list):
        return isinstance(value, list) and all(isinstance(v, str) for v in value)
    if name == "pace":
        return value in PACES
    return isinstance(value, type(default))


def load_settings(path: str) -> ShowcaseSettings:
    """Load the settings from a JSON file

    Args:
        path: Path of the settings file

    Returns:
        Settings (default settings if the file is missing, unreadable or corrupted)
    """
    if not osp.isfile(path):
        return ShowcaseSettings()
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, ValueError) as exc:
        logger.warning(
            "Showcase settings %s cannot be read (%s): defaults used", path, exc
        )
        return ShowcaseSettings()
    return ShowcaseSettings.from_dict(data)


def save_settings(settings: ShowcaseSettings, path: str) -> bool:
    """Save the settings in a JSON file (replaced atomically)

    Args:
        settings: Settings
        path: Path of the settings file

    Returns:
        True if the settings are saved (a failure is logged, not raised)
    """
    folder = osp.dirname(osp.abspath(path))
    try:
        os.makedirs(folder, exist_ok=True)
        handle, temp_path = tempfile.mkstemp(
            prefix=".showcase-", suffix=".json", dir=folder
        )
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as file:
                json.dump(settings.to_dict(), file, indent=2)
            os.replace(temp_path, path)
        except BaseException:
            if osp.exists(temp_path):
                os.remove(temp_path)
            raise
    except OSError as exc:
        logger.warning("Showcase settings %s cannot be saved (%s)", path, exc)
        return False
    return True


__all__ = [
    "PACES",
    "SETTINGS_FILENAME",
    "ShowcaseSettings",
    "load_settings",
    "save_settings",
]
