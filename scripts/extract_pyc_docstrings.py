from __future__ import annotations

import dis
import importlib.util
import marshal
import sys
from pathlib import Path
from types import CodeType

sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")


def load_code(pyc_path: Path) -> CodeType | None:
    try:
        with open(pyc_path, "rb") as f:
            magic = f.read(16)
            code = marshal.load(f)
        if isinstance(code, CodeType):
            return code
    except Exception as exc:
        print(f"  ERREUR chargement {pyc_path.name}: {exc}", file=sys.stderr)
    return None


def walk_codes(code: CodeType, prefix: str = ""):
    name = code.co_name
    full = f"{prefix}.{name}" if prefix else name
    yield full, code
    for const in code.co_consts:
        if isinstance(const, CodeType):
            yield from walk_codes(const, full)


def extract_docstring(code: CodeType) -> str | None:
    consts = code.co_consts
    if not consts:
        return None
    first = consts[0]
    if isinstance(first, str):
        return first
    return None


def main():
    pyc_dir = Path("OR-Tools/src/__pycache__")
    targets = ["benchmark", "benchmark_pousse", "timer", "ukp_solver", "visualization"]

    for module_name in targets:
        candidates = sorted(pyc_dir.glob(f"{module_name}.cpython-*.pyc"))
        if not candidates:
            print(f"\n=== {module_name}: AUCUN .pyc trouve ===")
            continue
        pyc = candidates[-1]
        print(f"\n=== {module_name} (depuis {pyc.name}) ===")
        code = load_code(pyc)
        if code is None:
            continue
        for full_name, c in walk_codes(code):
            ds = extract_docstring(c)
            if ds:
                preview = ds.replace("\n", "\\n")
                if len(preview) > 200:
                    preview = preview[:200] + "..."
                print(f"  [{c.co_firstlineno:>4}] {full_name}: {preview!r}")


if __name__ == "__main__":
    main()
