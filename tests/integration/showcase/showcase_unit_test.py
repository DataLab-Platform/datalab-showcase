# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Showcase mode unit tests

Command-line options and scenario selection of the showcase mode.
"""

from __future__ import annotations

import pytest

from datalab_showcase.core.commandline import DEFAULT_WEB_URL, parse_arguments
from datalab_showcase.showcase.engine import ScenarioSkipped, ShowcaseScenario
from datalab_showcase.showcase.player import (
    ShowcaseOptions,
    interleave,
    parse_scenario_ids,
    select_scenarios,
)
from datalab_showcase.showcase.scenarios import get_native_scenarios


def test_showcase_command_line_options() -> None:
    """All the showcase options are parsed, and give the showcase options"""
    parsed = parse_arguments(
        [
            "--showcase=d1,d3",
            "--showcase-loop",
            "--showcase-speed=0.7",
            "--showcase-screen=1",
            "--showcase-fullscreen",
            "--showcase-web=http://localhost:5173/",
        ]
    )
    assert not parsed.warnings
    request = parsed.request
    assert request.scenarios == "d1,d3"
    assert request.loop and request.fullscreen
    assert request.speed == pytest.approx(0.7)
    assert request.screen == 1
    assert request.web_url == "http://localhost:5173/"
    assert ShowcaseOptions.from_request(request) == ShowcaseOptions(
        scenario_ids=["d1", "d3"],
        loop=True,
        speed=0.7,
        fullscreen=True,
        screen=1,
        web_url="http://localhost:5173/",
    )
    # Without URL, the host page of the DataLab Web showcase is played
    parsed = parse_arguments(["--showcase", "--showcase-web"])
    assert parsed.request.web_url == DEFAULT_WEB_URL


def test_showcase_command_line_defaults() -> None:
    """Without IDS, --showcase plays all the scenarios, once, at normal pace"""
    request = parse_arguments(["--showcase"]).request
    assert request.scenarios == "all"
    assert not request.loop and not request.fullscreen
    assert request.speed is None and request.screen is None
    assert request.web_url is None
    assert ShowcaseOptions.from_request(request) == ShowcaseOptions()
    assert parse_arguments([]).request is None


def test_scenario_selection() -> None:
    """Scenarios are selected from their IDs, in the requested order"""
    assert parse_scenario_ids(None) is None
    assert parse_scenario_ids("all") is None
    assert parse_scenario_ids(" d1, ,d3 ") == ["d1", "d3"]
    assert interleave([1, 2, 3], ["a"]) == [1, "a", 2, 3]
    assert interleave([1], ["a", "b", "c"]) == [1, "a", "b", "c"]
    scenarios = get_native_scenarios()
    assert [scenario.id for scenario in scenarios] == ["d1", "d2", "d3", "d4"]
    assert all(scenario.title and scenario.subtitle for scenario in scenarios)
    selected = select_scenarios(scenarios, ["d3", "unknown", "d1", "d3"])
    assert [scenario.id for scenario in selected] == ["d3", "d1"]
    assert select_scenarios(scenarios, None) == scenarios


def test_scenario_requirements() -> None:
    """A scenario requiring a missing module is skipped"""
    scenario = ShowcaseScenario(
        "missing", "Missing", lambda ctx: None, requires=("json", "no_such_module")
    )
    assert scenario.missing_requirements() == ["no_such_module"]
    with pytest.raises(ScenarioSkipped):
        scenario.check_requirements()
