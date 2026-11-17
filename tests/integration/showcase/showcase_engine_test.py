# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Showcase engine tests

Waiting loops, captions, modal-dialog guard, warm-up of the processing worker and
operator controls.
"""

from __future__ import annotations

import time
from collections.abc import Callable

import pytest
from datalab.env import execenv
from datalab.gui.processor.base import WorkerState
from datalab.tests import datalab_test_app_context
from guidata import qthelpers
from qtpy import QtCore as QC
from qtpy import QtWidgets as QW

from datalab_showcase.showcase import ShowcaseOptions, ShowcasePlayer
from datalab_showcase.showcase.engine import (
    NEXT_DEMO,
    RESTART_DEMO,
    STOP_NOW,
    ShowcaseContext,
    ShowcaseInterrupted,
    ShowcaseScenario,
    process_events,
)


@pytest.mark.parametrize("speed", [0.0, 0.01])
def test_waits_delete_the_objects_scheduled_for_deletion(speed: float) -> None:
    """Like the main event loop, the waits delete the objects scheduled for deletion

    The showcase never returns to the main event loop: replaced widgets would stay
    painted over the new ones.
    """
    with datalab_test_app_context(console=False) as win:
        ctx = ShowcaseContext(win, speed)
        deleted: list[str] = []
        for name, wait in (
            ("pause", lambda: ctx.pause(0.5)),
            ("wait_until", lambda: ctx.wait_until(lambda: "wait_until" in deleted, 1)),
        ):
            widget = QW.QWidget(win)
            widget.destroyed.connect(lambda _obj=None, name=name: deleted.append(name))
            widget.deleteLater()
            wait()
            assert name in deleted


def test_caption_moves_above_a_window_covering_it() -> None:
    """The caption moves to the top of the main window while a window covers it"""
    with datalab_test_app_context(console=False) as win:
        with ShowcaseContext(win, 0.01) as ctx:
            ctx.say("Caption", hold=0.0)
            caption = ctx.caption_banner
            assert caption is not None and caption.isVisible()
            assert not caption.moved
            bottom = caption.geometry()
            dialog = QW.QDialog(win)
            dialog.setGeometry(
                QC.QRect(win.mapToGlobal(bottom.topLeft()), bottom.size())
            )
            dialog.show()
            try:
                ctx.pause(60.0)  # 0.6 s: the guard places the caption
                assert caption.placement == (caption.top_limit(), None, None)
                assert caption.geometry().bottom() < bottom.top()
                ctx.say("Next caption", hold=0.0)
                assert caption.moved
            finally:
                dialog.close()
            ctx.pause(60.0)
            assert not caption.moved
            assert caption.geometry() == bottom


def test_caption_is_narrowed_beside_a_tall_window() -> None:
    """Beside a window covering the main window from top to bottom, the caption is
    narrowed, on the side with the most room"""
    with datalab_test_app_context(console=False) as win:
        win.resize(1400, 900)
        with ShowcaseContext(win, 0.01) as ctx:
            ctx.say("A caption long enough to be wrapped once narrowed", hold=0.0)
            caption = ctx.caption_banner
            dialog = QW.QDialog(win)
            dialog.setGeometry(
                QC.QRect(win.mapToGlobal(QC.QPoint(500, 0)), QC.QSize(300, 900))
            )
            dialog.show()
            try:
                ctx.pause(60.0)
                geometry = caption.geometry()
                assert caption.moved and geometry.width() < caption.default_width()
                frame = dialog.frameGeometry()
                frame.moveTopLeft(win.mapFromGlobal(frame.topLeft()))
                assert not frame.intersects(geometry)
                assert geometry.left() > frame.right()  # More room on the right
            finally:
                dialog.close()
            ctx.pause(60.0)
            assert not caption.moved


def test_tall_dialog_is_moved_below_the_caption() -> None:
    """A tall modal dialog covering the caption wherever it goes is moved down,
    when the main window has room for both"""
    with datalab_test_app_context(console=False) as win:
        win.resize(1200, 1000)
        with ShowcaseContext(win, 0.01) as ctx:
            ctx.say("Caption", hold=0.0)
            caption = ctx.caption_banner
            bottom = caption.geometry_at()
            top = caption.geometry_at(caption.top_limit())
            # Covering half of the caption at the top, all of it at the bottom
            dialog_top = top.top() + top.height() // 2
            dialog = QW.QDialog(win)
            dialog.setModal(True)
            dialog.setGeometry(
                QC.QRect(
                    win.mapToGlobal(QC.QPoint(bottom.left(), dialog_top)),
                    QC.QSize(bottom.width(), bottom.bottom() - dialog_top),
                )
            )
            dialog.show()
            try:
                ctx.pause(60.0)
                assert caption.placement == (caption.top_limit(), None, None)
                frame = dialog.frameGeometry()
                frame.moveTopLeft(win.mapFromGlobal(frame.topLeft()))
                assert not frame.intersects(caption.geometry())
                assert frame.bottom() < win.height()
            finally:
                dialog.close()


def test_guard_waits_for_the_demo_mode() -> None:
    """The guard never accepts a dialog before the demo mode closes it, but accepts
    a message box after a delay following the showcase speed"""
    with datalab_test_app_context(console=False) as win:
        dialog = QW.QDialog(win)
        box = QW.QMessageBox(win)
        delay = execenv.delay
        try:
            for speed in (0.7, 1.0, 1.5):
                ctx = ShowcaseContext(win, speed)
                assert ctx.modal_timeout == pytest.approx(max(4.0, 6.0 * speed))
                execenv.delay = int(5000 * speed)
                grace = ctx.GUARD_GRACE * max(speed, 1.0)
                assert ctx.guard_timeout(dialog) == pytest.approx(
                    max(ctx.modal_timeout, 5.0 * speed + grace)
                )
                assert ctx.guard_timeout(box) == pytest.approx(ctx.modal_timeout)
                execenv.delay = 0
                assert ctx.guard_timeout(dialog) == pytest.approx(ctx.modal_timeout)
        finally:
            execenv.delay = delay
            dialog.deleteLater()
            box.deleteLater()
            process_events()


def test_processing_worker_warm_up() -> None:
    """At showcase speed, the processing worker warms up while the first title card
    is shown, so that the first computation of a scenario does not wait for it"""
    with datalab_test_app_context(console=False) as win:
        worker = win.signalpanel.processor.worker
        if worker is None:
            pytest.skip("Process isolation is disabled")
        ShowcaseContext(win, 0.0).start_warm_up()
        assert worker.state_machine.current_state == WorkerState.IDLE
        with ShowcaseContext(win, 0.01) as ctx:
            ctx.start_warm_up()
            assert worker.state_machine.current_state == WorkerState.RUNNING
            ctx.title_card("Title", hold=0.0)
            assert worker.state_machine.current_state == WorkerState.IDLE
        # The worker is ready for the computations of the scenarios
        win.signalpanel.new_object()
        win.signalpanel.processor.run_feature("absolute")
        assert len(win.signalpanel) == 2


def _wait(seconds: float) -> None:
    """Process events during a duration (s), as the main event loop would do"""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        process_events()
        time.sleep(0.01)


def _scenario(run: Callable[[ShowcaseContext], None] | None = None) -> ShowcaseScenario:
    """Return a scenario for the tests of the operator controls"""
    return ShowcaseScenario("test", "Test", run or (lambda _ctx: None))


def test_pause_is_requested_then_immediate() -> None:
    """F9 requests a pause, taking effect at the next pause point; F9 again pauses
    now, at any checkpoint, without consuming the timeout of the waits"""
    with datalab_test_app_context(console=False) as win:
        with ShowcaseContext(win, 0.01) as ctx:
            ctx.begin_scenario(_scenario())
            ctx.toggle_pause()
            assert ctx.paused and not ctx.pause_effective
            # A requested pause does not stop a checkpoint
            start = time.monotonic()
            assert not ctx.wait_until(lambda: False, 0.1)
            assert time.monotonic() - start < 0.4
            ctx.toggle_pause()
            assert ctx.pause_effective
            QC.QTimer.singleShot(400, ctx.toggle_pause)
            start = time.monotonic()
            assert not ctx.wait_until(lambda: False, 0.1)
            assert time.monotonic() - start >= 0.45
            assert not ctx.paused and not ctx.pause_effective
            ctx.end_scenario()


def test_operator_interrupts_the_demos() -> None:
    """Restart, next demo and stop now interrupt the scenario at its next
    checkpoint: its cleanup is played instantly"""
    played: list[str] = []

    def first(ctx: ShowcaseContext) -> None:
        played.append("first")
        restart = played.count("first") == 1
        QC.QTimer.singleShot(50, ctx.restart_demo if restart else ctx.next_demo)
        try:
            ctx.pause(1000.0)  # 10 s, unless interrupted
            played.append("not interrupted")
        finally:
            start = time.monotonic()
            ctx.pause(1000.0)
            ctx.say("Cleanup")
            played.append("cleanup" if time.monotonic() - start < 1.0 else "slow")

    def second(ctx: ShowcaseContext) -> None:
        played.append("second")
        ctx.request_stop()
        assert ctx.stop_requested and ctx.interruption is None
        QC.QTimer.singleShot(50, ctx.request_stop)
        ctx.pause(1000.0)
        played.append("not stopped")

    scenarios = [
        ShowcaseScenario("first", "First", first),
        ShowcaseScenario("second", "Second", second),
    ]
    start = time.monotonic()
    with datalab_test_app_context(console=False) as win:
        options = ShowcaseOptions(loop=True, speed=0.01)
        results = ShowcasePlayer(win, scenarios, options).play()
    assert time.monotonic() - start < 30.0
    assert [(r.scenario_id, r.status, r.message) for r in results] == [
        ("first", "interrupted", RESTART_DEMO),
        ("first", "interrupted", NEXT_DEMO),
        ("second", "interrupted", STOP_NOW),
    ]
    assert played == ["first", "cleanup", "first", "cleanup", "second"]


def test_stop_can_be_cancelled() -> None:
    """A stop after the demo can be cancelled, but not a stop now"""
    with datalab_test_app_context(console=False) as win:
        with ShowcaseContext(win, 0.01) as ctx:
            ctx.begin_scenario(_scenario())
            ctx.toggle_pause()
            ctx.request_stop()
            assert ctx.stop_requested and not ctx.paused
            ctx.cancel_stop()
            assert not ctx.stop_requested
            ctx.request_stop()
            ctx.request_stop()
            ctx.cancel_stop()
            assert ctx.stop_requested and ctx.interruption == STOP_NOW
            with pytest.raises(ShowcaseInterrupted):
                ctx.pause(1.0)
            assert ctx.unwinding
            assert ctx.end_scenario() == STOP_NOW


def test_live_pace_and_next_step() -> None:
    """The pace changes live, and the next step skips the current wait, then
    fast-forwards to the next caption (pausing there, if paused)"""
    with datalab_test_app_context(console=False) as win:
        ShowcaseContext(win, 0.0).change_pace(faster=True)  # Nothing in check mode
        with ShowcaseContext(win, 1.0) as ctx:
            ctx.change_pace(faster=True)
            assert ctx.speed == 0.7
            for _index in range(5):
                ctx.change_pace(faster=True)
            assert ctx.speed == ctx.PACE_FACTORS[-1]
            ctx.change_pace(faster=False)
            assert ctx.speed == 0.7
            ctx.begin_scenario(_scenario())
            QC.QTimer.singleShot(100, ctx.next_step)
            start = time.monotonic()
            ctx.pause(30.0)
            assert time.monotonic() - start < 5.0
            # Fast-forward to the next caption
            start = time.monotonic()
            ctx.pause(2.0)
            assert time.monotonic() - start < 1.0
            ctx.say("Step", hold=0.0)
            start = time.monotonic()
            ctx.pause(0.5)
            assert time.monotonic() - start >= 0.3
            # While paused: pause again at the next caption
            ctx.toggle_pause()
            ctx.toggle_pause()
            QC.QTimer.singleShot(100, ctx.next_step)
            QC.QTimer.singleShot(700, ctx.toggle_pause)
            step = ctx.step
            start = time.monotonic()
            ctx.pause(0.0)
            ctx.say("Next step", hold=0.0)
            assert time.monotonic() - start >= 0.6
            assert ctx.step == step + 1 and not ctx.paused
            ctx.end_scenario()


def test_demo_mode_does_not_close_dialogs_while_paused() -> None:
    """While paused, the dialogs closed by the demo mode of DataLab stay open"""
    original = qthelpers.close_dialog_and_quit
    with datalab_test_app_context(console=False) as win:
        dialog = QW.QDialog(win)
        try:
            with ShowcaseContext(win, 0.01) as ctx:
                assert qthelpers.close_dialog_and_quit is not original
                dialog.show()
                ctx.toggle_pause()
                ctx.toggle_pause()
                qthelpers.close_dialog_and_quit(dialog)
                _wait(0.4)
                assert dialog.isVisible()
                ctx.toggle_pause()
                _wait(0.4)
                assert not dialog.isVisible()
            assert qthelpers.close_dialog_and_quit is original
        finally:
            dialog.deleteLater()
            process_events()


@pytest.mark.parametrize("controls", [True, False])
def test_control_bar(controls: bool) -> None:
    """The control bar shows the state and the progress of the showcase, unless
    disabled"""
    with datalab_test_app_context(console=False) as win:
        with ShowcaseContext(win, 1.0, controls=controls) as ctx:
            ctx.playlist_position, ctx.playlist_size = 2, 3
            ctx.begin_scenario(_scenario())
            ctx.show_controls()
            bar = ctx.control_bar
            if not controls:
                assert bar is None
                return
            assert bar is not None and bar.isVisible()
            assert "Test" in bar.progress_label.text()
            assert bar.dots_label.text() == "○ ● ○"
            assert bar.pace_label.text() == "×1"
            assert not bar.cancel_stop_button.isVisible()
            bar.faster_button.click()
            assert ctx.speed == 0.7 and bar.pace_label.text() == "×1.4"
            bar.pause_button.click()
            assert ctx.paused and bar.pause_button.property("active")
            bar.stop_button.click()
            assert ctx.stop_requested and not ctx.paused
            assert bar.cancel_stop_button.isVisible()
            bar.cancel_stop_button.click()
            assert not ctx.stop_requested
            assert not bar.cancel_stop_button.isVisible()
            ctx.end_scenario()
        assert not bar.isVisible()
