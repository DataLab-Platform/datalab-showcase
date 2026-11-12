# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""The plugin in DataLab: registration, actions and unregistration."""

from __future__ import annotations

import sys

import pytest
from datalab.env import execenv
from datalab.gui.main import DLMainWindow
from datalab.gui.plugins.applications import get_application_plugins
from datalab.plugins import PluginBase, PluginRegistry
from datalab.tests import datalab_test_app_context
from qtpy import QtCore as QC
from qtpy import QtWidgets as QW

from datalab_showcase import PLUGIN_ID, PLUGIN_NAME, __version__
from datalab_showcase.adapters import desktop
from datalab_showcase.showcase import dialog as dialog_module

ACTION_TITLE = "Showcase mode..."


def get_showcase_plugin() -> PluginBase:
    """Return the showcase plugin registered by DataLab

    DataLab finds the plugin from the ``datalab_`` prefix of its package (``src``
    is on the Python path of the tests): the plugin class may be reloaded, it is
    found from its ID.
    """
    plugins = [p for p in PluginRegistry.get_plugins() if p.plugin_id == PLUGIN_ID]
    assert len(plugins) == 1, "The showcase plugin is not registered"
    return plugins[0]


def get_showcase_actions(win: DLMainWindow) -> list[QW.QAction]:
    """Return the visible showcase actions of the data panels"""
    return [
        action
        for panel in (win.signalpanel, win.imagepanel)
        for action in panel.actions()
        if action.text() == ACTION_TITLE and action.isVisible()
    ]


def get_plugin_timers(win: DLMainWindow) -> list[QC.QObject]:
    """Return the objects of the plugin owned by the main window"""
    return [
        obj
        for obj in win.findChildren(QC.QObject)
        if obj.objectName().startswith("datalab_showcase")
    ]


def test_plugin_descriptor() -> None:
    """The entry point exposes the identity of the plugin, without capability"""
    plugin_class = desktop.ShowcasePlugin
    assert plugin_class.get_plugin_id() == PLUGIN_ID == "org.datalab.showcase"
    assert plugin_class.PLUGIN_INFO.name == PLUGIN_NAME == "DataLab Showcase"
    assert plugin_class.PLUGIN_INFO.version == __version__
    assert plugin_class.PLUGIN_INFO.capabilities == frozenset()


def test_plugin_actions() -> None:
    """The plugin adds **Showcase mode...** to its menu, in both data panels, and
    is not an application of the Applications panel"""
    with datalab_test_app_context(console=False) as win:
        plugin = get_showcase_plugin()
        assert plugin not in get_application_plugins()
        assert plugin.deferred_start is None
        actions = get_showcase_actions(win)
        assert len(actions) == 2 and actions == plugin.actions
        for action in actions:
            assert action.isEnabled() and not action.icon().isNull()
        win.signalpanel.acthandler.selected_objects_changed([], [])
        assert actions[0].isEnabled()


def test_action_opens_the_dialog(monkeypatch: pytest.MonkeyPatch) -> None:
    """The action opens the Showcase mode dialog (cancelled here)"""
    opened: list[QW.QDialog] = []

    def reject_dialog(dialog: QW.QDialog) -> int:
        opened.append(dialog)
        assert dialog_module.ShowcaseDialog.opened is dialog
        return 0

    monkeypatch.setattr(dialog_module, "exec_dialog", reject_dialog)
    with datalab_test_app_context(console=False) as win:
        get_showcase_actions(win)[0].trigger()
        assert len(opened) == 1
        assert isinstance(opened[0], dialog_module.ShowcaseDialog)
        assert dialog_module.ShowcaseDialog.opened is None


def test_unregister_removes_the_actions() -> None:
    """Unregistering the plugin removes its actions, and leaves no object"""
    with datalab_test_app_context(console=False) as win:
        plugin = get_showcase_plugin()
        actions = list(plugin.actions)
        plugin.unregister()
        assert not get_showcase_actions(win)
        assert plugin.actions == [] and plugin not in PluginRegistry.get_plugins()
        for action in actions:
            assert not action.isVisible() and not action.isEnabled()
            assert all(
                action not in panel.actions()
                for panel in (win.signalpanel, win.imagepanel)
            )
        # The action handlers still update the actions on selection changes
        win.signalpanel.acthandler.selected_objects_changed([], [])
        assert not actions[0].isEnabled()
        assert not get_plugin_timers(win)


def test_reload_plugins() -> None:
    """Reloading the plugins gives one Showcase mode action per panel"""
    with datalab_test_app_context(console=False) as win:
        win.reload_plugins()
        win.reload_plugins()
        plugin = get_showcase_plugin()
        assert get_showcase_actions(win) == plugin.actions
        assert len(plugin.actions) == 2
        assert plugin.deferred_start is None


def test_unregister_cancels_the_start(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unregistering the plugin before the showcase starts cancels the start, and
    restores the execution environment"""
    monkeypatch.setattr(sys, "argv", ["datalab", "--showcase=d1"])
    do_not_quit = execenv.do_not_quit
    with datalab_test_app_context(console=False) as win:
        plugin = get_showcase_plugin()
        deferred = plugin.deferred_start
        assert deferred is not None and not deferred.finished
        assert execenv.do_not_quit
        assert [obj.objectName() for obj in get_plugin_timers(win)] == [
            "datalab_showcase_deferred_start",
            "datalab_showcase_deferred_start_timer",
        ]
        plugin.unregister()
        assert deferred.finished and plugin.deferred_start is None
        assert execenv.do_not_quit == do_not_quit
        QW.QApplication.sendPostedEvents(None, QC.QEvent.DeferredDelete)
        assert not get_plugin_timers(win)
