# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Translations
============

The plugin has its own translation catalog (``datalab_showcase`` domain, compiled
in the ``locale`` folder of the package): the captions and the user interface of
the showcase follow the language of DataLab, which is selected by the usual
environment variables (``LANGUAGE``, ``LC_ALL``, ``LC_MESSAGES`` and ``LANG``,
see :func:`get_languages`). Without any of them, DataLab sets ``LANG`` from the
system language when it starts, before loading its plugins.

The catalog is read as a resource of the package (:mod:`importlib.resources`),
not from a folder: DataLab runs a plugin installed from a file directly from its
wheel (a ZIP archive on ``sys.path``), where :mod:`gettext` cannot find it.

The texts of the DataLab user interface (e.g. the text of an action searched in a
menu) are translated with the catalog of DataLab instead, see
:func:`datalab_text`.
"""

from __future__ import annotations

import gettext
import io
import locale
import os
import struct
import warnings
from importlib import resources

#: Translation domain of the plugin (name of its catalog)
DOMAIN = "datalab_showcase"
#: Package holding the ``locale`` folder
PACKAGE = "datalab_showcase"
#: Environment variables selecting the language, by order of precedence (as
#: :func:`gettext.find`)
LANGUAGE_VARIABLES = ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")


def get_languages() -> list[str]:
    """Return the languages whose catalog is searched, by order of preference

    The rules of :func:`gettext.find` apply: the first environment variable set
    among ``LANGUAGE``, ``LC_ALL``, ``LC_MESSAGES`` and ``LANG`` gives a list of
    languages separated by colons, the ``C`` (or ``POSIX``) language ends the list
    (no translation). Each language is searched with its territory (e.g.
    ``fr_FR``), then without it (``fr``).

    Returns:
        Language codes (e.g. ``['fr_FR', 'fr']``)
    """
    value = next(
        (os.environ[name] for name in LANGUAGE_VARIABLES if os.environ.get(name)),
        "",
    )
    languages: list[str] = []
    for language in value.split(":"):
        if not language:
            continue
        code = locale.normalize(language).split("@")[0].split(".")[0]
        if code in ("C", "POSIX"):
            break
        for candidate in (code, code.split("_")[0]):
            if candidate not in languages:
                languages.append(candidate)
    return languages


def load_translations(package: str = PACKAGE) -> gettext.NullTranslations:
    """Load the catalog of the plugin for the current language

    Args:
        package: Package holding the ``locale`` folder

    Returns:
        Translations (English, i.e. untranslated texts, without catalog for the
         current language, or if the catalog cannot be read)
    """
    folder = resources.files(package) / "locale"
    for language in get_languages():
        resource = folder / language / "LC_MESSAGES" / f"{DOMAIN}.mo"
        try:
            if not resource.is_file():
                continue
            return gettext.GNUTranslations(io.BytesIO(resource.read_bytes()))
        except (OSError, struct.error, ValueError, LookupError) as exc:
            # A translation problem never prevents the plugin from loading
            warnings.warn(
                f"Unable to load the {DOMAIN!r} translations ({language}, "
                f"{type(exc).__name__}: {exc}): falling back to English",
                RuntimeWarning,
                stacklevel=2,
            )
            break
    return gettext.NullTranslations()


_ = load_translations().gettext


def datalab_text(text: str) -> str:
    """Translate a text of the DataLab user interface, with the catalog of DataLab

    The showcase finds some actions and widgets of DataLab from their text: this
    text must be translated as DataLab translates it.

    Args:
        text: Text of the DataLab user interface, in English

    Returns:
        Text translated in the language of DataLab
    """
    # pylint: disable=import-outside-toplevel
    from datalab.config import _ as datalab_translate

    return datalab_translate(text)


__all__ = [
    "DOMAIN",
    "_",
    "datalab_text",
    "get_languages",
    "load_translations",
]
