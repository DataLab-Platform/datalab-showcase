# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""Translations of the plugin: catalog, loading and DataLab texts."""

from __future__ import annotations

import ast
import gettext
import io
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from babel.messages import checkers
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

from datalab_showcase.i18n import (
    DOMAIN,
    LANGUAGE_VARIABLES,
    get_languages,
    load_translations,
)

PACKAGE_ROOT = Path(__file__).parents[2] / "src" / "datalab_showcase"
LOCALE_DIR = PACKAGE_ROOT / "locale"
CATALOGS = sorted(LOCALE_DIR.glob(f"*/LC_MESSAGES/{DOMAIN}.po"))
#: Package of the ZIP archive built by the tests
ZIPPED_PACKAGE = "zipped_showcase_catalog"


def read_catalog(path: Path):
    """Read a translation catalog"""
    with path.open("rb") as file:
        return read_po(file, domain=DOMAIN)


def compile_catalog(path: Path) -> bytes:
    """Compile a translation catalog, and return the content of its ``.mo`` file"""
    buffer = io.BytesIO()
    write_mo(buffer, read_catalog(path))
    return buffer.getvalue()


def set_language(monkeypatch: pytest.MonkeyPatch, **variables: str) -> None:
    """Select the language with environment variables (the others are unset)"""
    for name in LANGUAGE_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    for name, value in variables.items():
        monkeypatch.setenv(name, value)


def run_python(code: str, language: str) -> str:
    """Run Python code in a new process, with a language, and return its output"""
    environment = os.environ.copy()
    environment["LANGUAGE"] = language
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(PACKAGE_ROOT.parent), environment.get("PYTHONPATH", "")]
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        env=environment,
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def test_french_catalog_is_complete() -> None:
    """The French catalog translates every message, with consistent placeholders"""
    assert [path.parts[-3] for path in CATALOGS] == ["fr"]
    catalog = read_catalog(CATALOGS[0])
    messages = [message for message in catalog if message.id]
    assert len(messages) > 100
    untranslated = [message.id for message in messages if not message.string]
    assert not untranslated, untranslated
    for message in messages:
        assert not message.fuzzy, message.id
        for checker in (checkers.python_format,):
            checker(catalog, message)


def test_catalog_is_loaded(tmp_path: Path) -> None:
    """The compiled French catalog translates the messages of the plugin"""
    mo_path = tmp_path / "fr" / "LC_MESSAGES" / f"{DOMAIN}.mo"
    mo_path.parent.mkdir(parents=True)
    mo_path.write_bytes(compile_catalog(CATALOGS[0]))
    translation = gettext.translation(DOMAIN, str(tmp_path), languages=["fr"])
    assert translation.gettext("Showcase mode") == "Mode vitrine"
    assert translation.gettext("Step %d") % 2 == "Étape 2"


@pytest.mark.parametrize(
    "variables, expected",
    [
        ({"LANGUAGE": "fr"}, ["fr_FR", "fr"]),
        ({"LANGUAGE": "de:fr_FR.UTF-8"}, ["de_DE", "de", "fr_FR", "fr"]),
        ({"LANGUAGE": "", "LC_ALL": "fr_CA"}, ["fr_CA", "fr"]),
        ({"LC_MESSAGES": "fr_FR@euro", "LANG": "en_US.UTF-8"}, ["fr_FR", "fr"]),
        ({"LANG": "en_US.UTF-8"}, ["en_US", "en"]),
        ({"LANGUAGE": "C:fr"}, []),
        ({"LANG": "POSIX"}, []),
        ({}, []),
    ],
)
def test_languages(
    variables: dict[str, str], expected: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The language is selected by the environment variables, as with gettext"""
    set_language(monkeypatch, **variables)
    assert get_languages() == expected


def test_catalog_is_read_from_a_zip_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DataLab runs a plugin installed from a file from its wheel, a ZIP archive on
    ``sys.path``: the catalog is read from the archive"""
    archive = tmp_path / "plugin.whl"
    catalog = f"{ZIPPED_PACKAGE}/locale/fr/LC_MESSAGES/{DOMAIN}.mo"
    with zipfile.ZipFile(archive, "w") as file:
        file.writestr(f"{ZIPPED_PACKAGE}/__init__.py", "")
        file.writestr(catalog, compile_catalog(CATALOGS[0]))
    monkeypatch.syspath_prepend(str(archive))
    monkeypatch.delitem(sys.modules, ZIPPED_PACKAGE, raising=False)
    try:
        set_language(monkeypatch, LANGUAGE="fr")
        translations = load_translations(ZIPPED_PACKAGE)
        assert translations.gettext("Showcase mode") == "Mode vitrine"
        # No catalog for the language: English
        set_language(monkeypatch, LANG="de_DE.UTF-8")
        translations = load_translations(ZIPPED_PACKAGE)
        assert translations.gettext("Showcase mode") == "Showcase mode"
    finally:
        sys.modules.pop(ZIPPED_PACKAGE, None)


def test_corrupted_catalog_gives_english(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A corrupted catalog is reported, and the texts are left untranslated"""
    package = tmp_path / "corrupted_showcase_catalog"
    mo_path = package / "locale" / "fr" / "LC_MESSAGES" / f"{DOMAIN}.mo"
    mo_path.parent.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    mo_path.write_bytes(b"not a catalog")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.delitem(sys.modules, package.name, raising=False)
    try:
        set_language(monkeypatch, LANGUAGE="fr")
        with pytest.warns(RuntimeWarning, match="falling back to English"):
            translations = load_translations(package.name)
        assert translations.gettext("Showcase mode") == "Showcase mode"
    finally:
        sys.modules.pop(package.name, None)


def test_language_follows_datalab() -> None:
    """The plugin follows the language of DataLab (here, ``LANGUAGE=fr``), with its
    own catalog for its messages, and the catalog of DataLab for DataLab texts"""
    if not (LOCALE_DIR / "fr" / "LC_MESSAGES" / f"{DOMAIN}.mo").is_file():
        pytest.fail(
            "The catalogs are not compiled: "
            "run 'python scripts/translations.py compile'"
        )
    code = (
        "from datalab_showcase.i18n import _, datalab_text; "
        "print(_('Showcase mode')); print(_('Step %d') % 3); "
        "print(datalab_text('Show results'))"
    )
    lines = run_python(code, "fr").splitlines()
    assert lines[:2] == ["Mode vitrine", "Étape 3"]
    datalab_french = lines[2] == "Afficher les résultats"
    assert run_python(code, "en").splitlines() == [
        "Showcase mode",
        "Step 3",
        "Show results",
    ]
    if not datalab_french:
        pytest.skip("The French catalog of DataLab is not compiled")


def _datalab_texts() -> list[str]:
    """Return the DataLab texts used by the plugin (``datalab_text`` calls)"""
    texts = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "datalab_text"
            ):
                (argument,) = node.args
                texts.append(argument.value)
    return texts


def test_datalab_texts_are_translated_by_datalab() -> None:
    """Each DataLab text searched by the showcase is translated by DataLab: the
    showcase finds the same actions in English and in French"""
    texts = _datalab_texts()
    assert "Show results" in texts and len(texts) >= 10
    import datalab  # pylint: disable=import-outside-toplevel

    locale_dir = Path(datalab.__file__).parent / "locale"
    try:
        translation = gettext.translation("datalab", str(locale_dir), ["fr"])
    except OSError:
        pytest.skip("The French catalog of DataLab is not compiled")
    untranslated = [text for text in texts if translation.gettext(text) == text]
    assert not untranslated, untranslated
