# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""Start of the showcase requested on the command line, deferred until DataLab is
ready."""

from __future__ import annotations

import sys

import pytest
from datalab.env import DLExecEnv, execenv
from datalab.tests import datalab_test_app_context
from guidata.qthelpers import qt_app_context
from qtpy import QtCore as QC
from qtpy import QtWidgets as QW

from datalab_showcase.core.commandline import ShowcaseRequest, parse_arguments
from datalab_showcase.showcase import startup


@pytest.fixture(name="started_property")
def fixture_started_property() -> None:
    """Forget that the showcase was started in this process, after the test"""
    yield
    app = QW.QApplication.instance()
    if app is not None:
        app.setProperty(startup.STARTED_PROPERTY, False)


def run_event_loop(until, timeout_ms: int = 5000) -> None:
    """Run the event loop of the application until a condition is met (or until a
    timeout)

    The event loop of the application is used, not a local ``QEventLoop``: once
    the application has quit (e.g. at the end of a previous test), a local event
    loop returns at once, until the event loop of the application runs again.

    Args:
        until: Callable returning True to stop the loop
        timeout_ms: Maximum duration of the loop (ms)
    """
    app = QW.QApplication.instance()
    timer = QC.QTimer()
    timer.timeout.connect(lambda: until() and app.quit())
    timer.start(20)
    deadline = QC.QTimer()
    deadline.setSingleShot(True)
    deadline.timeout.connect(app.quit)
    deadline.start(timeout_ms)
    app.exec()
    timer.stop()
    deadline.stop()


def test_datalab_command_line(monkeypatch: pytest.MonkeyPatch) -> None:
    """DataLab ignores the showcase options given with ``=``, but takes a separated
    value as an HDF5 file to open: the showcase reports it"""
    arguments = [
        "--showcase=d1,d3",
        "--showcase-loop",
        "--showcase-speed=0.7",
        "--showcase-screen=1",
        "--showcase-fullscreen",
        "--showcase-web=https://host/web-showcase/",
    ]
    monkeypatch.setattr(sys, "argv", ["datalab", *arguments])
    assert DLExecEnv().h5files is None
    assert parse_arguments(arguments).warnings == []
    arguments = ["--showcase", "d1"]
    monkeypatch.setattr(sys, "argv", ["datalab", *arguments])
    assert DLExecEnv().h5files == ["d1"]
    parsed = parse_arguments(arguments)
    assert parsed.request == ShowcaseRequest(scenarios="all")
    assert len(parsed.warnings) == 1 and "--showcase=d1" in parsed.warnings[0]


def test_event_loop_detection() -> None:
    """The event loop is detected with the Qt binding in use, but not while events
    are processed by ``processEvents``"""
    states: list[bool] = []

    def record_state() -> None:
        states.append(startup.is_event_loop_running())

    with qt_app_context():
        assert not startup.is_event_loop_running()
        QC.QTimer.singleShot(0, record_state)
        for _index in range(100):
            QW.QApplication.processEvents()
            if states:
                break
        QC.QTimer.singleShot(0, record_state)
        run_event_loop(lambda: len(states) >= 2)
        assert not startup.is_event_loop_running()
    assert states == [False, True]


@pytest.mark.usefixtures("started_property")
def test_deferred_start_waits_until_datalab_is_ready() -> None:
    """The showcase starts once the event loop runs, the main window is visible and
    no modal dialog is shown; the log files question is skipped meanwhile"""
    played: list[ShowcaseRequest] = []
    loop_running = [False]
    request = ShowcaseRequest(scenarios="d1")
    do_not_quit = execenv.do_not_quit
    with qt_app_context():
        win = QW.QMainWindow()
        deferred = startup.DeferredStart(
            win,
            request,
            play=lambda _win, req: played.append(req),
            loop_running=lambda: loop_running[0],
        )
        deferred.timer.stop()  # Polled by the test
        assert execenv.do_not_quit
        deferred.poll()
        win.show()
        deferred.poll()
        assert not deferred.is_ready()
        loop_running[0] = True
        dialog = QW.QDialog(win)
        dialog.setModal(True)
        dialog.show()
        deferred.poll()
        assert not deferred.finished and not played
        dialog.close()
        deferred.poll()
        assert deferred.finished and execenv.do_not_quit == do_not_quit
        QW.QApplication.processEvents()
        assert played == [request]
        deferred.poll()
        QW.QApplication.processEvents()
        assert played == [request]
        assert QW.QApplication.instance().property(startup.STARTED_PROPERTY)
        win.close()


@pytest.mark.usefixtures("started_property")
def test_start_from_command_line() -> None:
    """The showcase is started once, from the startup of DataLab only"""
    with qt_app_context():
        win = QW.QMainWindow()
        assert startup.start_from_command_line(win, ["--showcase-loop"]) is None
        deferred = startup.start_from_command_line(win, ["--showcase=d2"])
        assert deferred.request == ShowcaseRequest(scenarios="d2")
        deferred.cancel()
        # Plugins reloaded while DataLab runs
        results: list = []
        QC.QTimer.singleShot(
            0,
            lambda: results.append(
                startup.start_from_command_line(win, ["--showcase"])
            ),
        )
        run_event_loop(lambda: bool(results))
        assert results == [None]
        # Started once per process
        QW.QApplication.instance().setProperty(startup.STARTED_PROPERTY, True)
        assert startup.start_from_command_line(win, ["--showcase"]) is None


@pytest.mark.usefixtures("started_property")
def test_showcase_starts_in_datalab(monkeypatch: pytest.MonkeyPatch) -> None:
    """DataLab started with ``--showcase=...`` plays the showcase once its event loop
    runs"""
    played: list[tuple] = []
    monkeypatch.setattr(sys, "argv", ["datalab", "--showcase=d3", "--showcase-loop"])
    monkeypatch.setattr(
        startup, "play_request", lambda win, request: played.append((win, request))
    )
    do_not_quit = execenv.do_not_quit
    with datalab_test_app_context(console=False) as win:
        assert execenv.do_not_quit
        assert not played
        run_event_loop(lambda: bool(played))
        assert played == [(win, ShowcaseRequest(scenarios="d3", loop=True))]
        assert execenv.do_not_quit == do_not_quit
