# Contributing

## Development environment

The plugin is developed with the sources of DataLab and of its stack (Sigima, SigimaX, DataLab-Capsule, guidata, PlotPy, PythonQwt), cloned side by side, or with the published DataLab:

```bash
python -m pip install -e ".[test]"
```

With the sources of DataLab (whose version may not satisfy the requirement of the plugin before its release), install the plugin without dependencies and put the sources on the Python path:

```powershell
python -m pip install -e . --no-deps
python -m pip install babel build pytest ruff
$env:PYTHONPATH = "C:\Dev\DataLab;C:\Dev\Sigima;C:\Dev\SigimaX;C:\Dev\DataLab-Capsule\src;C:\Dev\guidata;C:\Dev\PlotPy;C:\Dev\PythonQwt;C:\Dev\datalab-showcase\src"
```

To try a change in DataLab, add the project folder in **Plugins > Configure plugins... > Advanced** and reload the plugins: no installation is needed. DataLab also finds the plugin when `src` is on the Python path (package name starting with `datalab_`).

## Checks

Compile the translations first (the tests check the French catalog, and the wheel must contain it), then run the tests and Ruff:

```bash
python scripts/translations.py compile
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

The tests run on the `offscreen` Qt platform (`--show-windows` shows the windows). The plugin tests use the test helpers of DataLab (`datalab.tests`, included in the `datalab-platform` wheel), but the plugin itself must never import a test suite (`datalab.tests`, `pytest`): the standalone DataLab does not include them.

[pre-commit](https://pre-commit.com/) runs Ruff before each commit, once installed with `pre-commit install`.

## Translations

The plugin has its own translation catalog: `src/datalab_showcase/locale/fr/LC_MESSAGES/datalab_showcase.po`. Write the texts of the plugin with `_()` (`from datalab_showcase.i18n import _`), then update the catalog and translate the new messages:

```bash
python scripts/translations.py scan
```

The texts of the user interface of DataLab which the showcase searches (e.g. the text of an action of a menu) are translated with the catalog of DataLab: write them with `datalab_text()` (`from datalab_showcase.i18n import datalab_text`), they are not extracted into the catalog of the plugin.

The compiled catalogs (`.mo` files) are not tracked by git: `python scripts/translations.py compile` builds them, before the tests and before building the wheel (the CI workflows do it).

DataLab runs a plugin installed from a file directly from its wheel (a ZIP archive on `sys.path`): the plugin reads its catalog as a package resource (`importlib.resources`), never from a folder. Read any other file of the package the same way.

## Architecture

Keep host-independent code in `core`, the showcase itself (which drives the user interface of DataLab) in `showcase`, and the plugin class in `adapters`: see [doc/architecture.md](doc/architecture.md). Add focused tests at the same layer as the behavior under test.

The showcase uses some internal widgets of DataLab (e.g. the pages of the Applications panel): check the plugin with each new minor version of DataLab (the **development** job of the **Tests** workflow runs every week with the development version of DataLab).

## Continuous integration

The **Tests** workflow runs Ruff and the tests on each push and pull request, on Linux and Windows with PyQt5 and on Linux with PyQt6. Until DataLab 1.4.1 is published on PyPI, these tests install DataLab from its `release` branch (`DATALAB_BRANCH` variable of the workflow): once it is published, set `DATALAB_BRANCH` to `""` to test the published DataLab. The **development** job tests the `develop` branches of the DataLab stack every week (non-blocking).
