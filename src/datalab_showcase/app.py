# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
``datalab-showcase`` command
============================

The ``datalab-showcase`` command (installed with the Python package) starts
DataLab and plays all the demos in a loop, in full screen: it is equivalent to
``datalab --showcase --showcase-loop --showcase-fullscreen``. It accepts the
command-line options of DataLab and of the showcase, e.g.
``datalab-showcase --showcase=d1,d3 --showcase-screen=1``.
"""

from __future__ import annotations

import sys

from datalab_showcase.core.commandline import complete_kiosk_arguments


def run() -> None:
    """Start DataLab, then play the showcase in a loop, in full screen

    The ``--showcase=all``, ``--showcase-loop`` and ``--showcase-fullscreen``
    options are added to the command line, unless already given: the plugin reads
    them once DataLab registers it.
    """
    sys.argv[1:] = complete_kiosk_arguments(sys.argv[1:])
    # pylint: disable=import-outside-toplevel
    from datalab.app import run as run_datalab

    run_datalab()


if __name__ == "__main__":
    run()
