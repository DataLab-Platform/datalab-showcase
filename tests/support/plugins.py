# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Test doubles of application plugins
===================================

Adapted from the test suite of the Applications panel of DataLab
(``datalab/tests/features/plugins/applications_panel_test.py``): the plugin tests
do not depend on the private helpers of the DataLab test suite.
"""

from __future__ import annotations

from types import SimpleNamespace

from datalab.plugins import PluginCapability, PluginInfo, PluginRegistry
from datalab.plugins.examples import PluginExample
from datalab.plugins.recipe_binding import RecipeReadiness, RecipeReadinessStatus
from datalab.plugins.recipes import RecipeDescriptor
from datalab.plugins.tools import PluginTool

#: Capabilities of an application plugin
APPLICATION = frozenset({PluginCapability.APPLICATION})


def application_plugin(
    plugin_id: str,
    name: str,
    capabilities: frozenset[PluginCapability] = APPLICATION,
    *,
    recipes: tuple[RecipeDescriptor, ...] = (),
    examples: tuple[PluginExample, ...] = (),
    tools: tuple[PluginTool, ...] = (),
    documentation_url: str | None = None,
    icon: str | None = None,
    calls: list[tuple] | None = None,
    readiness: RecipeReadiness | None = None,
) -> object:
    """Build the minimal active-plugin surface consumed by the Applications panel

    Args:
        plugin_id: Plugin ID
        name: Plugin name
        capabilities: Plugin capabilities
        recipes: Recipes of the plugin
        examples: Examples of the plugin
        tools: Tools of the plugin
        documentation_url: Documentation URL
        icon: Plugin icon
        calls: List recording the commands run on the plugin
        readiness: Readiness of the recipes

    Returns:
        Plugin double, to be added to the registered plugins
    """
    calls = [] if calls is None else calls
    if readiness is None:
        readiness = RecipeReadiness(RecipeReadinessStatus.NO_INPUT, {})
    plugin = SimpleNamespace(
        plugin_id=plugin_id,
        info=PluginInfo(
            id=plugin_id,
            name=name,
            version="1.2.3",
            description=f"{name} description",
            icon=icon,
            capabilities=capabilities,
            documentation_url=documentation_url,
        ),
        get_recipes=lambda: recipes,
        get_examples=lambda: examples,
        get_tools=lambda: tools,
        assess_recipe=lambda recipe_id: readiness,
        assess_tool=lambda tool_id: None,
        launch_recipe=lambda recipe_id: calls.append(("recipe", recipe_id)),
        try_example=lambda example_id, recipe_id: calls.append(
            ("try", example_id, recipe_id)
        ),
        launch_example=lambda example_id: calls.append(("example", example_id)),
        launch_tool=lambda tool_id: calls.append(("tool", tool_id)),
    )
    # Registered plugins are unregistered after each test (see conftest.py)
    plugin.unregister = lambda: PluginRegistry.unregister_plugin(plugin)
    return plugin
