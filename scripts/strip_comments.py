from __future__ import annotations

import ast
import io
import re
import sys
import tokenize
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

PYTHON_FILES = [
    "OR-Tools/main.py",
    "OR-Tools/src/__init__.py",
    "OR-Tools/src/benchmark.py",
    "OR-Tools/src/benchmark_pousse.py",
    "OR-Tools/src/distances.py",
    "OR-Tools/src/parsers.py",
    "OR-Tools/src/timer.py",
    "OR-Tools/src/tsp_solver.py",
    "OR-Tools/src/ukp_solver.py",
    "OR-Tools/src/visualization.py",
    "OR-Tools/src/visualization_pousse.py",
    "scripts/make_plots.py",
]

C_FILES = [
    "Separation-Evaluation/src/common.c",
    "Separation-Evaluation/src/main.c",
    "Separation-Evaluation/src/output.c",
    "Separation-Evaluation/src/parser_tsp.c",
    "Separation-Evaluation/src/parser_ukp.c",
    "Separation-Evaluation/src/timer.c",
    "Separation-Evaluation/src/tsplib.c",
    "Separation-Evaluation/src/tsp_bb.c",
    "Separation-Evaluation/src/ukp_bb.c",
    "Separation-Evaluation/include/common.h",
    "Separation-Evaluation/include/output.h",
    "Separation-Evaluation/include/parser_tsp.h",
    "Separation-Evaluation/include/parser_ukp.h",
    "Separation-Evaluation/include/timer.h",
    "Separation-Evaluation/include/tsplib.h",
    "Separation-Evaluation/include/tsp_bb.h",
    "Separation-Evaluation/include/ukp_bb.h",
]


def _collect_docstring_byte_ranges(source: str, source_bytes: bytes) -> list[tuple[int, int]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    byte_lines = source_bytes.splitlines(keepends=True)

    def line_col_to_byte_offset(line: int, col: int) -> int:
        offset = 0
        for i in range(line - 1):
            offset += len(byte_lines[i])
        return offset + col

    ranges: list[tuple[int, int]] = []
    container_types = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

    for node in ast.walk(tree):
        if not isinstance(node, container_types):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if not isinstance(first, ast.Expr):
            continue
        value = first.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            start = line_col_to_byte_offset(first.lineno, first.col_offset)
            end = line_col_to_byte_offset(first.end_lineno, first.end_col_offset)
            ranges.append((start, end))

    return ranges


def _collect_comment_char_ranges(source: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    char_lines = source.splitlines(keepends=True)

    def line_col_to_char_offset(line: int, col: int) -> int:
        offset = 0
        for i in range(line - 1):
            offset += len(char_lines[i])
        return offset + col

    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                start = line_col_to_char_offset(tok.start[0], tok.start[1])
                end = line_col_to_char_offset(tok.end[0], tok.end[1])
                ranges.append((start, end))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return ranges


def _apply_byte_deletions(source_bytes: bytes, ranges: list[tuple[int, int]]) -> bytes:
    if not ranges:
        return source_bytes
    sorted_ranges = sorted(ranges, key=lambda x: x[0], reverse=True)
    data = bytearray(source_bytes)
    for start, end in sorted_ranges:
        del data[start:end]
    return bytes(data)


def _apply_char_deletions(source: str, ranges: list[tuple[int, int]]) -> str:
    if not ranges:
        return source
    sorted_ranges = sorted(ranges, key=lambda x: x[0], reverse=True)
    chars = list(source)
    for start, end in sorted_ranges:
        del chars[start:end]
    return "".join(chars)


def _clean_blank_lines(text: str) -> str:
    lines = text.splitlines()
    cleaned: list[str] = []
    blank_run = 0
    for line in lines:
        stripped = line.rstrip()
        if stripped == "":
            blank_run += 1
            if blank_run <= 1:
                cleaned.append("")
        else:
            blank_run = 0
            cleaned.append(stripped)

    while cleaned and cleaned[0] == "":
        cleaned.pop(0)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()

    return "\n".join(cleaned) + "\n"


def strip_python(source: str) -> str:
    source_bytes = source.encode("utf-8")
    doc_ranges = _collect_docstring_byte_ranges(source, source_bytes)
    after_docs_bytes = _apply_byte_deletions(source_bytes, doc_ranges)
    after_docs = after_docs_bytes.decode("utf-8")

    comment_ranges = _collect_comment_char_ranges(after_docs)
    after_comments = _apply_char_deletions(after_docs, comment_ranges)

    return _clean_blank_lines(after_comments)


def strip_c(source: str) -> str:
    out: list[str] = []
    i = 0
    n = len(source)
    state = "CODE"

    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""

        if state == "CODE":
            if ch == '"':
                out.append(ch)
                state = "STRING"
                i += 1
            elif ch == "'":
                out.append(ch)
                state = "CHAR"
                i += 1
            elif ch == "/" and nxt == "/":
                state = "LINE_COMMENT"
                i += 2
            elif ch == "/" and nxt == "*":
                state = "BLOCK_COMMENT"
                i += 2
            else:
                out.append(ch)
                i += 1
        elif state == "STRING":
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(source[i + 1])
                i += 2
            elif ch == '"':
                state = "CODE"
                i += 1
            else:
                i += 1
        elif state == "CHAR":
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(source[i + 1])
                i += 2
            elif ch == "'":
                state = "CODE"
                i += 1
            else:
                i += 1
        elif state == "LINE_COMMENT":
            if ch == "\n":
                out.append(ch)
                state = "CODE"
                i += 1
            else:
                i += 1
        elif state == "BLOCK_COMMENT":
            if ch == "*" and nxt == "/":
                state = "CODE"
                i += 2
            else:
                i += 1

    return _clean_blank_lines("".join(out))


def process_file(path: Path, kind: str) -> tuple[int, int]:
    original = path.read_text(encoding="utf-8")
    if kind == "python":
        stripped = strip_python(original)
    else:
        stripped = strip_c(original)
    path.write_text(stripped, encoding="utf-8")
    return len(original.splitlines()), len(stripped.splitlines())


def main() -> int:
    total_before = 0
    total_after = 0
    errors: list[str] = []

    for rel in PYTHON_FILES:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing: {rel}")
            continue
        try:
            before, after = process_file(path, "python")
            total_before += before
            total_after += after
            print(f"PY  {rel}: {before} -> {after} lignes")
        except Exception as exc:
            errors.append(f"{rel}: {exc}")

    for rel in C_FILES:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing: {rel}")
            continue
        try:
            before, after = process_file(path, "c")
            total_before += before
            total_after += after
            print(f"C   {rel}: {before} -> {after} lignes")
        except Exception as exc:
            errors.append(f"{rel}: {exc}")

    print()
    print(f"Total: {total_before} -> {total_after} lignes ({total_before - total_after} supprimees)")
    if errors:
        print("ERREURS:")
        for err in errors:
            print(f"  - {err}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
