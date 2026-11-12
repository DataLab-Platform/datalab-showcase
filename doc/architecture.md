# Architecture

`datalab_showcase` uses inward-facing dependencies:

```text
adapters -> showcase -> core
```

- `core` owns host-independent behavior and imports neither DataLab nor Qt: the command-line options of the showcase (`core/commandline.py`) and its settings file (`core/settings.py`).
- `showcase` drives the user interface of DataLab: the engine (`engine.py`: captions, title cards, spotlights, mouse pointer, menu walks, modal-dialog guard, hotkeys), the player (`player.py`), the **Showcase mode** dialog (`dialog.py`), the native demos (`scenarios/`), the demos generated for the application plugins (`applications.py`, `applications_plan.py`), the DataLab Web interlude (`scenarios/web_interlude.py`) and the start from the command line (`startup.py`). It must not import the adapters, nor any test suite.
- `adapters/desktop.py` defines the DataLab plugin class, `ShowcasePlugin`: DataLab loads it from the project folder, and the installed entry point targets it. The plugin declares no capability: it is not listed in the Applications panel.
- `i18n.py` gives the translation function of the plugin (`_`, own catalog, read as a package resource since DataLab runs a plugin installed from a file from its wheel, a ZIP archive on `sys.path`) and `datalab_text` (catalog of DataLab, for the texts of DataLab searched by the showcase).
- `app.py` is the `datalab-showcase` command.

The package root exposes identity metadata without importing DataLab, Qt or a host adapter. `tests/unit/test_architecture.py` checks these boundaries as the project grows.

## Start from the command line

DataLab registers its plugins while it builds its main window, before showing it, before its startup actions (`execute_post_show_actions`, which may ask questions) and before its event loop. When the command line requests the showcase, the plugin (`startup.DeferredStart`):

1. sets `execenv.do_not_quit` (SigimaX then skips the question about the log files of a previous session),
2. polls with a timer until the event loop runs (`QThread.loopLevel() > 0`, with PyQt5 and PyQt6), the main window is visible, and no modal dialog nor popup is shown,
3. restores `execenv.do_not_quit`, then plays the showcase.

The showcase is started this way once per process, and not when the plugins are reloaded. DataLab ignores the options it does not know (`parse_known_args`), but takes a separated value as an HDF5 file to open: the plugin only reads the `--option=value` form.

## Internal DataLab APIs

The showcase drives DataLab like an end-to-end test: besides the public plugin API, it uses the main window, the data panels, their processors and action handlers, the history panel, the Applications panel (`application_pages`, `recipe_rows`, `outcome_label`), the instrument windows, the tour cover, the capsule dialog and the processing preview dialog of DataLab 1.4. This is why the plugin requires `datalab-platform >= 1.4.1, < 1.5`.
