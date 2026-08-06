#!/usr/bin/env python3
"""Validate every ``aws-cloud-utilities`` example in docs/ against the real CLI.

Catches documentation drift: examples that reference a command group, a
subcommand, or an option that does not exist. Exits non-zero when any example
is invalid so CI can gate on it.

Usage:
    python scripts/validate_docs.py [DOCS_DIR]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cli_introspect import PROG, Node, build_root  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

# Tokens that are deliberately illustrative rather than literal: bracketed
# placeholders (<name>, [OPTIONS]) and bare metavars (COMMAND, BUCKET_NAME).
# Real command names are always lowercase, so an all-caps token is never one.
PLACEHOLDER = re.compile(r"[<>\[\]{}]|\.\.\.|^[A-Z][A-Z0-9_]*$")

# Root options that take no value, so the next token is not their argument.
VALUELESS_GLOBAL = {"--verbose", "--debug", "--help", "--version"}

# Opt out of validation for a deliberately-invalid example.
IGNORE = "validate-docs: ignore"


class Issue(NamedTuple):
    path: Path
    line: int
    kind: str
    detail: str
    example: str


def _iter_examples(text: str):
    """Yield ``(line_number, command)`` for each CLI example, joining continuations.

    A line containing ``validate-docs: ignore`` exempts the example that follows
    it, so pages can show deliberately-invalid usage as a counter-example.
    """
    lines = text.split("\n")
    idx = 0
    while idx < len(lines):
        stripped = lines[idx].strip()
        if stripped.startswith("$ "):
            stripped = stripped[2:].strip()
        if not stripped.startswith(PROG):
            idx += 1
            continue

        preceding = next((ln for ln in reversed(lines[:idx]) if ln.strip()), "")
        if IGNORE in preceding:
            idx += 1
            continue

        start = idx + 1
        parts = [stripped]
        while parts[-1].endswith("\\") and idx + 1 < len(lines):
            idx += 1
            parts[-1] = parts[-1].rstrip("\\").strip()
            parts.append(lines[idx].strip())
        idx += 1
        yield start, " ".join(parts)


def _tokenize(command: str) -> List[str]:
    """Split a command into tokens, dropping shell pipelines and redirects."""
    command = re.split(r"\s(?:\|\||&&|>>|\||>|;)\s", command)[0]
    return command.split()


def _skip_global_options(tokens: List[str]) -> List[str]:
    """Drop root-level options that appear before the command name."""
    pos = 0
    while pos < len(tokens) and tokens[pos].startswith("-"):
        flag = tokens[pos].split("=")[0]
        takes_value = "=" not in tokens[pos] and flag not in VALUELESS_GLOBAL
        pos += 2 if takes_value else 1
    return tokens[pos:]


def _valid_flags(node: Node) -> set:
    """Options accepted *after* the command name.

    Root options such as ``--profile`` and ``--output`` are not included: Click
    rejects them in trailing position, so documenting them there is a real bug.
    """
    return {o for p in node.params for o in p.opts if o.startswith("-")} | {"--help"}


def validate(docs_dir: Path) -> tuple[List[Issue], int]:
    root = build_root()
    issues: List[Issue] = []
    checked = 0

    for path in sorted(docs_dir.rglob("*.md")):
        if path.name.startswith("."):
            continue  # macOS AppleDouble sidecars (._foo.md) are not documentation
        for line_no, command in _iter_examples(path.read_text(encoding="utf-8")):
            checked += 1
            tokens = _skip_global_options(_tokenize(command)[1:])

            # Descend the tree as far as the tokens name real subcommands.
            node = root
            consumed: List[str] = []
            for token in tokens:
                if token.startswith("-") or PLACEHOLDER.search(token):
                    break
                if token in node.children:
                    node = node.children[token]
                    consumed.append(token)
                    continue
                if node.is_group:
                    available = ", ".join(sorted(node.children))
                    context = " ".join(consumed) or "(top level)"
                    issues.append(
                        Issue(
                            path,
                            line_no,
                            "unknown-subcommand",
                            f"{context} -> '{token}' (available: {available})",
                            command,
                        )
                    )
                    node = None
                break

            if node is None:
                continue

            valid = _valid_flags(node)
            root_flags = {o for p in root.params for o in p.opts if o.startswith("-")}
            for token in tokens[len(consumed) :]:
                if not token.startswith("--"):
                    continue
                flag = token.split("=")[0]
                if PLACEHOLDER.search(flag) or flag in valid:
                    continue
                context = " ".join(consumed) or PROG
                kind = "misplaced-global-option" if flag in root_flags else "unknown-option"
                issues.append(Issue(path, line_no, kind, f"{context} {flag}", command))

    return issues, checked


def main() -> int:
    docs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "docs"
    if not docs_dir.is_dir():
        print(f"error: no such docs directory: {docs_dir}", file=sys.stderr)
        return 2

    issues, checked = validate(docs_dir)

    if not issues:
        print(f"OK: {checked} CLI examples in {docs_dir.name}/ all match the current command tree.")
        return 0

    current = None
    for issue in issues:
        rel = issue.path.relative_to(REPO_ROOT)
        if rel != current:
            current = rel
            print(f"\n{rel}")
        print(f"  line {issue.line}: {issue.kind}: {issue.detail}")
        print(f"    {issue.example}")

    print(f"\n{len(issues)} invalid example(s) out of {checked} checked.")
    print("Run 'make docs-gen' to regenerate command reference sections from the CLI.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
