"""Contract tests for the generated DataLab plugin."""

from datalab.plugins import PluginCapability

from datalab_showcase import __version__
from datalab_showcase.adapters import desktop


def test_plugin_descriptor() -> None:
    """The generated entry point exposes stable SDK metadata."""
    plugin_class = desktop.DataLabShowcasePlugin
    assert plugin_class.get_plugin_id() == "org.datalab.showcase"
    assert plugin_class.PLUGIN_INFO.version == __version__
    assert plugin_class.PLUGIN_INFO.capabilities == frozenset(
        {
            PluginCapability.VISUALIZATION,
        }
    )
