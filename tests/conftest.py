# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Test configuration
==================

The tests run DataLab like its own test suite does (see ``datalab/tests/conftest.py``
in DataLab): unattended mode, default configuration without persistence, and the
``offscreen`` Qt platform (unless ``--show-windows`` is given).

The settings of the showcase are stored in a temporary folder: the tests never
change the settings of the user.
"""

from __future__ import annotations

import gc
import os

import pytest

# English user interface, as in the test suite of DataLab: set before the
# translations of DataLab and of the plugin are loaded
os.environ.setdefault("LANG", "en_US.UTF-8")

# pylint: disable=wrong-import-position
from datalab.config import Conf, ensure_initialized, reset_to_defaults  # noqa: E402
from datalab.env import execenv  # noqa: E402
from datalab.plugins import PluginRegistry  # noqa: E402
from guidata.config import ValidationMode, set_validation_mode  # noqa: E402
from qtpy import QtCore as QC  # noqa: E402

from datalab_showcase.showcase import settings as settings_module  # noqa: E402
from datalab_showcase.showcase.scenarios import web_interlude  # noqa: E402

set_validation_mode(ValidationMode.STRICT)

# Unattended mode: dialogs are accepted, no user interaction
execenv.unattended = True
execenv.verbose = "quiet"

INITIAL_CWD = os.getcwd()


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add the option showing the windows during the tests"""
    parser.addoption(
        "--show-windows",
        action="store_true",
        default=False,
        help="Display Qt windows during tests (disables QT_QPA_PLATFORM=offscreen)",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Select the offscreen Qt platform, unless the windows are shown"""
    if not config.getoption("--show-windows"):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(autouse=True)
def reset_datalab_configuration():
    """Start every test with the default configuration of DataLab, not persisted"""
    ensure_initialized(load_user_config=False)
    reset_to_defaults()
    Conf.rpc_server_enabled.set(False)
    # Keep pytest's faulthandler, which reports crashes in the test output
    Conf.faulthandler_enabled.set(False)
    try:
        yield
    finally:
        # pylint: disable=import-outside-toplevel
        from datalab.tests import close_datalab_background

        close_datalab_background()


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Store the settings of the showcase and the browser profile of the DataLab
    Web interlude in a temporary folder"""
    path = str(tmp_path / "showcase.json")
    monkeypatch.setattr(settings_module, "get_settings_path", lambda: path)
    profile_dir = str(tmp_path / "showcase-browser")
    monkeypatch.setattr(web_interlude, "get_profile_dir", lambda: profile_dir)
    return path


@pytest.fixture(autouse=True)
def reset_cwd():
    """Reset the current working directory after each test"""
    yield
    os.chdir(INITIAL_CWD)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_teardown(item, nextitem):  # pylint: disable=unused-argument
    """Unregister the plugins and destroy the widgets of the test"""
    PluginRegistry.unregister_all_plugins()
    if QC.QCoreApplication.instance() is not None:
        QC.QCoreApplication.processEvents()
        QC.QCoreApplication.sendPostedEvents(None, QC.QEvent.DeferredDelete)
    gc.collect()
