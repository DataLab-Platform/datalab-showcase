# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""Settings of the showcase, in a JSON file (host independent)."""

from __future__ import annotations

import json
from pathlib import Path

from datalab_showcase.core.settings import (
    ShowcaseSettings,
    load_settings,
    save_settings,
)


def test_missing_file_gives_the_defaults(tmp_path: Path) -> None:
    """Without settings file, the default settings are used"""
    settings = load_settings(str(tmp_path / "showcase.json"))
    assert settings == ShowcaseSettings()
    assert settings.pace == "normal" and settings.fullscreen and not settings.loop
    assert settings.screen == -1 and settings.web_timeout == 15


def test_settings_are_saved_and_loaded(tmp_path: Path) -> None:
    """The settings are saved in a JSON file, then loaded"""
    path = tmp_path / "folder" / "showcase.json"
    settings = ShowcaseSettings(
        excluded_scenarios=["d2", "app:org.example"],
        loop=True,
        pace="fast",
        fullscreen=False,
        screen=1,
        web_enabled=True,
        web_url="http://localhost:5173/",
        web_ids="w1",
        web_timeout=5,
    )
    assert save_settings(settings, str(path))
    assert json.loads(path.read_text(encoding="utf-8"))["pace"] == "fast"
    assert load_settings(str(path)) == settings
    # No temporary file is left
    assert [item.name for item in path.parent.iterdir()] == ["showcase.json"]


def test_corrupted_file_gives_the_defaults(tmp_path: Path) -> None:
    """A corrupted or unexpected file gives the default settings"""
    path = tmp_path / "showcase.json"
    for content in ("{not json", "[1, 2]", '"text"', ""):
        path.write_text(content, encoding="utf-8")
        assert load_settings(str(path)) == ShowcaseSettings()
    path.write_bytes(b"\xff\xfe\x00")
    assert load_settings(str(path)) == ShowcaseSettings()


def test_invalid_values_give_their_defaults(tmp_path: Path) -> None:
    """Invalid values are replaced by their default value, the others are kept"""
    path = tmp_path / "showcase.json"
    data = {
        "excluded_scenarios": ["d1", 2],
        "loop": "yes",
        "pace": "very fast",
        "fullscreen": False,
        "screen": True,
        "web_url": None,
        "web_timeout": 3,
        "unknown": 1,
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    assert load_settings(str(path)) == ShowcaseSettings(fullscreen=False, web_timeout=3)


def test_save_failure_is_reported(tmp_path: Path) -> None:
    """A settings file which cannot be written is reported, not raised"""
    folder = tmp_path / "showcase.json"
    folder.mkdir()
    assert not save_settings(ShowcaseSettings(), str(folder))
