"""Introspect the aws-cloud-utilities Click command tree.

Shared by ``scripts/gen_docs.py`` (which renders the command reference) and
``scripts/validate_docs.py`` (which checks that every example in ``docs/`` is
a command the CLI actually accepts).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional

import click

from aws_cloud_utilities.cli import main

PROG = "aws-cloud-utilities"


def _is_unset(value: object) -> bool:
    """Click 8.2 uses a sentinel object for 'no default'; it has no useful repr."""
    return value is None or type(value).__name__ == "Sentinel" or repr(value) == "Sentinel.UNSET"


@dataclass
class Param:
    """A single option or positional argument on a command."""

    opts: List[str]
    metavar: str
    help: Optional[str]
    required: bool
    is_argument: bool
    default: Optional[str]
    choices: Optional[List[str]]
    multiple: bool


@dataclass
class Node:
    """A command or command group in the CLI tree."""

    name: str
    path: str
    summary: str
    description: str
    params: List[Param] = field(default_factory=list)
    children: Dict[str, "Node"] = field(default_factory=dict)

    @property
    def is_group(self) -> bool:
        return bool(self.children)

    @property
    def options(self) -> List[Param]:
        return [p for p in self.params if not p.is_argument]

    @property
    def arguments(self) -> List[Param]:
        return [p for p in self.params if p.is_argument]

    def walk(self) -> Iterator["Node"]:
        """Yield this node and every descendant, depth-first."""
        yield self
        for child in self.children.values():
            yield from child.walk()

    def leaves(self) -> Iterator["Node"]:
        """Yield every runnable (non-group) command under this node."""
        for node in self.walk():
            if not node.is_group and node.path:
                yield node


def _summary(cmd: click.Command) -> str:
    text = (cmd.help or cmd.short_help or "").strip()
    if not text:
        return ""
    return " ".join(text.split("\n\n")[0].split())


def _describe(param: click.Parameter) -> Param:
    choices = list(param.type.choices) if isinstance(param.type, click.Choice) else None
    is_argument = isinstance(param, click.Argument)

    if is_argument:
        opts = [param.name.upper()]
        metavar = (param.metavar or param.name).upper()
        if param.nargs == -1:
            metavar += "..."
    else:
        opts = [o for o in param.opts if o.startswith("-")]
        metavar = (
            "" if getattr(param, "is_flag", False) else str(getattr(param.type, "name", "")).upper()
        )

    default = param.default
    if callable(default) or _is_unset(default) or default is False:
        default = None
    if isinstance(default, (list, tuple)):
        default = ",".join(str(v) for v in default) or None

    return Param(
        opts=opts,
        metavar=metavar,
        help=getattr(param, "help", None),
        required=bool(param.required),
        is_argument=is_argument,
        default=None if default is None else str(default),
        choices=choices,
        multiple=bool(getattr(param, "multiple", False)),
    )


def _build(cmd: click.Command, name: str, path: str) -> Node:
    node = Node(
        name=name,
        path=path,
        summary=_summary(cmd),
        description=(cmd.help or "").strip(),
        params=[_describe(p) for p in cmd.params if p.name != "help"],
    )
    if isinstance(cmd, click.Group):
        for sub_name, sub in sorted(cmd.commands.items()):
            node.children[sub_name] = _build(sub, sub_name, f"{path} {sub_name}".strip())
    return node


def build_root() -> Node:
    """The whole CLI as a tree, rooted at ``aws-cloud-utilities``."""
    return _build(main, PROG, "")
