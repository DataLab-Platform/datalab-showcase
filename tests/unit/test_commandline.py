# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""Command-line options of the showcase (host independent)."""

from __future__ import annotations

import pytest

from datalab_showcase.core.commandline import (
    DEFAULT_WEB_URL,
    ShowcaseRequest,
    complete_kiosk_arguments,
    has_showcase_option,
    is_showcase_argument,
    parse_arguments,
)


def test_all_options_with_equal_sign() -> None:
    """Each option is parsed in its ``--option=value`` form"""
    parsed = parse_arguments(
        [
            "workspace.h5",
            "--showcase=d1,d3",
            "--showcase-loop",
            "--showcase-speed=0.7",
            "--showcase-screen=1",
            "--showcase-fullscreen",
            "--showcase-web=http://localhost:5173/",
            "--unattended",
        ]
    )
    assert parsed.warnings == []
    assert parsed.request == ShowcaseRequest(
        scenarios="d1,d3",
        loop=True,
        speed=0.7,
        screen=1,
        fullscreen=True,
        web_url="http://localhost:5173/",
    )


def test_defaults() -> None:
    """``--showcase`` alone plays all the demos once, at normal pace"""
    assert parse_arguments(["--showcase"]).request == ShowcaseRequest()
    assert parse_arguments(["--showcase="]).request == ShowcaseRequest()
    assert parse_arguments(["--showcase=all"]).request == ShowcaseRequest()
    request = parse_arguments(["--showcase", "--showcase-web"]).request
    assert request.web_url == DEFAULT_WEB_URL
    assert DEFAULT_WEB_URL == "https://datalab-platform.com/web-showcase/"


def test_no_showcase_without_showcase_option() -> None:
    """Without ``--showcase``, nothing is played: other options are ignored"""
    parsed = parse_arguments(["file.h5", "--unattended"])
    assert parsed.request is None and parsed.warnings == []
    parsed = parse_arguments(["--showcase-loop", "--showcase-speed=2"])
    assert parsed.request is None
    assert len(parsed.warnings) == 1 and "--showcase" in parsed.warnings[0]
    assert not has_showcase_option(["--showcase-loop"])
    assert has_showcase_option(["--showcase=d2"])


def test_separated_value_is_ignored_with_a_warning() -> None:
    """``--showcase d1``: DataLab takes ``d1`` as a file to open, the showcase
    ignores it (all the demos are played) and tells how to write the option"""
    parsed = parse_arguments(["--showcase", "d1"])
    assert parsed.request == ShowcaseRequest(scenarios="all")
    assert len(parsed.warnings) == 1
    assert "--showcase=d1" in parsed.warnings[0]
    parsed = parse_arguments(["--showcase", "--showcase-web", "http://host/"])
    assert parsed.request.web_url == DEFAULT_WEB_URL
    assert "--showcase-web=http://host/" in parsed.warnings[0]


@pytest.mark.parametrize("option", ["--showcase-speed", "--showcase-screen"])
def test_value_options_require_an_equal_sign(option: str) -> None:
    """A value option without ``=`` is ignored, with a warning"""
    parsed = parse_arguments(["--showcase", option, "1"])
    assert parsed.request == ShowcaseRequest()
    assert len(parsed.warnings) == 1
    assert f"{option}=1" in parsed.warnings[0]


@pytest.mark.parametrize(
    "argument",
    [
        "--showcase-speed=fast",
        "--showcase-speed=-1",
        "--showcase-speed=nan",
        "--showcase-screen=1.5",
        "--showcase-screen=-2",
        "--showcase-loop=yes",
        "--showcase-fullscreen=0",
        "--showcase-unknown",
    ],
)
def test_invalid_options_are_ignored(argument: str) -> None:
    """Invalid values, values given to flags and unknown options are ignored"""
    parsed = parse_arguments(["--showcase", argument])
    assert parsed.request == ShowcaseRequest()
    assert len(parsed.warnings) == 1 and argument.split("=")[0] in parsed.warnings[0]


def test_arguments_after_double_dash_are_not_options() -> None:
    """The arguments following ``--`` are not options"""
    assert parse_arguments(["--", "--showcase"]).request is None


def test_showcase_arguments() -> None:
    """The showcase options are recognized, valid or not"""
    assert is_showcase_argument("--showcase")
    assert is_showcase_argument("--showcase=d1")
    assert is_showcase_argument("--showcase-anything")
    assert not is_showcase_argument("--showcases")
    assert not is_showcase_argument("showcase")


def test_kiosk_arguments() -> None:
    """The ``datalab-showcase`` command plays all the demos in a loop, in full
    screen, unless other options are given"""
    assert complete_kiosk_arguments([]) == [
        "--showcase=all",
        "--showcase-loop",
        "--showcase-fullscreen",
    ]
    assert complete_kiosk_arguments(["--showcase=d1", "--showcase-loop"]) == [
        "--showcase=d1",
        "--showcase-loop",
        "--showcase-fullscreen",
    ]
    assert complete_kiosk_arguments(["file.h5", "--", "--x"]) == [
        "file.h5",
        "--showcase=all",
        "--showcase-loop",
        "--showcase-fullscreen",
        "--",
        "--x",
    ]
    request = parse_arguments(complete_kiosk_arguments([])).request
    assert request == ShowcaseRequest(loop=True, fullscreen=True)
