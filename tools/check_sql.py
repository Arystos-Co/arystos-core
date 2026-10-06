"""Detect SQL string literals using interpolated formatting."""

import ast
import re
import sys
from pathlib import Path

SQL_KEYWORDS = re.compile(r"\b(?:SELECT|INSERT|UPDATE|DELETE)\b", re.IGNORECASE)


def contains_sql_keyword(value: str) -> bool:
    """Return whether a string contains a SQL statement keyword."""
    return SQL_KEYWORDS.search(value) is not None


def find_unsafe_sql_strings(source: str) -> list[int]:
    """Return line numbers of interpolated string expressions containing SQL keywords."""
    tree = ast.parse(source)
    flagged_lines: set[int] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            literal_text = "".join(
                value.value
                for value in node.values
                if isinstance(value, ast.Constant) and isinstance(value.value, str)
            )
            if contains_sql_keyword(literal_text):
                flagged_lines.add(node.lineno)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "format" and isinstance(node.func.value, ast.Constant):
                value = node.func.value.value
                if isinstance(value, str) and contains_sql_keyword(value):
                    flagged_lines.add(node.lineno)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                if contains_sql_keyword(node.left.value):
                    flagged_lines.add(node.lineno)

    return sorted(flagged_lines)


def main() -> int:
    """Scan server Python sources and report unsafe SQL string formatting."""
    server_path = Path(__file__).resolve().parents[1] / "server"
    violations: list[tuple[Path, int]] = []

    for path in sorted(server_path.rglob("*.py")):
        for line_number in find_unsafe_sql_strings(path.read_text(encoding="utf-8")):
            violations.append((path, line_number))

    if violations:
        for path, line_number in violations:
            print(f"{path}:{line_number}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
