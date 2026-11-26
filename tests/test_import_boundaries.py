import ast
from pathlib import Path

from tests.architecture.contracts import ALLOWED_DEPENDENCIES

REPO_ROOT = Path(__file__).resolve().parents[1]
APPS_DIR = REPO_ROOT / "apps"


def _extract_imported_apps(file_path: Path) -> set[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    imported_apps: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if len(parts) >= 2 and parts[0] == "apps":
                    imported_apps.add(parts[1])
        elif isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split(".")
            if len(parts) >= 2 and parts[0] == "apps":
                imported_apps.add(parts[1])

    return imported_apps


def test_no_disallowed_app_imports():
    violations: list[str] = []

    for app_dir in sorted(APPS_DIR.iterdir()):
        if not app_dir.is_dir() or app_dir.name not in ALLOWED_DEPENDENCIES:
            continue
        source_app = app_dir.name
        allowed = ALLOWED_DEPENDENCIES[source_app] | {source_app}

        for py_file in sorted(app_dir.rglob("*.py")):
            for target_app in sorted(_extract_imported_apps(py_file)):
                if target_app not in allowed:
                    rel_path = py_file.relative_to(REPO_ROOT)
                    violations.append(
                        f"{rel_path} ({source_app}) imports disallowed app '{target_app}'"
                    )

    assert not violations, "Disallowed module imports found:\n" + "\n".join(violations)
