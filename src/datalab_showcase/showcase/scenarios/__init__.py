# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Native showcase scenarios
=========================

Each module of the :mod:`datalab_showcase.showcase.scenarios` package defines a
module-level ``SCENARIO`` (:class:`~datalab_showcase.showcase.engine.ShowcaseScenario`)
whose ``run`` callable plays the scenario with a
:class:`~datalab_showcase.showcase.engine.ShowcaseContext`.

The DataLab Web interlude (:mod:`~datalab_showcase.showcase.scenarios.web_interlude`)
is not a native scenario: the player adds it to the playlist when a DataLab Web
URL is given.
"""

from __future__ import annotations

from datalab_showcase.showcase.engine import ShowcaseScenario
from datalab_showcase.showcase.scenarios import (
    d1_provenance,
    d2_capsule,
    d3_image_analysis,
    d4_automation,
    web_interlude,
)

__all__ = ["SCENARIO_MODULES", "get_native_scenarios", "web_interlude"]

#: Modules of the native scenarios, in playing order
SCENARIO_MODULES = (d1_provenance, d2_capsule, d3_image_analysis, d4_automation)


def get_native_scenarios() -> list[ShowcaseScenario]:
    """Return the native showcase scenarios, in playing order

    Returns:
        Native scenarios
    """
    return [module.SCENARIO for module in SCENARIO_MODULES]
