# Copyright (c) DataLab Platform Developers, BSD 3-Clause license, see LICENSE file.

"""Dependency rules of the layers of the plugin."""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[2] / "src" / "datalab_showcase"
PACKAGE_NAME = "datalab_showcase"
#: Modules of the hosts (DataLab and Qt)
HOST_MODULES = (
    "PyQt5",
    "PyQt6",
    "PySide6",
    "datalab",
    "guidata",
    "js",
    "plotpy",
    "pyodide",
    "qtpy",
    "sigima",
    "sigimax",
)
#: Modules of the test suites, not available in the standalone DataLab
TEST_MODULES = ("_pytest", "datalab.tests", "pytest", "sigimax.tests")
#: Modules forbidden in each layer, besides the test modules
FORBIDDEN_LAYER_IMPORTS = {
    "core": (*HOST_MODULES, f"{PACKAGE_NAME}.adapters", f"{PACKAGE_NAME}.showcase"),
    "showcase": (f"{PACKAGE_NAME}.adapters",),
    "adapters": (),
}


def _module_imports(filename: Path) -> set[str]:
    """Return direct imports declared by one Python source file."""
    tree = ast.parse(filename.read_text(encoding="utf-8"), filename=str(filename))
    relative_parts = filename.relative_to(PACKAGE_ROOT).with_suffix("").parts
    package_parts = (PACKAGE_NAME, *relative_parts[:-1])
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                if node.module is not None:
                    imports.add(node.module)
                continue
            base_parts = package_parts[: len(package_parts) - node.level + 1]
            if node.module is not None:
                imports.add(".".join((*base_parts, *node.module.split("."))))
            else:
                imports.update(
                    ".".join((*base_parts, *alias.name.split(".")))
                    for alias in node.names
                )
    return imports


def _matches(module: str, prefixes: tuple[str, ...]) -> bool:
    """Return True if a module is one of the prefixes, or one of their modules"""
    return any(
        module == prefix or module.startswith(f"{prefix}.") for prefix in prefixes
    )


def test_package_root_does_not_import_hosts() -> None:
    """Importing the package identity loads neither DataLab, nor Qt, nor adapters."""
    imports = _module_imports(PACKAGE_ROOT / "__init__.py")
    assert not any(_matches(name, HOST_MODULES) for name in imports)
    assert not any(name.startswith(f"{PACKAGE_NAME}.") for name in imports)


def test_import_scanner_resolves_relative_imports() -> None:
    """Relative imports cannot bypass the architecture checks."""
    imports = _module_imports(PACKAGE_ROOT / "showcase" / "scenarios" / "__init__.py")
    assert f"{PACKAGE_NAME}.showcase.engine" in imports


def test_layers_do_not_import_forbidden_modules() -> None:
    """The core layer is host independent, the showcase layer does not depend on
    the adapters, and no module imports a test suite."""
    violations: list[str] = []
    for layer, forbidden in FORBIDDEN_LAYER_IMPORTS.items():
        for filename in sorted((PACKAGE_ROOT / layer).rglob("*.py")):
            for imported_module in sorted(_module_imports(filename)):
                if _matches(imported_module, forbidden + TEST_MODULES):
                    violations.append(
                        f"{filename.relative_to(PACKAGE_ROOT)} imports "
                        f"{imported_module}"
                    )
    for filename in sorted(PACKAGE_ROOT.glob("*.py")):
        for imported_module in sorted(_module_imports(filename)):
            if _matches(imported_module, TEST_MODULES):
                violations.append(f"{filename.name} imports {imported_module}")
    assert not violations, "\n".join(violations)
