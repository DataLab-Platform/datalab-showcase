# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
DataLab Showcase
================

Showcase mode for DataLab: live and unattended demos of DataLab features, for
exhibitions, conference booths and demonstrations.

The package root only gives the identity of the plugin: it imports neither
DataLab nor Qt. The plugin class is
:class:`~datalab_showcase.adapters.desktop.ShowcasePlugin`.
"""

PLUGIN_DESCRIPTION = (
    "Showcase mode: live and unattended demos of DataLab for exhibitions"
)
PLUGIN_ID = "org.datalab.showcase"
PLUGIN_NAME = "DataLab Showcase"
__version__ = "0.1.0"

__all__ = [
    "PLUGIN_DESCRIPTION",
    "PLUGIN_ID",
    "PLUGIN_NAME",
    "__version__",
]
