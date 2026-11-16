# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
DataLab Desktop plugin adapter
==============================

The :class:`ShowcasePlugin` class exposes the showcase mode to DataLab:

- **Plugins > DataLab Showcase > Showcase mode...** opens the **Showcase mode**
  dialog (see :mod:`datalab_showcase.showcase.dialog`).
- The ``--showcase`` command-line options of DataLab start the showcase once
  DataLab is ready (see :mod:`datalab_showcase.showcase.startup`).

The plugin declares no capability: it is not listed in the Applications panel.
Unregistering it (e.g. when the plugins are reloaded) cancels a pending start,
stops the showcase playing (after the current demo), closes the Showcase mode
dialog and removes the actions of the plugin.
"""

from __future__ import annotations

import sys

from datalab.gui.plugins.applications import get_plugin_icon
from datalab.plugins import PluginBase, PluginInfo
from qtpy import QtWidgets as QW

from datalab_showcase import PLUGIN_DESCRIPTION, PLUGIN_ID, PLUGIN_NAME, __version__
from datalab_showcase.i18n import _
from datalab_showcase.showcase import (
    close_showcase_dialog,
    show_showcase_dialog,
    stop_showcase,
)
from datalab_showcase.showcase.startup import DeferredStart, start_from_command_line

#: Icon of the plugin and of its action
PLUGIN_ICON = "datalab_showcase:icons/showcase.svg"
#: Documentation of the plugin
DOCUMENTATION_URL = "https://github.com/DataLab-Platform/datalab-showcase#readme"


class ShowcasePlugin(PluginBase):
    """Showcase mode: live and unattended demos of DataLab features"""

    PLUGIN_INFO = PluginInfo(
        id=PLUGIN_ID,
        name=PLUGIN_NAME,
        version=__version__,
        description=PLUGIN_DESCRIPTION,
        icon=PLUGIN_ICON,
        documentation_url=DOCUMENTATION_URL,
    )

    def __init__(self) -> None:
        super().__init__()
        #: Actions created by the plugin (one per data panel)
        self.actions: list[QW.QAction] = []
        #: Start of the showcase requested on the command line, until it starts
        self.deferred_start: DeferredStart | None = None

    def register_hooks(self) -> None:
        """Start the showcase requested on the command line, once DataLab is ready"""
        self.deferred_start = start_from_command_line(self.main, sys.argv[1:])

    def unregister_hooks(self) -> None:
        """Stop the showcase and remove what the plugin added to DataLab"""
        if self.deferred_start is not None:
            self.deferred_start.cancel()
            self.deferred_start = None
        stop_showcase()
        close_showcase_dialog()
        self.__remove_actions()

    def create_actions(self) -> None:
        """Add **Showcase mode...** to the menu of the plugin, in both panels"""
        title = PLUGIN_NAME.replace("&", "&&")
        for panel in (self.signalpanel, self.imagepanel):
            handler = panel.acthandler
            with handler.new_menu(title):
                action = handler.new_action(
                    _("Showcase mode") + "...",
                    triggered=self.show_showcase_dialog,
                    tip=_(
                        "Play live demos of DataLab features, without any user "
                        "interaction, for exhibitions and booths."
                    ),
                    select_condition="always",
                )
            action.setIcon(get_plugin_icon(PLUGIN_ICON))
            self.actions.append(action)

    def show_showcase_dialog(self) -> None:
        """Show the Showcase mode dialog, then play the showcase"""
        show_showcase_dialog(self.main)

    def __remove_actions(self) -> None:
        """Remove the actions of the plugin from DataLab menus and panels

        The action handlers of DataLab keep a reference to each action (to enable
        it on selection changes): the actions are disconnected and hidden, never
        deleted.
        """
        for action in self.actions:
            # The panel shows the action too (for its shortcut)
            for widget in _associated_widgets(action):
                widget.removeAction(action)
            action.triggered.disconnect()
            action.setVisible(False)
            action.setEnabled(False)
        self.actions.clear()


def _associated_widgets(action: QW.QAction) -> list[QW.QWidget]:
    """Return the widgets showing an action (panels, menus, toolbars)

    Args:
        action: Action

    Returns:
        Widgets showing the action
    """
    # QAction.associatedWidgets (Qt 5) became QAction.associatedObjects (Qt 6)
    if hasattr(action, "associatedObjects"):
        objects = action.associatedObjects()
    else:
        objects = action.associatedWidgets()
    return [obj for obj in objects if isinstance(obj, QW.QWidget)]
