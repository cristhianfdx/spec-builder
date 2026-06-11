"""
Prompt engine — reads .md files with YAML frontmatter, resolves variables,
and renders the final prompt body.

Frontmatter schema:
---
name: execute-spec
description: Runs a full spec in SDD mode
variables:
  - name: SPEC_NAME
    description: Spec folder name (e.g. 001-create-foundation)
    required: true
  - name: AGENT
    description: Target agent
    default: "claude-code"
agents: [claude-code, copilot, cursor, gemini-cli, generic]
---
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from sddkit.engines.template import render_string


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)", re.DOTALL)


@dataclass
class PromptVariable:
    name: str
    description: str = ""
    required: bool = False
    default: str | None = None


@dataclass
class PromptMeta:
    name: str
    description: str = ""
    variables: list[PromptVariable] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)
    body: str = ""


def parse_prompt(path: Path) -> PromptMeta:
    """Parse a prompt .md file into a PromptMeta object."""
    raw = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(raw)
    if not match:
        # No frontmatter — treat entire file as body
        return PromptMeta(name=path.stem, body=raw)

    front = yaml.safe_load(match.group(1)) or {}
    body = match.group(2).strip()

    variables = [
        PromptVariable(
            name=v["name"],
            description=v.get("description", ""),
            required=v.get("required", False),
            default=v.get("default"),
        )
        for v in front.get("variables", [])
    ]

    return PromptMeta(
        name=front.get("name", path.stem),
        description=front.get("description", ""),
        variables=variables,
        agents=front.get("agents", []),
        body=body,
    )


def render_prompt(meta: PromptMeta, overrides: dict[str, str]) -> str:
    """
    Resolve variable values and render the prompt body.

    Args:
        meta: Parsed prompt metadata.
        overrides: User-supplied variable values (--var KEY=VALUE).

    Returns:
        Rendered prompt string.

    Raises:
        ValueError: If a required variable is missing and has no default.
    """
    context: dict[str, str] = {}
    for var in meta.variables:
        if var.name in overrides:
            context[var.name] = overrides[var.name]
        elif var.default is not None:
            context[var.name] = var.default
        elif var.required:
            raise ValueError(
                f"Variable '{var.name}' is required but was not provided. "
                f"Use --var {var.name}=<value>"
            )

    return render_string(meta.body, context)
