"""🔴 The purity boundary (PRD §25.3) — the highest-leverage code decision.

Walks the AST of every file in engine/ and fails the build if it imports or calls
anything that would make the science non-deterministic or dependent on the outside
world. This is what lets the engine be trusted and unit-tested offline.
"""
from __future__ import annotations

import ast
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent.parent / "engine"

FORBIDDEN_IMPORTS = {
    "requests", "httpx", "urllib", "random",
    "subprocess", "socket", "boto3", "supabase",
}
FORBIDDEN_BUILTINS = {"open"}
FORBIDDEN_CALLS = {"datetime.now", "time.time", "os.environ", "os.getenv"}


def _dotted(node: ast.AST) -> str:
    """Reconstruct a dotted name from an Attribute/Name chain (e.g. ``os.getenv``)."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in FORBIDDEN_IMPORTS:
                    found.append(f"{path.name}:{node.lineno} import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in FORBIDDEN_IMPORTS:
                found.append(f"{path.name}:{node.lineno} from {node.module} import ...")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_BUILTINS:
                found.append(f"{path.name}:{node.lineno} call {node.func.id}()")
        elif isinstance(node, ast.Attribute):
            dotted = _dotted(node)
            if dotted in FORBIDDEN_CALLS:
                found.append(f"{path.name}:{node.lineno} {dotted}")
    return found


def test_engine_is_pure():
    all_violations: list[str] = []
    for py in sorted(ENGINE_DIR.rglob("*.py")):
        all_violations.extend(_violations(py))
    assert not all_violations, "engine/ purity violations:\n" + "\n".join(all_violations)
