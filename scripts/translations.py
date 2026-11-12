# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""
Translations of the plugin
==========================

Update the translation catalogs (``.po`` files) from the sources, or compile them
(``.mo`` files, built into the wheel but not tracked by git). Requires Babel
(``pip install babel``, or the ``test`` extra of the project)::

    python scripts/translations.py scan
    python scripts/translations.py compile

The ``.po`` files are in ``src/datalab_showcase/locale/<language>/LC_MESSAGES``.
The strings of the user interface of DataLab, found by the showcase from their
text (``datalab_text``), are translated with the catalog of DataLab: they are not
extracted.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "datalab_showcase"
LOCALE_DIR = ROOT / "src" / DOMAIN / "locale"
LANGUAGES = ("fr",)
PYBABEL = [sys.executable, "-m", "babel.messages.frontend"]
#: Volatile header lines removed from the catalogs (no merge conflicts)
VOLATILE_HEADERS = (
    "Project-Id-Version",
    "Report-Msgid-Bugs-To",
    "POT-Creation-Date",
    "PO-Revision-Date",
    "Last-Translator",
    "Language-Team",
    "Generated-By",
)


def _remove_volatile_headers(path: Path) -> None:
    """Remove the volatile header lines of a catalog"""
    content = path.read_text(encoding="utf-8")
    for header in VOLATILE_HEADERS:
        content = re.sub(rf'"{header}:[^"]*\\n"\n', "", content)
    path.write_text(content, encoding="utf-8", newline="\n")


def scan() -> None:
    """Extract the translatable strings, then update the catalogs"""
    template = LOCALE_DIR / f"{DOMAIN}.pot"
    LOCALE_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        PYBABEL
        + [
            "extract",
            "--mapping-file",
            str(ROOT / "babel.cfg"),
            "--output-file",
            str(template),
            "--no-location",
            "--no-wrap",
            "--sort-by-file",
            "--project",
            DOMAIN,
            "--copyright-holder",
            "DataLab Platform Developers",
            "src",
        ],
        check=True,
        cwd=ROOT,
    )
    _remove_volatile_headers(template)
    for language in LANGUAGES:
        subprocess.run(
            PYBABEL
            + [
                "update",
                "--input-file",
                str(template),
                "--output-dir",
                str(LOCALE_DIR),
                "--locale",
                language,
                "--domain",
                DOMAIN,
                "--ignore-obsolete",
                "--init-missing",
                "--no-wrap",
                "--ignore-pot-creation-date",
            ],
            check=True,
            cwd=ROOT,
        )
        catalog = LOCALE_DIR / language / "LC_MESSAGES" / f"{DOMAIN}.po"
        _remove_volatile_headers(catalog)


def compile_catalogs() -> list[Path]:
    """Compile the catalogs into ``.mo`` files

    Returns:
        Paths of the compiled files
    """
    # pylint: disable=import-outside-toplevel
    from babel.messages.mofile import write_mo
    from babel.messages.pofile import read_po

    compiled = []
    for po_path in sorted(LOCALE_DIR.glob(f"*/LC_MESSAGES/{DOMAIN}.po")):
        with po_path.open("rb") as file:
            catalog = read_po(file, domain=DOMAIN)
        messages = [message for message in catalog if message.id]
        translated = [message for message in messages if message.string]
        mo_path = po_path.with_suffix(".mo")
        with mo_path.open("wb") as file:
            write_mo(file, catalog)
        print(
            f"{mo_path.relative_to(ROOT)}: {len(translated)} of {len(messages)} "
            "messages translated"
        )
        compiled.append(mo_path)
    if not compiled:
        raise SystemExit(f"No catalog found in {LOCALE_DIR}")
    return compiled


def main() -> None:
    """Run the command given on the command line"""
    parser = argparse.ArgumentParser(description="Scan or compile the translations")
    parser.add_argument("command", choices=("scan", "compile"))
    args = parser.parse_args()
    if args.command == "scan":
        scan()
    else:
        compile_catalogs()


if __name__ == "__main__":
    main()
