# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""The ``datalab-showcase`` command."""

from __future__ import annotations

import sys

import datalab.app
import pytest

from datalab_showcase import app


@pytest.mark.parametrize(
    "arguments, expected",
    [
        ([], ["--showcase=all", "--showcase-loop", "--showcase-fullscreen"]),
        (
            ["--showcase=d1,d3", "--showcase-screen=1"],
            [
                "--showcase=d1,d3",
                "--showcase-screen=1",
                "--showcase-loop",
                "--showcase-fullscreen",
            ],
        ),
    ],
)
def test_kiosk_command(
    arguments: list[str], expected: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The command runs DataLab, playing the demos in a loop, in full screen"""
    calls: list[list[str]] = []
    monkeypatch.setattr(datalab.app, "run", lambda: calls.append(sys.argv[1:]))
    monkeypatch.setattr(sys, "argv", ["datalab-showcase", *arguments])
    app.run()
    assert calls == [expected]
