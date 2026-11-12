# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Showcase started from the command line
======================================

The :mod:`datalab_showcase.showcase.startup` module starts the showcase requested
on the command line of DataLab (``--showcase`` options, see
:mod:`datalab_showcase.core.commandline`).

DataLab registers its plugins while it builds its main window: before showing it,
before running its startup actions (``execute_post_show_actions``) and before
running its event loop. The startup actions may ask questions, e.g. whether to
show the log files of a previous session which ended abnormally (SigimaX
``check_for_previous_crash``): such a question would block a booth computer
started unattended. The start of the showcase is therefore deferred
(:class:`DeferredStart`):

1. At registration, ``execenv.do_not_quit`` is set (its previous value is kept):
   the log files question is skipped (``check_for_previous_crash`` returns early
   in this case).
2. A timer then checks, until all these conditions are met, that the main event
   loop runs (``QThread.loopLevel() > 0``, true in the event loop of
   ``QApplication.exec`` and in the nested loop of a modal dialog), that the main
   window is visible, and that no modal dialog (e.g. another startup question)
   nor popup is shown.
3. ``execenv.do_not_quit`` is restored, then the showcase is played.

The showcase is started this way only once per process, and only when the plugin
is registered while DataLab starts (not when the plugins are reloaded).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

from datalab.env import execenv
from qtpy import QtCore as QC
from qtpy import QtWidgets as QW

from datalab_showcase.core.commandline import ShowcaseRequest, parse_arguments
from datalab_showcase.showcase.player import (
    ScenarioResult,
    ShowcaseOptions,
    play_showcase,
)

if TYPE_CHECKING:
    from datalab.gui.main import DLMainWindow

logger = logging.getLogger("datalab_showcase")

#: Name of the property of the application set once the showcase was started from
#: the command line (only once per process)
STARTED_PROPERTY = "datalab_showcase_started"


def is_event_loop_running() -> bool:
    """Return True while an event loop runs in the current thread

    Returns:
        True in the event loop of ``QApplication.exec``, or in the nested event loop
         of a modal dialog (but not while events are processed by
         ``processEvents``)
    """
    return QC.QThread.currentThread().loopLevel() > 0


def play_request(win: DLMainWindow, request: ShowcaseRequest) -> list[ScenarioResult]:
    """Play the showcase requested on the command line

    Args:
        win: DataLab main window
        request: Showcase request

    Returns:
        Results of the scenarios played
    """
    logger.info("Showcase requested on the command line: %s", request)
    results = play_showcase(win, ShowcaseOptions.from_request(request))
    for result in results:
        if result.status != "done":
            logger.warning("Showcase scenario %s %s", result.scenario_id, result.status)
    return results


class DeferredStart(QC.QObject):
    """Start of the showcase requested on the command line, deferred until DataLab
    is ready (see :mod:`datalab_showcase.showcase.startup`)

    The object is a child of the main window: it is deleted once the showcase is
    started, or when the start is cancelled (:meth:`cancel`).

    Args:
        win: DataLab main window
        request: Showcase request
        play: Callable playing the showcase (default: :func:`play_request`)
        loop_running: Callable returning True while the event loop runs (default:
         :func:`is_event_loop_running`)
    """

    #: Interval (ms) between two checks of the startup conditions
    POLL_INTERVAL_MS = 200

    def __init__(
        self,
        win: DLMainWindow,
        request: ShowcaseRequest,
        play: Callable[[DLMainWindow, ShowcaseRequest], object] | None = None,
        loop_running: Callable[[], bool] | None = None,
    ) -> None:
        super().__init__(win)
        self.setObjectName("datalab_showcase_deferred_start")
        self.win = win
        self.request = request
        self.__play = play_request if play is None else play
        self.__loop_running = (
            is_event_loop_running if loop_running is None else loop_running
        )
        #: True once the showcase is started, or its start cancelled
        self.finished = False
        self.__do_not_quit = execenv.do_not_quit
        # No question about the log files of a previous session (see module doc)
        execenv.do_not_quit = True
        self.timer = QC.QTimer(self)
        self.timer.setObjectName("datalab_showcase_deferred_start_timer")
        self.timer.setInterval(self.POLL_INTERVAL_MS)
        self.timer.timeout.connect(self.poll)
        self.timer.start()

    def is_ready(self) -> bool:
        """Return True once DataLab is ready to play the showcase

        Returns:
            True if the event loop runs, the main window is visible, and no modal
             dialog nor popup is shown
        """
        return (
            self.__loop_running()
            and self.win.isVisible()
            and QW.QApplication.activeModalWidget() is None
            and QW.QApplication.activePopupWidget() is None
        )

    def poll(self) -> None:
        """Start the showcase once DataLab is ready (timer)"""
        if self.finished or not self.is_ready():
            return
        win, request, play = self.win, self.request, self.__play
        self.__finish()
        app = QW.QApplication.instance()
        app.setProperty(STARTED_PROPERTY, True)
        # Played outside of the slot of the timer, which is deleted meanwhile
        QC.QTimer.singleShot(0, lambda: play(win, request))

    def cancel(self) -> None:
        """Cancel the start of the showcase, if not started yet"""
        self.__finish()

    def __finish(self) -> None:
        """Stop the timer, restore ``execenv.do_not_quit``, then delete the object"""
        if self.finished:
            return
        self.finished = True
        self.timer.stop()
        execenv.do_not_quit = self.__do_not_quit
        self.deleteLater()


def start_from_command_line(
    win: DLMainWindow, arguments: Sequence[str]
) -> DeferredStart | None:
    """Start the showcase requested on the command line, once DataLab is ready

    The options are parsed (warnings are logged). Nothing is done without the
    ``--showcase`` option, when the event loop already runs (the plugins are
    reloaded), or if the showcase was already started from the command line in
    this process.

    Args:
        win: DataLab main window, being built
        arguments: Command-line arguments, without the program name

    Returns:
        Deferred start, or None if the showcase is not started
    """
    parsed = parse_arguments(arguments)
    for message in parsed.warnings:
        logger.warning(message)
    if parsed.request is None:
        return None
    app = QW.QApplication.instance()
    if is_event_loop_running() or app.property(STARTED_PROPERTY):
        logger.info("Showcase not started again: DataLab is already running")
        return None
    return DeferredStart(win, parsed.request)


__all__ = [
    "DeferredStart",
    "is_event_loop_running",
    "play_request",
    "start_from_command_line",
]
