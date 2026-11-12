# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""Qualification of the wheel of the plugin."""

from __future__ import annotations

import os
import subprocess
import sys
import zipfile
from email.parser import Parser
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.version import Version

from datalab_showcase import __version__

PROJECT_ROOT = Path(__file__).parents[2]
PACKAGE = "datalab_showcase"


@pytest.fixture(name="wheel_path", scope="module")
def fixture_wheel_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the wheel of the project"""
    wheel_dir = tmp_path_factory.mktemp("wheel")
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", os.fspath(wheel_dir)],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    (path,) = wheel_dir.glob("*-py3-none-any.whl")
    assert path.name == f"{PACKAGE}-{__version__}-py3-none-any.whl"
    return path


@pytest.fixture(name="wheel")
def fixture_wheel(wheel_path: Path) -> zipfile.ZipFile:
    """Open the wheel of the project"""
    with zipfile.ZipFile(wheel_path) as wheel:
        yield wheel


def test_wheel_contains_the_compiled_catalogs(wheel: zipfile.ZipFile) -> None:
    """The wheel contains the compiled translations (not tracked by git: compile
    them first with ``python scripts/translations.py compile``) and the icon"""
    names = set(wheel.namelist())
    assert f"{PACKAGE}/locale/fr/LC_MESSAGES/{PACKAGE}.mo" in names, (
        "Compiled catalog missing: run 'python scripts/translations.py compile' "
        "before building the wheel"
    )
    assert f"{PACKAGE}/icons/showcase.svg" in names
    assert f"{PACKAGE}/adapters/desktop.py" in names
    assert not any(name.startswith(("tests/", "scripts/")) for name in names)
    assert not any(name.endswith((".po", ".pot")) for name in names)


def test_wheel_runs_from_a_zip_archive(wheel_path: Path) -> None:
    """DataLab runs a plugin installed from a file from its wheel, a ZIP archive on
    ``sys.path``: the French catalog is read from the wheel"""
    code = (
        "import sys; sys.path.insert(0, sys.argv[1]); "
        "import datalab_showcase.i18n as i18n; "
        "print(i18n.__file__); print(i18n._('Showcase mode'))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code, os.fspath(wheel_path)],
        env=dict(os.environ, LANGUAGE="fr", PYTHONIOENCODING="utf-8"),
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    module_path, text = completed.stdout.strip().splitlines()
    assert Path(module_path).parent.parent == wheel_path
    assert text == "Mode vitrine"


def test_wheel_metadata(wheel: zipfile.ZipFile) -> None:
    """The wheel declares the plugin entry point, the ``datalab-showcase`` command
    and the DataLab versions it supports"""
    dist_info = f"{PACKAGE}-{__version__}.dist-info"
    entry_points = wheel.read(f"{dist_info}/entry_points.txt").decode()
    assert "[datalab.plugins]" in entry_points
    assert f"{PACKAGE} = {PACKAGE}.adapters.desktop:ShowcasePlugin" in entry_points
    assert "[gui_scripts]" in entry_points
    assert f"datalab-showcase = {PACKAGE}.app:run" in entry_points
    metadata = Parser().parsestr(wheel.read(f"{dist_info}/METADATA").decode())
    assert metadata["Requires-Python"] == ">=3.10"
    requirements = {
        Requirement(raw).name: Requirement(raw)
        for raw in metadata.get_all("Requires-Dist")
        if "extra ==" not in raw
    }
    assert list(requirements) == ["datalab-platform"]
    specifier = requirements["datalab-platform"].specifier
    assert Version("1.4.1") in specifier and Version("1.4.9") in specifier
    for version in ("1.4.0", "1.5.0", "2.0.0"):
        assert Version(version) not in specifier
