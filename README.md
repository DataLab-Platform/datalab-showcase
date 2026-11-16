# DataLab Showcase

Showcase mode for [DataLab](https://datalab-platform.com/): live and unattended demos of DataLab features, for exhibitions, conference booths and kiosks, where DataLab presents itself on a screen, in a loop.

Each demo drives the real user interface of DataLab, as a user would do: a title card introduces the demo, then captions explain each step while the mouse pointer moves, menus open and the relevant parts of the window are highlighted. The captions follow the language of DataLab (English or French). At the end of the demos, an end card invites the audience to try DataLab.

> **Warning:** the showcase mode clears the workspace (signals, images, macros and history) before each demo.

## Requirements

DataLab 1.4.1 or a later 1.4.x version (`datalab-platform >= 1.4.1, < 1.5`): the showcase drives the user interface of DataLab, including some of its internal widgets, so each minor version of DataLab needs a release of the plugin. The plugin works in the standalone DataLab (`DataLab.exe`, MSI installer) as well as with the Python package.

## Installation

### Standalone DataLab (no Python environment needed)

- From the plugin catalog: **Plugins > Configure plugins...**, **Catalog** tab, then click **Install** next to **DataLab Showcase**.
- From a file: download the wheel (`datalab_showcase-X.Y.Z-py3-none-any.whl`) from the [releases](https://github.com/DataLab-Platform/datalab-showcase/releases) of this repository, then **Plugins > Configure plugins...**, **From file** tab, **Install from file...**.

Then reload the plugins (**Plugins > Reload plugins**) or restart DataLab: the **Plugins** menu gets a **DataLab Showcase** submenu.

### Python package

Install the wheel of a release in the Python environment of DataLab:

```console
python -m pip install datalab_showcase-X.Y.Z-py3-none-any.whl
```

The package also installs the `datalab-showcase` command (see below). If some plugins were disabled in **Plugins > Configure plugins...**, DataLab only loads the plugins enabled there: enable **DataLab Showcase** in the **Installed plugins** tab.

## Playing the showcase

### From the menu

Select **Plugins > DataLab Showcase > Showcase mode...**: a dialog lets you choose:

- the demos to play,
- whether to play them in a loop,
- the pace (slow, normal or fast),
- whether to show DataLab in full screen,
- whether to include DataLab Web, and its URL (see [DataLab Web on the same booth](#datalab-web-on-the-same-booth)),
- the screen showing DataLab, when several screens are available.

These choices are remembered for the next time, in the `showcase.json` file of the DataLab configuration folder (e.g. `C:\Users\<user>\.DataLab_v1\showcase.json` on Windows, `~/.DataLab_v1/showcase.json` on Linux and macOS). The plugin adds no option to the configuration of DataLab: removing the plugin leaves nothing behind but this file. A missing or corrupted file gives the default choices.

### From the command line (kiosk)

The showcase may also be started with command-line options of DataLab, e.g. to start a booth computer directly in showcase mode, with the standalone version of DataLab:

```console
DataLab.exe --showcase --showcase-loop --showcase-fullscreen
```

| Option | Description |
| --- | --- |
| `--showcase` | Play all the demos once DataLab is ready |
| `--showcase=IDS` | Play the demos whose comma-separated identifiers are given (e.g. `--showcase=d1,d3`) |
| `--showcase-loop` | Play the demos in a loop, until the operator stops the showcase |
| `--showcase-speed=SPEED` | Delay factor: 1 by default, slower above (e.g. `1.5`), faster below (e.g. `0.7`) |
| `--showcase-screen=N` | Index of the screen showing DataLab (`0` for the first screen) |
| `--showcase-fullscreen` | Show DataLab in full screen during the showcase |
| `--showcase-web`, `--showcase-web=URL` | End each loop with one pass of the DataLab Web showcase, in a browser window (see [DataLab Web on the same booth](#datalab-web-on-the-same-booth)) |

> **Always give a value with `=`** (`--showcase=d1`, `--showcase-speed=0.7`), never as a separate argument (`--showcase d1`). These options belong to the plugin, not to DataLab: DataLab ignores them, but it takes the first argument which is not an option as an HDF5 file to open. With `--showcase d1`, DataLab tries to open a file named `d1` and shows an error message: the showcase waits until this message is closed, then plays all the demos (it never uses such a separated value), and logs a warning telling how to write the option.

With the Python package, the `datalab-showcase` command starts DataLab and plays all the demos in a loop, in full screen: it adds `--showcase=all`, `--showcase-loop` and `--showcase-fullscreen` to its command line, unless already given (e.g. `datalab-showcase --showcase=d1,d3 --showcase-screen=1`).

The showcase starts once DataLab is ready: its main window is shown and no startup question is pending. The question about the log files of a previous session which ended abnormally is not asked when the showcase is requested on the command line, so that an unattended booth computer does not wait for an answer. Other startup questions, if any, delay the showcase until they are answered.

### Operator hotkeys

While the showcase plays, the operator may use the following keys:

- **F9**: pause or resume the showcase,
- **Shift+F12**, or **Esc** twice quickly: stop the showcase after the current demo.

Once the showcase is stopped, or once all the demos have been played (without loop), DataLab is given back for a live demonstration: the window gets its previous state back, and the dialogs are no longer accepted automatically.

The showcase is designed to run unattended for hours: if a demo fails, the showcase moves on to the next one, and the dialogs left open are accepted after a while.

## Demos

| Identifier | Demo |
| --- | --- |
| `d1` | Full traceability: history, provenance, cascade recompute |
| `d2` | Reproducibility: provenance capsules (RO-Crate) |
| `d3` | Advanced, interactive image analysis |
| `d4` | Automation and openness: macros and remote control |
| `app:<plugin ID>` | Demo of an installed application plugin (see below) |
| `web` | DataLab Web interlude (see below) |

### Demos of the installed applications

Besides the demos of DataLab itself, each installed application plugin takes part in the showcase with a demo presenting the application in the **Applications** panel. The demos of DataLab and those of the applications alternate. The identifier of the demo of an application is `app:` followed by the plugin identifier (e.g. `app:org.datalab.camera-characterization`).

The demo of an application is generated from what the application declares, without any code specific to the showcase:

- The application is presented with its name and its description.
- Its first two examples designed for a method are tried with their **Try with this example** command: the example is opened, the parameters of the method are shown, then the method runs. Its main result is shown, with its table of results, if any. When the example is designed for several methods, the next one may then run on this result (e.g. compute an absorption spectrum, then normalize it).
- An application without such an example opens its first tool which needs no selection, an instrument first: the instrument window shows its live view, acquires a few times (with and without the **New group** option), then is closed, which disconnects the instrument. For example, the [TANGO Instruments](https://github.com/DataLab-Platform/datalab-tango) plugin is demonstrated live with its **Simulated TANGO devices...** tool (in the versions of the plugin providing this tool), which serves a simulated oscilloscope or camera from DataLab (Python installations only: the TANGO plugin is not qualified for the standalone DataLab).
- The demo ends with an invitation to discover more applications in the plugin catalog.

An application without example nor tool is only presented. The options changed by the demo (method selected in the Applications panel, recent applications of the welcome page, **New group** option of the instruments) are restored at the end of the demo.

### DataLab Web on the same booth

[DataLab Web](https://datalab-platform.com/web/), the version of DataLab running in a web browser, has its own showcase, played by its host page, <https://datalab-platform.com/web-showcase/>.

With two screens, run both showcases side by side: DataLab on one screen (**Screen** option of the dialog, or `--showcase-screen=N`), and the DataLab Web showcase on the other screen, in a browser window.

With a single screen, DataLab may include DataLab Web: each loop then ends with an interlude, during which DataLab Web takes over in a browser window for one pass of its own demos, in the language and at the pace of DataLab. Once the browser window closes, DataLab shows up again and the showcase goes on. To include DataLab Web:

- check **Include DataLab Web** in the **Showcase mode** dialog, and optionally enter the URL of the DataLab Web showcase (the public host page is used by default),
- or use the `--showcase-web` (or `--showcase-web=URL`) command-line option:

```console
DataLab.exe --showcase --showcase-loop --showcase-fullscreen --showcase-web
```

The interlude opens the host page with the `demos` (demo identifiers, or `all`), `close=1` (window closed after one pass), `lang` and `speed` parameters, e.g. `https://datalab-platform.com/web-showcase/?demos=all&close=1&lang=fr&speed=1`. The other parameters of a given URL are kept.

The DataLab Web interlude needs a Chromium-based web browser: Google Chrome (the preferred one), Microsoft Edge (always available on Windows) or Chromium. With Microsoft Edge, DataLab Web may run slower when the *Enhance your security on the web* setting of Edge applies to it. The browser runs with a profile dedicated to the showcase (`showcase-browser` folder of the DataLab configuration folder): the browser window does not show the bookmarks nor the tabs of the usual browser profile, and the Python runtime of DataLab Web, downloaded on the first interlude, is kept for the next ones. The browser window is shown in full screen when DataLab is.

The identifier of the interlude is `web`: give it among the identifiers of the demos to play it elsewhere than at the end of the loop (e.g. `--showcase=d1,web,d2`). To stop the showcase during the interlude, close the browser window (e.g. with **Alt+F4**): DataLab shows up again, then press **Shift+F12**.

The interlude lasts 15 minutes at most: the browser window is closed afterwards. This duration and the DataLab Web demos to play (all of them, by default) may be changed in `showcase.json`, with the `web_timeout` setting (in minutes) and the `web_ids` setting (comma-separated identifiers of the DataLab Web demos).

## Limits

- The plugin is pinned to DataLab 1.4.x: a new minor version of DataLab needs a new release of the plugin.
- When another instance of DataLab is running, DataLab asks whether to continue before loading its plugins: this question is not handled by the showcase, and an unattended booth computer waits for an answer. Make sure that only one DataLab runs on a booth computer.
- The values of the options must be given with `=` (see above).
- The showcase clears the workspace before each demo.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) and [doc/architecture.md](doc/architecture.md).

## Publishing

Set the new version in `pyproject.toml` and in `src/datalab_showcase/__init__.py` (`X.Y.Z`, or `X.Y.ZrcN` for a release candidate), then push a tag such as `v0.1.0` (or `v0.2.0-rc1`). The **Release** workflow checks that the tag matches both versions, compiles the translations, runs the tests, builds the wheel (checking that it contains the compiled translations) and publishes it in a GitHub release with its SHA-256 checksum and build provenance attestation (a release candidate is published as a pre-release): DataLab users install it with **Plugins > Configure plugins... > From file**.

To list a release in the DataLab plugin catalog, open a pull request on <https://github.com/DataLab-Platform/plugins> with the entry printed in the summary of the **Release** workflow run (release candidates are not listed).

## License

BSD 3-Clause, see [LICENSE](LICENSE).
