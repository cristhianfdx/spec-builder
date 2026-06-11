"""
sdd prompt — manage and run custom prompts.

Subcommands:
  sdd prompt list                          # list all prompts (base + custom)
  sdd prompt new <name>                    # scaffold a new custom prompt
  sdd prompt run <name> --var KEY=VALUE    # render and print a prompt
  sdd prompt show <name>                   # show prompt metadata
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from sddkit.engines.prompt import parse_prompt, render_prompt, PromptMeta

prompt_app = typer.Typer(no_args_is_help=True)
console = Console()

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


def _find_project_root(start: Path) -> Path:
    current = start
    for _ in range(10):
        if (current / ".specify").exists():
            return current
        current = current.parent
    return start


def _collect_prompts(project_root: Path) -> dict[str, Path]:
    """Return {name: path} for all prompts (base + custom)."""
    prompts: dict[str, Path] = {}
    base_dir = project_root / ".specify" / "prompts"
    if base_dir.exists():
        for p in sorted(base_dir.glob("*.md")):
            prompts[p.stem] = p
    custom_dir = base_dir / "custom"
    if custom_dir.exists():
        for p in sorted(custom_dir.glob("*.md")):
            prompts[f"custom/{p.stem}"] = p
    return prompts


@prompt_app.command("list")
def prompt_list() -> None:
    """List all available prompts (base and custom)."""
    project_root = _find_project_root(Path.cwd())
    prompts = _collect_prompts(project_root)

    if not prompts:
        console.print("[yellow]No prompts found.[/] Run [bold]sdd init[/] first.")
        raise typer.Exit()

    table = Table(title="Available prompts", show_lines=True)
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Variables")
    table.add_column("Agents")

    for key, path in prompts.items():
        meta = parse_prompt(path)
        vars_str = ", ".join(
            f"{v.name}{'*' if v.required else ''}" for v in meta.variables
        )
        agents_str = ", ".join(meta.agents) if meta.agents else "all"
        tag = "[dim](base)[/]" if "custom" not in key else "[green](custom)[/]"
        table.add_row(f"{key} {tag}", meta.description, vars_str, agents_str)

    console.print(table)
    console.print("\n[dim]* = required variable[/]")


@prompt_app.command("new")
def prompt_new(
    name: str = typer.Argument(..., help="Prompt name (slug, e.g. 'review-spec')"),
    description: str = typer.Option("", "--description", "-d", help="Short description"),
) -> None:
    """Scaffold a new custom prompt in .specify/prompts/custom/."""
    project_root = _find_project_root(Path.cwd())
    custom_dir = project_root / ".specify" / "prompts" / "custom"
    custom_dir.mkdir(parents=True, exist_ok=True)

    dest = custom_dir / f"{name}.md"
    if dest.exists():
        console.print(f"[red]Prompt already exists:[/] {dest}")
        raise typer.Exit(1)

    title = name.replace("-", " ").title()
    content = CUSTOM_PROMPT_TEMPLATE.format(
        name=name,
        title=title,
        description=description or f"Custom prompt: {title}",
    )
    dest.write_text(content, encoding="utf-8", newline="\n")
    console.print(f"\n[bold green]Created[/] custom prompt at [cyan]{dest}[/]")
    console.print(f"Edit the file to customize variables and instructions.\n")


@prompt_app.command("run")
def prompt_run(
    name: str = typer.Argument(..., help="Prompt name (e.g. 'execute-spec' or 'custom/review-spec')"),
    var: list[str] = typer.Option([], "--var", "-v", help="Variable override: KEY=VALUE"),
    copy: bool = typer.Option(False, "--copy", "-c", help="Copy output to clipboard"),
) -> None:
    """Render a prompt with variable substitution and print it."""
    project_root = _find_project_root(Path.cwd())
    prompts = _collect_prompts(project_root)

    if name not in prompts:
        console.print(f"[red]Prompt '{name}' not found.[/] Run [bold]sdd prompt list[/] to see available prompts.")
        raise typer.Exit(1)

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
            import subprocess, sys
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

    console.print(f"\n[bold cyan]{meta.name}[/]")
    console.print(f"[dim]{meta.description}[/]\n")

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
