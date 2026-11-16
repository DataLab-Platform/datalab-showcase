# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Showcase mode
=============

The :mod:`datalab_showcase.showcase` package implements the showcase mode:
live and unattended demos of DataLab features, for exhibitions and booths.

The showcase mode is started from the **Plugins > DataLab Showcase** menu
(**Showcase mode...**), with the ``--showcase`` command-line options of DataLab
(see :mod:`datalab_showcase.core.commandline` and
:mod:`datalab_showcase.showcase.startup`), or with the ``datalab-showcase``
command. It plays the native scenarios (:mod:`datalab_showcase.showcase.scenarios`)
and the scenarios generated for the active application plugins
(:mod:`datalab_showcase.showcase.applications`), and optionally ends each loop
with a DataLab Web interlude, for booths with a single screen
(:mod:`datalab_showcase.showcase.scenarios.web_interlude`).

.. note::

    This package must not import the test suites (e.g. :mod:`datalab.tests`),
    whose dependencies (e.g., ``pytest``) are not available in the standalone
    application.
"""

from __future__ import annotations

from datalab_showcase.showcase.dialog import (
    ShowcaseDialog,
    close_showcase_dialog,
    show_showcase_dialog,
)
from datalab_showcase.showcase.engine import (
    ScenarioSkipped,
    ShowcaseContext,
    ShowcaseScenario,
)
from datalab_showcase.showcase.player import (
    ScenarioResult,
    ShowcaseOptions,
    ShowcasePlayer,
    get_showcase_scenarios,
    is_showcase_playing,
    play_showcase,
    stop_showcase,
)

__all__ = [
    "ScenarioResult",
    "ScenarioSkipped",
    "ShowcaseContext",
    "ShowcaseDialog",
    "ShowcaseOptions",
    "ShowcasePlayer",
    "ShowcaseScenario",
    "close_showcase_dialog",
    "get_showcase_scenarios",
    "is_showcase_playing",
    "play_showcase",
    "show_showcase_dialog",
    "stop_showcase",
]
