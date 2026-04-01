"""Audit the explicit public nyc311 namespace surface."""

from __future__ import annotations

import ast
import builtins
import importlib
import inspect
import re
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Final

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PACKAGE_ROOT = SRC / "nyc311"
API_DOC_PATH = ROOT / "docs" / "api.md"
DOC_DIRECTIVE_RE: Final[re.Pattern[str]] = re.compile(r"^:::\s+(nyc311(?:\.[A-Za-z0-9_]+)?)\s*$")
ALLOWED_DUPLICATE_EXPORTS: Final[frozenset[str]] = frozenset()
ALLOWED_PRIVATE_EXPORTS: Final[frozenset[str]] = frozenset({"__version__"})

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

MODULE_AST_CACHE: dict[str, ast.Module | None] = {}
IMPORT_MAP_CACHE: dict[str, dict[str, str]] = {}
DEFINITION_KIND_CACHE: dict[str, dict[str, str]] = {}


@dataclass(frozen=True)
class AuditRow:
    public_module: str
    symbol_name: str
    origin_module: str
    kind: str


def discover_public_modules() -> tuple[str, ...]:
    """Derive the public top-level module list from the package layout."""
    discovered = ["nyc311"]
    for child in sorted(PACKAGE_ROOT.iterdir(), key=lambda path: path.name):
        if child.name in {"__pycache__", "py.typed"} or child.name.startswith("_"):
            continue
        if child.is_dir() and (child / "__init__.py").exists():
            discovered.append(f"nyc311.{child.name}")
            continue
        if child.is_file() and child.suffix == ".py" and child.stem not in {"__init__", "__main__"}:
            discovered.append(f"nyc311.{child.stem}")
    return tuple(discovered)


def module_path(module_name: str) -> Path | None:
    """Return the local source path for a nyc311 module."""
    if not module_name.startswith("nyc311"):
        return None

    relative = module_name.removeprefix("nyc311").lstrip(".")
    if not relative:
        candidate = PACKAGE_ROOT / "__init__.py"
        return candidate if candidate.exists() else None

    module_parts = relative.split(".")
    file_candidate = PACKAGE_ROOT.joinpath(*module_parts).with_suffix(".py")
    if file_candidate.exists():
        return file_candidate

    package_candidate = PACKAGE_ROOT.joinpath(*module_parts, "__init__.py")
    if package_candidate.exists():
        return package_candidate

    return None


def parse_module_ast(module_name: str) -> ast.Module | None:
    """Parse and cache the AST for a local module."""
    if module_name in MODULE_AST_CACHE:
        return MODULE_AST_CACHE[module_name]

    path = module_path(module_name)
    if path is None:
        MODULE_AST_CACHE[module_name] = None
        return None

    tree = ast.parse(path.read_text(encoding="utf-8"))
    MODULE_AST_CACHE[module_name] = tree
    return tree


def resolve_relative_import(module_name: str, level: int, imported_module: str | None) -> str:
    """Resolve a relative import target to an absolute module path."""
    path = module_path(module_name)
    parent_parts = module_name.split(".")
    if path is not None and path.name == "__init__.py":
        base_parts = parent_parts
    else:
        base_parts = parent_parts[:-1]

    anchor_parts = base_parts[: len(base_parts) - level + 1]
    if imported_module:
        anchor_parts.extend(imported_module.split("."))
    return ".".join(anchor_parts)


def build_import_map(module_name: str) -> dict[str, str]:
    """Map imported symbol names in a module to their source modules."""
    if module_name in IMPORT_MAP_CACHE:
        return IMPORT_MAP_CACHE[module_name]

    import_map: dict[str, str] = {}
    tree = parse_module_ast(module_name)
    if tree is None:
        IMPORT_MAP_CACHE[module_name] = import_map
        return import_map

    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            if node.level > 0:
                origin_module = resolve_relative_import(module_name, node.level, node.module)
            elif node.module is not None:
                origin_module = node.module
            else:
                continue

            for alias in node.names:
                public_name = alias.asname or alias.name
                import_map[public_name] = origin_module

    IMPORT_MAP_CACHE[module_name] = import_map
    return import_map


def is_type_alias_expr(node: ast.AST | None) -> bool:
    """Return whether an AST expression looks like a runtime type alias."""
    if node is None:
        return False
    if isinstance(node, ast.Name):
        return node.id in builtins.__dict__ or node.id[:1].isupper()
    if isinstance(node, ast.Attribute):
        return True
    if isinstance(node, ast.Subscript):
        return is_type_alias_expr(node.value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return is_type_alias_expr(node.left) and is_type_alias_expr(node.right)
    return False


def build_definition_kinds(module_name: str) -> dict[str, str]:
    """Map symbol names defined in a module to a coarse kind string."""
    if module_name in DEFINITION_KIND_CACHE:
        return DEFINITION_KIND_CACHE[module_name]

    kinds: dict[str, str] = {}
    tree = parse_module_ast(module_name)
    if tree is None:
        DEFINITION_KIND_CACHE[module_name] = kinds
        return kinds

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            kinds[node.name] = "class"
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            kinds[node.name] = "callable"
            continue
        if hasattr(ast, "TypeAlias") and isinstance(node, ast.TypeAlias):
            kinds[node.name.id] = "type_alias"
            continue
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    kinds[target.id] = "type_alias" if is_type_alias_expr(node.value) else "value"
            continue
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            kinds[node.target.id] = "type_alias" if is_type_alias_expr(node.value) else "value"

    DEFINITION_KIND_CACHE[module_name] = kinds
    return kinds


def exported_names(module_name: str) -> list[str]:
    """Load and validate ``__all__`` for a public module."""
    module = importlib.import_module(module_name)
    names = getattr(module, "__all__", None)
    if not isinstance(names, list):
        raise ValueError(f"{module_name} must define __all__ as a list.")
    for symbol_name in names:
        if not isinstance(symbol_name, str):
            raise ValueError(f"{module_name}.__all__ must contain only strings.")
        if symbol_name.startswith("_") and symbol_name not in ALLOWED_PRIVATE_EXPORTS:
            raise ValueError(f"{module_name}.__all__ must not export private name {symbol_name!r}.")
        if not hasattr(module, symbol_name):
            raise ValueError(f"{module_name}.__all__ references missing symbol {symbol_name!r}.")
    return names


def symbol_origin_module(public_module: str, symbol_name: str, symbol: object) -> str:
    """Resolve the most specific source module for a public symbol."""
    import_map = build_import_map(public_module)
    if symbol_name in import_map:
        explicit_origin = getattr(symbol, "__module__", None)
        if not isinstance(explicit_origin, str) or explicit_origin in {"builtins", "typing", "types"}:
            return import_map[symbol_name]

    explicit_origin = getattr(symbol, "__module__", None)
    if isinstance(explicit_origin, str):
        return explicit_origin

    if symbol_name in import_map:
        return import_map[symbol_name]

    if symbol_name == "__version__":
        return "nyc311._version"
    return public_module


def is_runtime_type_alias(symbol: object) -> bool:
    """Return whether a runtime object looks like a type alias target."""
    if isinstance(symbol, (type, types.GenericAlias, types.UnionType)):
        return True
    type_alias_type = getattr(__import__("typing"), "TypeAliasType", None)
    return type_alias_type is not None and isinstance(symbol, type_alias_type)


def classify_symbol_kind(origin_module: str, symbol_name: str, symbol: object) -> str:
    """Return a readable kind label for a public symbol."""
    definition_kinds = build_definition_kinds(origin_module)
    if symbol_name in definition_kinds:
        inferred_kind = definition_kinds[symbol_name]
        if inferred_kind == "type_alias" and not is_runtime_type_alias(symbol):
            return "value"
        return inferred_kind
    if inspect.isclass(symbol):
        return "class"
    if callable(symbol):
        return "callable"
    return "value"


def public_rows(public_modules: tuple[str, ...]) -> list[AuditRow]:
    """Return the public API rows for all discovered public modules."""
    rows: list[AuditRow] = []
    for public_module in public_modules:
        module = importlib.import_module(public_module)
        for symbol_name in exported_names(public_module):
            symbol = getattr(module, symbol_name)
            origin_module = symbol_origin_module(public_module, symbol_name, symbol)
            kind = classify_symbol_kind(origin_module, symbol_name, symbol)
            rows.append(
                AuditRow(
                    public_module=public_module,
                    symbol_name=symbol_name,
                    origin_module=origin_module,
                    kind=kind,
                )
            )
    return rows


def validate_unique_public_locations(rows: list[AuditRow]) -> None:
    """Ensure public symbols are exposed in a single namespace unless allowed."""
    symbol_locations: dict[str, list[str]] = {}
    for row in rows:
        symbol_locations.setdefault(row.symbol_name, []).append(row.public_module)

    duplicates = {
        symbol_name: locations
        for symbol_name, locations in symbol_locations.items()
        if len(locations) > 1 and symbol_name not in ALLOWED_DUPLICATE_EXPORTS
    }
    if duplicates:
        formatted = ", ".join(
            f"{symbol_name}: {sorted(locations)}"
            for symbol_name, locations in sorted(duplicates.items())
        )
        raise ValueError(f"Public symbols must have unique locations. Duplicates: {formatted}")


def documented_public_modules() -> set[str]:
    """Return the set of namespaces referenced by mkdocstrings directives."""
    modules: set[str] = set()
    for line in API_DOC_PATH.read_text(encoding="utf-8").splitlines():
        match = DOC_DIRECTIVE_RE.match(line.strip())
        if match:
            modules.add(match.group(1))
    return modules


def validate_docs_api_coverage(public_modules: tuple[str, ...]) -> None:
    """Ensure every public namespace is represented in docs/api.md."""
    documented = documented_public_modules()
    expected = set(public_modules)
    missing = sorted(expected.difference(documented))
    extras = sorted(documented.difference(expected))
    if missing or extras:
        parts: list[str] = []
        if missing:
            parts.append(f"missing docs entries for {missing}")
        if extras:
            parts.append(f"unexpected docs entries for {extras}")
        joined = "; ".join(parts)
        raise ValueError(f"docs/api.md public namespace coverage mismatch: {joined}.")


def main() -> int:
    """Print a markdown table summarizing the current public namespace surface."""
    public_modules = discover_public_modules()
    rows = public_rows(public_modules)
    validate_unique_public_locations(rows)
    validate_docs_api_coverage(public_modules)

    lines = [
        "# nyc311 public API audit",
        "",
        f"- public modules: {len(public_modules)}",
        f"- public symbols: {len(rows)}",
        "",
        "| Public Module | Symbol | Origin | Kind |",
        "| --- | --- | --- | --- |",
        *[
            f"| `{row.public_module}` | `{row.symbol_name}` | `{row.origin_module}` | `{row.kind}` |"
            for row in rows
        ],
    ]
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
