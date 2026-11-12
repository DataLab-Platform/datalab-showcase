# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Command-line options of the showcase
====================================

The plugin reads its options on the command line of DataLab itself, e.g.
``DataLab.exe --showcase --showcase-loop --showcase-fullscreen``:

- ``--showcase``: play all the demos, ``--showcase=d1,d3``: play the given demos
- ``--showcase-loop``: play the demos in a loop
- ``--showcase-speed=0.7``: delay factor (1: normal pace, slower above, faster
  below)
- ``--showcase-screen=1``: index of the screen showing the showcase (0: first
  screen)
- ``--showcase-fullscreen``: show DataLab in full screen
- ``--showcase-web``, ``--showcase-web=URL``: end each loop with one pass of the
  DataLab Web showcase, in a browser window

.. warning::

    A value must be given with ``=`` (``--showcase=d1``, not ``--showcase d1``).
    DataLab ignores the options it does not know (``parse_known_args``), but it
    takes the first argument which is not an option as an HDF5 file to open: with
    ``--showcase d1``, DataLab tries to open a file named ``d1`` and shows an error
    message, which delays the showcase until it is closed. Such a separated value
    is never used by the showcase, which warns about it.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

#: Option starting the showcase (all the demos, or ``--showcase=IDS``)
SHOWCASE_OPTION = "--showcase"
#: Option playing the demos in a loop
LOOP_OPTION = "--showcase-loop"
#: Option setting the delay factor (``--showcase-speed=0.7``)
SPEED_OPTION = "--showcase-speed"
#: Option setting the index of the screen showing the showcase
SCREEN_OPTION = "--showcase-screen"
#: Option showing DataLab in full screen
FULLSCREEN_OPTION = "--showcase-fullscreen"
#: Option ending each loop with the DataLab Web interlude (``--showcase-web=URL``)
WEB_OPTION = "--showcase-web"

#: Options without value
FLAG_OPTIONS = (LOOP_OPTION, FULLSCREEN_OPTION)
#: Options requiring a value
VALUE_OPTIONS = (SPEED_OPTION, SCREEN_OPTION)
#: Options with an optional value
OPTIONAL_VALUE_OPTIONS = (SHOWCASE_OPTION, WEB_OPTION)
#: All the options of the showcase
OPTIONS = (SHOWCASE_OPTION, *FLAG_OPTIONS, *VALUE_OPTIONS, WEB_OPTION)

#: Host page of the DataLab Web showcase, played by the DataLab Web interlude when
#: no other URL is given
DEFAULT_WEB_URL = "https://datalab-platform.com/web-showcase/"


@dataclass(frozen=True)
class ShowcaseRequest:
    """Showcase requested on the command line

    Args:
        scenarios: Comma-separated IDs of the demos to play, or ``'all'``
        loop: True to play the demos in a loop
        speed: Delay factor (None: normal pace)
        screen: Index of the screen showing the showcase (None: current screen)
        fullscreen: True to show DataLab in full screen
        web_url: URL of the DataLab Web showcase, to end each loop with it (None:
         no DataLab Web interlude)
    """

    scenarios: str = "all"
    loop: bool = False
    speed: float | None = None
    screen: int | None = None
    fullscreen: bool = False
    web_url: str | None = None


@dataclass
class ParsedArguments:
    """Showcase options found on a command line

    Args:
        request: Showcase requested (None: no ``--showcase`` option)
        warnings: Messages about the options which are ignored
    """

    request: ShowcaseRequest | None = None
    warnings: list[str] = field(default_factory=list)


def _split(argument: str) -> tuple[str, str | None]:
    """Split an argument into its option name and its value (None: no ``=``)"""
    name, sep, value = argument.partition("=")
    return name, (value if sep else None)


def is_showcase_argument(argument: str) -> bool:
    """Return True if an argument is a showcase option (valid or not)

    Args:
        argument: Command-line argument

    Returns:
        True for ``--showcase`` and the arguments starting with ``--showcase-`` or
         ``--showcase=``
    """
    name, _value = _split(argument)
    return name == SHOWCASE_OPTION or name.startswith(SHOWCASE_OPTION + "-")


def _separated_value(arguments: Sequence[str], index: int) -> str | None:
    """Return the argument following an option, if it looks like a value"""
    if index + 1 < len(arguments):
        following = arguments[index + 1]
        if following and not following.startswith("-"):
            return following
    return None


def parse_arguments(arguments: Sequence[str]) -> ParsedArguments:
    """Parse the showcase options of a command line

    Only the ``--option=value`` form gives a value to an option: a separated value
    (``--showcase d1``) is ignored with a warning, as DataLab takes it as a file to
    open. Invalid values are ignored with a warning too. The other arguments
    (DataLab options, files) are ignored, as well as the arguments following
    ``--``.

    Args:
        arguments: Command-line arguments, without the program name (e.g.
         ``sys.argv[1:]``)

    Returns:
        Showcase request (None without ``--showcase`` option) and warnings
    """
    result = ParsedArguments()
    found = False
    values: dict[str, object] = {}
    for index, argument in enumerate(arguments):
        if argument == "--":
            break
        if not is_showcase_argument(argument):
            continue
        name, value = _split(argument)
        separated = _separated_value(arguments, index) if value is None else None
        if name not in OPTIONS:
            result.warnings.append(f"Unknown showcase option ignored: {argument}")
        elif name in FLAG_OPTIONS:
            if value is not None:
                result.warnings.append(
                    f"{name} takes no value: {argument} is ignored (write {name})"
                )
            else:
                values[name] = True
        elif name in VALUE_OPTIONS:
            if value is None:
                example = separated if separated is not None else "VALUE"
                result.warnings.append(
                    f"{name} requires a value, given with '=' (e.g. "
                    f"{name}={example}): option ignored"
                )
            else:
                parsed = _parse_number(name, value)
                if parsed is None:
                    result.warnings.append(f"Invalid value ignored: {argument}")
                else:
                    values[name] = parsed
        else:
            if name == SHOWCASE_OPTION:
                found = True
            values[name] = value.strip() if value is not None else ""
            if separated is not None:
                result.warnings.append(
                    f"{separated!r} is not a value of {name}: write "
                    f"{name}={separated} (DataLab takes a separated value as a "
                    "file to open)"
                )
    if not found:
        if values:
            result.warnings.append(
                f"Showcase options ignored without the {SHOWCASE_OPTION} option"
            )
        return result
    web_url = values.get(WEB_OPTION)
    result.request = ShowcaseRequest(
        scenarios=str(values[SHOWCASE_OPTION]) or "all",
        loop=bool(values.get(LOOP_OPTION, False)),
        speed=values.get(SPEED_OPTION),
        screen=values.get(SCREEN_OPTION),
        fullscreen=bool(values.get(FULLSCREEN_OPTION, False)),
        web_url=None if web_url is None else (str(web_url) or DEFAULT_WEB_URL),
    )
    return result


def _parse_number(name: str, value: str) -> float | int | None:
    """Parse the value of the speed (float >= 0) or of the screen (int >= 0)

    Args:
        name: Option name
        value: Option value

    Returns:
        Parsed value, or None if it is invalid
    """
    try:
        number = float(value) if name == SPEED_OPTION else int(value)
    except ValueError:
        return None
    if number < 0 or not math.isfinite(number):
        return None
    return number


def has_showcase_option(arguments: Sequence[str]) -> bool:
    """Return True if a command line requests the showcase (``--showcase`` option)

    Args:
        arguments: Command-line arguments, without the program name

    Returns:
        True if the ``--showcase`` option is given (with or without value)
    """
    return parse_arguments(arguments).request is not None


def complete_kiosk_arguments(arguments: Sequence[str]) -> list[str]:
    """Return the arguments of the ``datalab-showcase`` command, for DataLab

    The command plays all the demos in a loop, in full screen: the
    ``--showcase=all``, ``--showcase-loop`` and ``--showcase-fullscreen`` options
    are added, unless already given (``--showcase=d1,d3`` selects the demos).

    Args:
        arguments: Command-line arguments, without the program name

    Returns:
        Completed arguments
    """
    arguments = list(arguments)
    # The arguments following "--" are not options
    end = arguments.index("--") if "--" in arguments else len(arguments)
    names = {_split(argument)[0] for argument in arguments[:end]}
    added = [] if SHOWCASE_OPTION in names else [SHOWCASE_OPTION + "=all"]
    added += [opt for opt in (LOOP_OPTION, FULLSCREEN_OPTION) if opt not in names]
    return arguments[:end] + added + arguments[end:]


__all__ = [
    "DEFAULT_WEB_URL",
    "OPTIONS",
    "ParsedArguments",
    "ShowcaseRequest",
    "complete_kiosk_arguments",
    "has_showcase_option",
    "is_showcase_argument",
    "parse_arguments",
]
