"""
sdd prompt — manage and run custom prompts.

Subcommands:
  sdd prompt list                                    # list all prompts (base + custom + copilot)
  sdd prompt new <name>                              # scaffold a new custom prompt (sdd format)
  sdd prompt new <name> --format copilot             # scaffold a new Copilot .prompt.md
  sdd prompt run <name> --var KEY=VALUE              # render and print a prompt
  sdd prompt show <name>                             # show prompt metadata
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from sddkit.engines.prompt import parse_prompt, render_prompt

prompt_app = typer.Typer(no_args_is_help=True)
console = Console()

# --- Prompt scaffold templates ---

CUSTOM_PROMPT_TEMPLATE = """\
---
name: {name}
description: {description}
variables:
  - name: SPEC_NAME
    description: Active spec folder name (e.g. 001-my-feature)
    required: true
  - name: AGENT
    description: Target AI agent
    default: "claude-code"
agents: [claude-code, copilot, cursor, gemini-cli, generic]
---

# Prompt: {title}

Configuration:
- SPEC_NAME: {{{{ SPEC_NAME }}}}
- AGENT: {{{{ AGENT }}}}

## Instructions

Read the following documents in order before taking any action:

1. `.specify/memory/constitution.md`
2. `.specify/specs/{{{{ SPEC_NAME }}}}/spec.md`
3. `.specify/specs/{{{{ SPEC_NAME }}}}/plan.md`
4. `.specify/specs/{{{{ SPEC_NAME }}}}/tasks.md`

## Rules

- Treat `.specify/` as the source of truth.
- Only implement what is described in `spec.md`.
- Follow `plan.md` for architecture decisions.
- Work task by task from `tasks.md`.
- Only work on pending checks (`- [ ]`) and mark them when truly complete.
- After each change, explain what task was completed and which files were modified.

## Expected output

1. What was built or modified.
2. Which files were created or changed.
3. Which tasks in `tasks.md` are now marked complete.
4. What remains pending (if any).
"""

COPILOT_PROMPT_TEMPLATE = """\
---
name: {name}
description: {description}
---

Configuration:
- SPEC_NAME: 001-initial-setup

Path resolution:
- SPEC_DIR = .specify/specs/{{SPEC_NAME}}
- SPEC_FILE = {{SPEC_DIR}}/spec.md
- PLAN_FILE = {{SPEC_DIR}}/plan.md
- TASKS_FILE = {{SPEC_DIR}}/tasks.md

Mandatory reading order:

1. .github/copilot-instructions.md
2. .specify/memory/constitution.md
3. {{SPEC_FILE}}
4. {{PLAN_FILE}}
5. {{TASKS_FILE}}

Use these documents as the sole source of truth for all work in this session.

Instructions:

<!-- Describe what Copilot should do in this prompt -->

Rules:

- Treat .specify/ as the source of truth.
- Only implement what is described in spec.md.
- Follow plan.md for architecture decisions.
- Work task by task from tasks.md.
- Only work on pending checks (- [ ]) and mark them when truly complete.
- After each change, explain what task was completed and which files were modified.

Required output when done:

1. What was built or modified.
2. Which files were created or changed.
3. Which tasks in {{TASKS_FILE}} are now marked complete.
4. What remains pending (if any).
"""


def _find_project_root(start: Path) -> Path:
    current = start
    for _ in range(10):
        if (current / ".specify").exists():
            return current
        current = current.parent
    return start


def _collect_prompts(project_root: Path) -> dict[str, Path]:
    """
    Return {key: path} for all prompts:
    - base:          .specify/prompts/*.md
    - custom:        .specify/prompts/custom/*.md   → key = "custom/<stem>"
    - copilot:       .github/prompts/*.prompt.md    → key = "copilot/<stem>"
    """
    prompts: dict[str, Path] = {}

    base_dir = project_root / ".specify" / "prompts"
    if base_dir.exists():
        for p in sorted(base_dir.glob("*.md")):
            prompts[p.stem] = p
    custom_dir = base_dir / "custom"
    if custom_dir.exists():
        for p in sorted(custom_dir.glob("*.md")):
            prompts[f"custom/{p.stem}"] = p

    # Copilot prompts (.github/prompts/*.prompt.md)
    copilot_dir = project_root / ".github" / "prompts"
    if copilot_dir.exists():
        for p in sorted(copilot_dir.glob("*.prompt.md")):
            prompts[f"copilot/{p.stem}"] = p

    return prompts


@prompt_app.command("list")
def prompt_list() -> None:
    """List all available prompts (base, custom, and copilot)."""
    project_root = _find_project_root(Path.cwd())
    prompts = _collect_prompts(project_root)

    if not prompts:
        console.print("[yellow]No prompts found.[/] Run [bold]sdd init[/] first.")
        raise typer.Exit()

    table = Table(title="Available prompts", show_lines=True)
    table.add_column("Name", style="cyan")
    table.add_column("Format")
    table.add_column("Description")
    table.add_column("Variables")

    for key, path in prompts.items():
        meta = parse_prompt(path)

        if key.startswith("copilot/"):
            fmt = "[yellow]copilot[/]"
            vars_str = "{SPEC_NAME}, {AGENT} (inline)"
        elif key.startswith("custom/"):
            fmt = "[green]custom[/]"
            vars_str = ", ".join(
                f"{v.name}{'*' if v.required else ''}" for v in meta.variables
            )
        else:
            fmt = "[dim]base[/]"
            vars_str = ", ".join(
                f"{v.name}{'*' if v.required else ''}" for v in meta.variables
            )

        table.add_row(key, fmt, meta.description, vars_str)

    console.print(table)
    console.print("\n[dim]* = required variable[/]")
    console.print("[dim]copilot prompts: edit SPEC_NAME directly in the file and use via Copilot Chat[/]\n")


@prompt_app.command("new")
def prompt_new(
    name: str = typer.Argument(..., help="Prompt name (slug, e.g. 'review-spec')"),
    description: str = typer.Option("", "--description", "-d", help="Short description"),
    fmt: str = typer.Option("sdd", "--format", "-f", help="Prompt format: 'sdd' (default) or 'copilot'"),
) -> None:
    """
    Scaffold a new custom prompt.

    sdd format  → .specify/prompts/custom/<name>.md   (Jinja2 variables, sdd prompt run)
    copilot     → .github/prompts/<name>.prompt.md    (VS Code Copilot Chat format)
    """
    project_root = _find_project_root(Path.cwd())
    title = name.replace("-", " ").title()
    desc = description or f"Custom prompt: {title}"

    if fmt == "copilot":
        dest_dir = project_root / ".github" / "prompts"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{name}.prompt.md"
        content = COPILOT_PROMPT_TEMPLATE.format(name=name, description=desc)
        label = "Copilot prompt"
        hint = "Edit SPEC_NAME in the file and use it via VS Code Copilot Chat (#<filename>)."
    else:
        dest_dir = project_root / ".specify" / "prompts" / "custom"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{name}.md"
        content = CUSTOM_PROMPT_TEMPLATE.format(name=name, title=title, description=desc)
        label = "sdd prompt"
        hint = "Use with: sdd prompt run custom/{name} --var SPEC_NAME=001-my-feature"

    if dest.exists():
        console.print(f"[red]Prompt already exists:[/] {dest}")
        raise typer.Exit(1)

    dest.write_text(content, encoding="utf-8", newline="\n")
    console.print(f"\n[bold green]Created[/] {label} at [cyan]{dest}[/]")
    console.print(f"{hint}\n")


@prompt_app.command("run")
def prompt_run(
    name: str = typer.Argument(..., help="Prompt name (e.g. 'execute-spec' or 'custom/review-spec')"),
    var: list[str] = typer.Option([], "--var", "-v", help="Variable override: KEY=VALUE"),
    copy: bool = typer.Option(False, "--copy", "-c", help="Copy output to clipboard"),
) -> None:
    """
    Render a prompt with variable substitution and print it.

    Only works with sdd-format prompts. Copilot prompts are edited directly.
    """
    project_root = _find_project_root(Path.cwd())
    prompts = _collect_prompts(project_root)

    if name not in prompts:
        console.print(f"[red]Prompt '{name}' not found.[/] Run [bold]sdd prompt list[/] to see available prompts.")
        raise typer.Exit(1)

    if name.startswith("copilot/"):
        console.print(
            f"[yellow]Copilot prompts are not rendered by sdd.[/]\n"
            f"Edit SPEC_NAME directly in [cyan]{prompts[name]}[/] and use it via VS Code Copilot Chat."
        )
        raise typer.Exit()

    overrides: dict[str, str] = {}
    for v in var:
        if "=" not in v:
            console.print(f"[red]Invalid --var format:[/] '{v}'. Use KEY=VALUE.")
            raise typer.Exit(1)
        k, val = v.split("=", 1)
        overrides[k.strip()] = val.strip()

    meta = parse_prompt(prompts[name])

    try:
        rendered = render_prompt(meta, overrides)
    except ValueError as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)

    console.rule(f"[bold cyan]{meta.name}[/]")
    console.print(rendered)
    console.rule()

    if copy:
        try:
            import subprocess
            import sys
            if sys.platform == "darwin":
                subprocess.run(["pbcopy"], input=rendered.encode(), check=True)
            elif sys.platform == "win32":
                subprocess.run(["clip"], input=rendered.encode(), check=True)
            else:
                subprocess.run(["xclip", "-selection", "clipboard"], input=rendered.encode(), check=True)
            console.print("\n[green]Copied to clipboard![/]")
        except Exception:
            console.print("\n[yellow]Could not copy to clipboard. Install xclip on Linux.[/]")


@prompt_app.command("show")
def prompt_show(
    name: str = typer.Argument(..., help="Prompt name"),
) -> None:
    """Show metadata and variables for a prompt."""
    project_root = _find_project_root(Path.cwd())
    prompts = _collect_prompts(project_root)

    if name not in prompts:
        console.print(f"[red]Prompt '{name}' not found.[/]")
        raise typer.Exit(1)

    meta = parse_prompt(prompts[name])
    is_copilot = name.startswith("copilot/")

    console.print(f"\n[bold cyan]{meta.name}[/]")
    console.print(f"[dim]{meta.description}[/]")

    if is_copilot:
        console.print(f"\nFormat: [yellow]copilot[/] — edit {{SPEC_NAME}} inline, use via VS Code Copilot Chat\n")
        return

    if meta.variables:
        table = Table(show_header=True)
        table.add_column("Variable", style="cyan")
        table.add_column("Required")
        table.add_column("Default")
        table.add_column("Description")
        for v in meta.variables:
            table.add_row(
                v.name,
                "[red]yes[/]" if v.required else "no",
                v.default or "—",
                v.description,
            )
        console.print(table)

    if meta.agents:
        console.print(f"\nSupported agents: [cyan]{', '.join(meta.agents)}[/]\n")
