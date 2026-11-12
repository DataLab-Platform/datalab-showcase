# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Showcase mode dialog
====================

The :mod:`datalab_showcase.showcase.dialog` module implements the **Showcase mode**
dialog (**Plugins > DataLab Showcase** menu): choice of the demos to play and of
the playing options.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from datalab.env import execenv
from guidata.configtools import get_icon
from guidata.qthelpers import exec_dialog
from qtpy import QtCore as QC
from qtpy import QtGui as QG
from qtpy import QtWidgets as QW

from datalab_showcase.i18n import _
from datalab_showcase.showcase.player import (
    PACE_SPEEDS,
    ScenarioResult,
    ShowcaseOptions,
    get_showcase_scenarios,
    is_showcase_playing,
    play_showcase,
)
from datalab_showcase.showcase.scenarios import web_interlude
from datalab_showcase.showcase.settings import load_settings, save_settings

if TYPE_CHECKING:
    from datalab.gui.main import DLMainWindow

    from datalab_showcase.showcase.engine import ShowcaseScenario

#: Icon of the showcase mode (DataLab icon)
ICON_NAME = "replay.svg"


class ShowcaseDialog(QW.QDialog):
    """Showcase mode dialog: choice of the demos and of the playing options

    The choices are remembered in the settings of the showcase (see
    :mod:`datalab_showcase.showcase.settings`).

    Args:
        parent: Parent widget (DataLab main window)
        scenarios: Available scenarios
    """

    #: Dialog opened by :func:`show_showcase_dialog`, if any
    opened: ShowcaseDialog | None = None

    def __init__(self, parent: QW.QWidget, scenarios: list[ShowcaseScenario]) -> None:
        super().__init__(parent)
        self.setWindowTitle(_("Showcase mode"))
        self.setWindowIcon(get_icon(ICON_NAME))
        self.scenarios = scenarios
        #: Settings of the showcase, updated once the dialog is accepted
        self.settings = settings = load_settings()
        #: Options chosen by the user, once the dialog is accepted
        self.options: ShowcaseOptions | None = None
        layout = QW.QVBoxLayout(self)
        intro = QW.QLabel(
            _(
                "Play live demos of DataLab features, without any user "
                "interaction, for exhibitions and booths."
            )
            + "<br><br>"
            + _(
                "Hotkeys: F9 to pause or resume, Shift+F12 to stop after the "
                "current demo."
            ),
            self,
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        group = QW.QGroupBox(_("Demos"), self)
        group_layout = QW.QVBoxLayout(group)
        self.scenario_list = QW.QListWidget(group)
        excluded = set(settings.excluded_scenarios)
        for scenario in scenarios:
            item = QW.QListWidgetItem(scenario.title, self.scenario_list)
            item.setData(QC.Qt.UserRole, scenario.id)
            item.setToolTip(scenario.subtitle or "")
            item.setFlags(item.flags() | QC.Qt.ItemIsUserCheckable)
            checked = scenario.id not in excluded
            item.setCheckState(QC.Qt.Checked if checked else QC.Qt.Unchecked)
        self.scenario_list.itemChanged.connect(self.__update_start_button)
        group_layout.addWidget(self.scenario_list)
        layout.addWidget(group)
        form = QW.QFormLayout()
        layout.addLayout(form)
        self.loop_check = QW.QCheckBox(_("Play in a loop"), self)
        self.loop_check.setChecked(settings.loop)
        form.addRow(self.loop_check)
        self.pace_combo = QW.QComboBox(self)
        for pace, label in (
            ("slow", _("Slow")),
            ("normal", _("Normal")),
            ("fast", _("Fast")),
        ):
            self.pace_combo.addItem(label, pace)
        index = self.pace_combo.findData(settings.pace)
        self.pace_combo.setCurrentIndex(index if index >= 0 else 1)
        form.addRow(_("Pace"), self.pace_combo)
        self.fullscreen_check = QW.QCheckBox(_("Full screen"), self)
        self.fullscreen_check.setChecked(settings.fullscreen)
        form.addRow(self.fullscreen_check)
        self.web_check = QW.QCheckBox(_("Include DataLab Web"), self)
        self.web_check.setToolTip(
            _(
                "For a single screen: each loop ends with one pass of the DataLab "
                "Web showcase, in a browser window (Google Chrome, Microsoft Edge "
                "or Chromium). The showcase resumes once the window is closed."
            )
        )
        self.web_check.setChecked(settings.web_enabled)
        form.addRow(self.web_check)
        self.web_url_edit = QW.QLineEdit(settings.web_url, self)
        self.web_url_edit.setPlaceholderText(web_interlude.DEFAULT_URL)
        self.web_url_edit.setToolTip(
            _("URL of the DataLab Web showcase (empty: %s)") % web_interlude.DEFAULT_URL
        )
        self.web_url_edit.setEnabled(self.web_check.isChecked())
        self.web_check.toggled.connect(self.web_url_edit.setEnabled)
        form.addRow(_("DataLab Web URL"), self.web_url_edit)
        #: Screen selector, only when several screens are available
        self.screen_combo: QW.QComboBox | None = None
        screens = QG.QGuiApplication.screens()
        if len(screens) > 1:
            self.screen_combo = QW.QComboBox(self)
            self.screen_combo.addItem(_("Current screen"), -1)
            for index, screen in enumerate(screens):
                self.screen_combo.addItem(f"{index + 1}: {screen.name()}", index)
            index = self.screen_combo.findData(settings.screen)
            self.screen_combo.setCurrentIndex(max(index, 0))
            form.addRow(_("Screen"), self.screen_combo)
        self.button_box = QW.QDialogButtonBox(
            QW.QDialogButtonBox.Ok | QW.QDialogButtonBox.Cancel, self
        )
        self.button_box.button(QW.QDialogButtonBox.Ok).setText(_("Start"))
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        self.__update_start_button()

    def get_selected_ids(self) -> list[str]:
        """Return the IDs of the checked scenarios, in playing order"""
        items = (
            self.scenario_list.item(row) for row in range(self.scenario_list.count())
        )
        return [
            item.data(QC.Qt.UserRole)
            for item in items
            if item.checkState() == QC.Qt.Checked
        ]

    def __update_start_button(self) -> None:
        """Enable the Start button when at least one scenario is checked"""
        button = self.button_box.button(QW.QDialogButtonBox.Ok)
        button.setEnabled(bool(self.get_selected_ids()))

    def __get_screen(self) -> int | None:
        """Return the index of the chosen screen, or None for the current one"""
        if self.screen_combo is None:
            return None
        index = self.screen_combo.currentData()
        return None if index < 0 else index

    def done(self, result: int) -> None:
        """Close the dialog, remembering the choices once it is accepted

        Args:
            result: Dialog result
        """
        if result == QW.QDialog.Accepted:
            self.__apply_choices()
        super().done(result)

    def __apply_choices(self) -> None:
        """Remember the choices in the settings and set :attr:`options`"""
        settings = self.settings
        selected = self.get_selected_ids()
        available = {scenario.id for scenario in self.scenarios}
        previous = set(settings.excluded_scenarios) - available
        excluded = previous | (available - set(selected))
        settings.excluded_scenarios = sorted(excluded)
        pace = self.pace_combo.currentData()
        settings.loop = self.loop_check.isChecked()
        settings.pace = pace
        settings.fullscreen = self.fullscreen_check.isChecked()
        screen = self.__get_screen()
        if self.screen_combo is not None:
            settings.screen = -1 if screen is None else screen
        web_url = self.web_url_edit.text().strip()
        settings.web_enabled = self.web_check.isChecked()
        settings.web_url = web_url
        save_settings(settings)
        self.options = ShowcaseOptions(
            scenario_ids=selected,
            loop=self.loop_check.isChecked(),
            speed=PACE_SPEEDS[pace],
            fullscreen=self.fullscreen_check.isChecked(),
            screen=screen,
            web_url=(web_url or web_interlude.DEFAULT_URL)
            if self.web_check.isChecked()
            else None,
        )


def show_showcase_dialog(win: DLMainWindow) -> list[ScenarioResult] | None:
    """Show the Showcase mode dialog, then play the showcase

    If the workspace is not empty, the user is warned that it will be cleared.

    Args:
        win: DataLab main window

    Returns:
        Results of the scenarios played, or None if the showcase was cancelled
    """
    if is_showcase_playing() or ShowcaseDialog.opened is not None:
        return None
    scenarios = get_showcase_scenarios(win)
    dialog = ShowcaseDialog(win, scenarios)
    ShowcaseDialog.opened = dialog
    try:
        accepted = exec_dialog(dialog)
    finally:
        ShowcaseDialog.opened = None
    if not accepted or dialog.options is None:
        return None
    if win.has_objects() and not execenv.unattended:
        answer = QW.QMessageBox.warning(
            win,
            _("Showcase mode"),
            _(
                "The showcase mode clears the workspace (signals, images, macros "
                "and history) before each demo."
            )
            + chr(10) * 2
            + _("Do you want to continue?"),
            QW.QMessageBox.Ok | QW.QMessageBox.Cancel,
        )
        if answer != QW.QMessageBox.Ok:
            return None
    return play_showcase(win, dialog.options, scenarios)


def close_showcase_dialog() -> None:
    """Close the Showcase mode dialog, if it is opened (e.g. when the plugin is
    unregistered)"""
    dialog = ShowcaseDialog.opened
    if dialog is not None:
        dialog.reject()
