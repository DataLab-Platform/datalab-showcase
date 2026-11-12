# DataLab Showcase

Showcase mode: live and unattended demos of DataLab for exhibitions

## Trying the plugin in DataLab

Add this project folder in **Plugins > Configure plugins... > Advanced**,
then reload the plugins: DataLab loads the plugin from
`src/datalab_showcase/adapters/desktop.py`, without installing the project.

## Development

```bash
python -m pip install -e ".[test]"
python -m pytest
python -m ruff check .
```

Installing the project also registers `org.datalab.showcase` through the
`datalab.plugins` entry-point group, as the published wheel does. Put
host-independent algorithms in `core`, compose them into headless recipes in
`workflow`, and keep DataLab or browser integration in `adapters`. The generated
architecture test preserves these dependency boundaries as the plugin grows.

## Publishing

Set the new version in `pyproject.toml` and in the package `__init__.py`
(`X.Y.Z`, or `X.Y.ZrcN` for a release candidate), then push a tag such as
`v0.1.0` (or `v0.2.0-rc1`). The **Release** workflow checks that the tag matches
both versions, runs the tests, builds the wheel and publishes it in a GitHub
release with its SHA-256 checksum and build provenance attestation (a release
candidate is published as a pre-release): DataLab users install it with
**Plugins > Configure plugins... > From file**.

To list a release in the DataLab plugin catalog, open a pull request on
<https://github.com/DataLab-Platform/plugins> with the entry printed in the
summary of the **Release** workflow run (release candidates are not listed).
