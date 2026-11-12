"""DataLab Desktop plugin adapter."""

from __future__ import annotations

from datalab.plugins import PluginBase, PluginCapability, PluginInfo

from .. import PLUGIN_DESCRIPTION, PLUGIN_ID, PLUGIN_NAME, __version__
from ..workflow import RECIPES as WORKFLOW_RECIPES


class DataLabShowcasePlugin(PluginBase):
    """Expose the plugin to DataLab Desktop."""

    PLUGIN_INFO = PluginInfo(
        id=PLUGIN_ID,
        name=PLUGIN_NAME,
        version=__version__,
        description=PLUGIN_DESCRIPTION,
        capabilities=(PluginCapability.VISUALIZATION,),
    )
    RECIPES = WORKFLOW_RECIPES

    def create_actions(self) -> None:
        """Create plugin actions after the DataLab panels are ready."""
