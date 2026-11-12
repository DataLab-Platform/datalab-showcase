# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - Unreleased

First release of the plugin: the Showcase mode, formerly developed for DataLab 1.5 (DataLab-Platform/DataLab#529), moves out of DataLab into this plugin, installable in the standalone DataLab from the plugin catalog or from a file.

- **Plugins > DataLab Showcase > Showcase mode...** plays live demos of DataLab features, without any user interaction, for exhibitions, conference booths and kiosks: a dialog chooses the demos, the loop, the pace, full screen display, the screen and the DataLab Web interlude. The choices are remembered in `showcase.json`, in the configuration folder of DataLab.
- Four demos of DataLab: full traceability (history, provenance and cascade recompute), reproducibility with provenance capsules (RO-Crate), advanced and interactive image analysis, and automation with macros and remote control. Each installed application plugin also takes part in the showcase, with a demo generated from its examples or its first tool (e.g. the simulated devices of the TANGO Instruments plugin).
- Command-line options of DataLab start a booth computer directly in unattended showcase mode, e.g. `DataLab.exe --showcase --showcase-loop --showcase-fullscreen`: `--showcase`, `--showcase=IDS`, `--showcase-loop`, `--showcase-speed=SPEED`, `--showcase-screen=N`, `--showcase-fullscreen` and `--showcase-web[=URL]` (values are given with `=`). The showcase starts once DataLab is ready, without asking about the log files of a previous session. With the Python package, the `datalab-showcase` command plays all the demos in a loop, in full screen.
- On a single-screen booth, each loop may end with one pass of the DataLab Web showcase (host page <https://datalab-platform.com/web-showcase/>), in a browser window (Google Chrome, Microsoft Edge or Chromium), in the language and at the pace of DataLab.
- Operator hotkeys: **F9** pauses or resumes the showcase, **Shift+F12** (or **Esc** twice) stops it after the current demo. A failing demo does not stop the showcase.
- English and French user interface, following the language of DataLab.
- Requires DataLab 1.4.1 or a later 1.4.x version.
