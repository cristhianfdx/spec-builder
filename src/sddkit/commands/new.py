"""
sdd new <feature-name> — create a new spec folder with spec.md, plan.md, tasks.md.

Usage:
  sdd new manage-users
  sdd new "User Authentication"
"""

from __future__ import annotations

import re
from pathlib import Path
from datetime import date

import typer
from rich.console import Console
from jinja2 import Environment, StrictUndefined

console = Console()


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", text.lower().strip()).strip("-")


def _next_number(specs_dir: Path) -> str:
    if not specs_dir.exists():
        return "001"
    existing = sorted(
        [d.name for d in specs_dir.iterdir() if d.is_dir() and re.match(r"^\d{3,}-", d.name)]
    )
    if not existing:
        return "001"
    last = int(existing[-1].split("-")[0])
    return f"{last + 1:03d}"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    console.print(f"  [green]created[/] {path.relative_to(Path.cwd())}")


def _render(template_path: Path, ctx: dict) -> str:
    env = Environment(undefined=StrictUndefined, keep_trailing_newline=True)
    return env.from_string(template_path.read_text(encoding="utf-8")).render(**ctx)


def _find_project_root(start: Path) -> Path:
    current = start
    for _ in range(10):
        if (current / ".specify").exists():
            return current
        current = current.parent
    return start


def new_command(
    name: str = typer.Argument(..., help="Feature name, e.g. 'manage-users' or 'User Authentication'"),
) -> None:
    """Create a new spec folder with spec.md, plan.md, and tasks.md."""
    from sddkit.engines.template import _templates_dir

    project_root = _find_project_root(Path.cwd())
    specs_dir = project_root / ".specify" / "specs"

    slug = _slugify(name)
    number = _next_number(specs_dir)
    folder_name = f"{number}-{slug}"
    spec_dir = specs_dir / folder_name

    if spec_dir.exists():
        console.print(f"[red]Spec folder already exists:[/] {spec_dir}")
        raise typer.Exit(1)

    tpl_root = _templates_dir()
    ctx = {
        "spec_name": name,
        "spec_number": number,
        "spec_slug": slug,
        "date": date.today().isoformat(),
    }

    console.print(f"\n[bold cyan]sdd new[/] — creating spec [bold]{folder_name}[/]\n")
    _write(spec_dir / "spec.md", _render(tpl_root / "spec.md.j2", ctx))
    _write(spec_dir / "plan.md", _render(tpl_root / "plan.md.j2", ctx))
    _write(spec_dir / "tasks.md", _render(tpl_root / "tasks.md.j2", ctx))

    console.print(f"\n[bold green]Done![/] Spec created at [cyan].specify/specs/{folder_name}/[/]")
    console.print("\nNext steps:")
    console.print("  1. Fill in [bold]spec.md[/] with acceptance criteria")
    console.print("  2. Define the technical approach in [bold]plan.md[/]")
    console.print("  3. Break down work into checkboxes in [bold]tasks.md[/]")
    console.print("  4. Point your agent at the spec and run it\n")
