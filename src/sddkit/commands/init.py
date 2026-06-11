"""
sdd init — initialize a new or existing project with SDD structure.

Usage:
  sdd init                  # interactive: asks for project name, creates subfolder
  sdd init my-project       # creates ./my-project/ with full SDD structure
  sdd init --here           # initializes SDD in the current directory
"""

from __future__ import annotations

import re
import stat
from pathlib import Path
from datetime import date

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm

from sddkit.agents.registry import list_agents, get_agent
from sddkit.engines.template import render, _templates_dir

init_app = typer.Typer(invoke_without_command=True, no_args_is_help=False)
console = Console()


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", text.lower().strip()).strip("-")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    console.print(f"  [green]created[/] {path}")


def scaffold(project_root: Path, project_name: str, agent_name: str) -> None:
    """Generate the full .specify/ structure and agent instruction file."""
    agent = get_agent(agent_name)
    ctx = {
        "project_name": project_name,
        "agent": agent_name,
        "agent_display": agent.display_name,
        "date": date.today().isoformat(),
    }

    # --- .specify/memory/constitution.md ---
    _write(project_root / ".specify" / "memory" / "constitution.md", render("constitution.md.j2", ctx))

    # --- First spec skeleton ---
    spec_dir = project_root / ".specify" / "specs" / "001-initial-setup"
    _write(spec_dir / "spec.md", render("spec.md.j2", {**ctx, "spec_name": "Initial Setup", "spec_number": "001"}))
    _write(spec_dir / "plan.md", render("plan.md.j2", {**ctx, "spec_name": "Initial Setup"}))
    _write(spec_dir / "tasks.md", render("tasks.md.j2", ctx))

    # --- .specify/prompts/ (base prompts) ---
    # Prompts are copied as raw text — they contain user-facing Jinja2 variables
    # ({{ SPEC_NAME }}, {{ AGENT }}) resolved at runtime via `sdd prompt run`,
    # not at scaffold time.
    prompts_src = _templates_dir() / "prompts"
    prompts_dir = project_root / ".specify" / "prompts"
    for prompt_tpl in ["execute-spec.md.j2", "sync-agent.md.j2", "new-spec.md.j2"]:
        dest_name = prompt_tpl.replace(".j2", "")
        raw = (prompts_src / prompt_tpl).read_text(encoding="utf-8")
        _write(prompts_dir / dest_name, raw)

    # Custom prompts directory (empty, ready for user)
    custom_keep = prompts_dir / "custom" / ".gitkeep"
    custom_keep.parent.mkdir(parents=True, exist_ok=True)
    custom_keep.write_text("", encoding="utf-8")

    # --- .specify/scripts/ ---
    scripts_dir = project_root / ".specify" / "scripts"
    _write(scripts_dir / "new-spec.sh", render("scripts/new-spec.sh.j2", ctx))
    _write(scripts_dir / "new-spec.ps1", render("scripts/new-spec.ps1.j2", ctx))
    _write(scripts_dir / "validate.sh", render("scripts/validate.sh.j2", ctx))
    _write(scripts_dir / "validate.ps1", render("scripts/validate.ps1.j2", ctx))

    # Make shell scripts executable on Unix
    for sh in [scripts_dir / "new-spec.sh", scripts_dir / "validate.sh"]:
        sh.chmod(sh.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    # --- Agent instruction file ---
    for extra in agent.extra_dirs:
        (project_root / extra).mkdir(parents=True, exist_ok=True)
    _write(project_root / agent.instruction_path, render(f"agents/{agent.template_file}", ctx))

    # --- AGENTS.md (generated guide, updated later by sdd sync) ---
    agents_md = project_root / "AGENTS.md"
    if not agents_md.exists():
        _write(agents_md, render("agents/generic.md.j2", {**ctx, "specs": []}))

    # --- .gitignore ---
    gitignore = project_root / ".gitignore"
    if not gitignore.exists():
        _write(gitignore, "# spec-builder\n.specify/prompts/custom/\n")


@init_app.callback(invoke_without_command=True)
def init(
    ctx: typer.Context,
    project: str = typer.Argument(None, help="Project name / folder to create"),
    here: bool = typer.Option(False, "--here", help="Initialize in the current directory"),
    agent: str = typer.Option(None, "--agent", "-a", help="Agent to use (skips interactive prompt)"),
) -> None:
    """Initialize a new or existing project with SDD structure."""
    if ctx.invoked_subcommand is not None:
        return

    console.print("\n[bold cyan]sdd init[/] — Spec-Driven Development setup\n")

    # Determine project root
    if here:
        project_root = Path.cwd()
        project_name = project or project_root.name
    elif project:
        project_root = Path.cwd() / project
        project_name = project
    else:
        project_name = Prompt.ask("[bold]Project name[/]")
        project_root = Path.cwd() / _slugify(project_name)

    # Agent selection
    agents = list_agents()
    if not agent:
        console.print("\n[bold]Available agents:[/]")
        for i, a in enumerate(agents, 1):
            console.print(f"  {i}. {a.display_name} ({a.name})")
        choice = Prompt.ask("\nChoose agent", default="1")
        try:
            agent = agents[int(choice) - 1].name
        except (ValueError, IndexError):
            agent = "generic"

    # Confirm if project_root already has files
    if project_root.exists() and any(project_root.iterdir()):
        if not Confirm.ask(f"\n[yellow]{project_root}[/] already exists. Initialize SDD here?"):
            raise typer.Abort()
    else:
        project_root.mkdir(parents=True, exist_ok=True)

    console.print(f"\n[bold]Scaffolding[/] {project_root}\n")
    scaffold(project_root, project_name, agent)

    console.print(f"\n[bold green]Done![/] Your SDD project is ready at [cyan]{project_root}[/]")
    console.print("\nNext steps:")
    console.print(f"  1. Edit [bold].specify/memory/constitution.md[/] to define your project rules")
    console.print(f"  2. Run [bold]sdd new <feature-name>[/] to create your first real spec")
    console.print(f"  3. Open the project in your AI agent and start building\n")
