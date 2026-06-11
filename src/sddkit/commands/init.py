"""
sdd init — initialize a new or existing project with SDD structure.

Usage:
  sdd init                              # interactive
  sdd init my-project                   # creates ./my-project/
  sdd init --here                       # initializes in current directory
  sdd init my-project --agent claude-code --profile full
"""

from __future__ import annotations

import re
import stat
from pathlib import Path
from datetime import date
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from jinja2 import Environment, StrictUndefined

from sddkit.agents.registry import list_agents, get_agent, AgentFile
from sddkit.engines.template import _templates_dir

console = Console()

PROFILES = ["basic", "standard", "full"]


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", text.lower().strip()).strip("-")


def _render(template_path: Path, ctx: dict) -> str:
    env = Environment(undefined=StrictUndefined, keep_trailing_newline=True)
    return env.from_string(template_path.read_text(encoding="utf-8")).render(**ctx)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    console.print(f"  [green]created[/] {path}")


def scaffold(project_root: Path, project_name: str, agent_name: str, profile: str) -> None:
    agent = get_agent(agent_name)
    ctx = {
        "project_name": project_name,
        "agent": agent_name,
        "agent_display": agent.display_name,
        "date": date.today().isoformat(),
    }

    tpl_root = _templates_dir()
    agent_tpl = tpl_root / "agents" / agent_name

    # .specify/memory/constitution.md
    _write(
        project_root / ".specify" / "memory" / "constitution.md",
        _render(tpl_root / "constitution.md.j2", ctx),
    )

    # First spec skeleton
    spec_dir = project_root / ".specify" / "specs" / "001-initial-setup"
    _write(spec_dir / "spec.md", _render(tpl_root / "spec.md.j2", {**ctx, "spec_name": "Initial Setup", "spec_number": "001"}))
    _write(spec_dir / "plan.md", _render(tpl_root / "plan.md.j2", {**ctx, "spec_name": "Initial Setup"}))
    _write(spec_dir / "tasks.md", _render(tpl_root / "tasks.md.j2", ctx))

    # .specify/prompts/ — sdd-format, raw copy (contain user-facing {{ }} variables)
    prompts_src = tpl_root / "prompts"
    prompts_dir = project_root / ".specify" / "prompts"
    for prompt_tpl in ["execute-spec.md.j2", "sync-agent.md.j2", "new-spec.md.j2"]:
        dest_name = prompt_tpl.replace(".j2", "")
        _write(prompts_dir / dest_name, (prompts_src / prompt_tpl).read_text(encoding="utf-8"))

    # Custom prompts placeholder
    custom_keep = prompts_dir / "custom" / ".gitkeep"
    custom_keep.parent.mkdir(parents=True, exist_ok=True)
    custom_keep.write_text("", encoding="utf-8")

    # .specify/scripts/
    scripts_src = tpl_root / "scripts"
    scripts_dir = project_root / ".specify" / "scripts"
    for script_tpl, executable in [
        ("new-spec.sh.j2",  True),
        ("new-spec.ps1.j2", False),
        ("validate.sh.j2",  True),
        ("validate.ps1.j2", False),
    ]:
        dest_name = script_tpl.replace(".j2", "")
        dest = scripts_dir / dest_name
        _write(dest, _render(scripts_src / script_tpl, ctx))
        if executable:
            dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    # Agent-specific files (profile-based)
    for af in agent.files_for_profile(profile):
        src = agent_tpl / af.src
        dst = project_root / af.dst

        if not src.exists():
            console.print(f"  [yellow]skipped[/] {af.dst} (template not found: {src})")
            continue

        content = src.read_text(encoding="utf-8") if af.raw else _render(src, ctx)
        _write(dst, content)

        if af.executable:
            dst.chmod(dst.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    # AGENTS.md (always, unless agent already generates it)
    agents_md = project_root / "AGENTS.md"
    if not agents_md.exists():
        generic_tpl = tpl_root / "agents" / "generic" / "AGENTS.md.j2"
        _write(agents_md, _render(generic_tpl, {**ctx, "specs": []}))

    # .gitignore
    gitignore = project_root / ".gitignore"
    if not gitignore.exists():
        _write(gitignore, "# spec-builder\n.specify/prompts/custom/\n")


def init_command(
    project: Optional[str] = typer.Argument(None, help="Project name / folder to create"),
    here: bool = typer.Option(False, "--here", help="Initialize in the current directory"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Agent to use"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile: basic, standard (default), full"),
) -> None:
    """Initialize a new or existing project with SDD structure."""

    console.print("\n[bold cyan]sdd init[/] — Spec-Driven Development setup\n")

    # Project root
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

    # Profile selection
    if not profile:
        agent_cfg = get_agent(agent)
        has_standard = bool(agent_cfg.standard)
        has_full = bool(agent_cfg.full)

        if has_full:
            console.print("\n[bold]Profile:[/]")
            console.print("  1. basic    — instruction file only")
            console.print("  2. standard — + hooks, skills, prompts")
            console.print("  3. full     — + sub-agents")
            p = Prompt.ask("\nChoose profile", default="2")
            profile = {"1": "basic", "2": "standard", "3": "full"}.get(p, "standard")
        elif has_standard:
            console.print("\n[bold]Profile:[/]")
            console.print("  1. basic    — instruction file only")
            console.print("  2. standard — + prompts / extra config")
            p = Prompt.ask("\nChoose profile", default="2")
            profile = {"1": "basic", "2": "standard"}.get(p, "standard")
        else:
            profile = "basic"

    if profile not in PROFILES:
        console.print(f"[red]Unknown profile '{profile}'.[/] Choose from: {', '.join(PROFILES)}")
        raise typer.Exit(1)

    # Confirm existing directory
    if project_root.exists() and any(project_root.iterdir()):
        if not Confirm.ask(f"\n[yellow]{project_root}[/] already exists. Initialize SDD here?"):
            raise typer.Abort()
    else:
        project_root.mkdir(parents=True, exist_ok=True)

    console.print(f"\n[bold]Scaffolding[/] {project_root} [dim]({agent} / {profile})[/]\n")
    scaffold(project_root, project_name, agent, profile)

    console.print(f"\n[bold green]Done![/] SDD project ready at [cyan]{project_root}[/]")
    console.print(f"Agent: [bold]{get_agent(agent).display_name}[/]  Profile: [bold]{profile}[/]")
    console.print("\nNext steps:")
    console.print("  1. Edit [bold].specify/memory/constitution.md[/] to define your project rules")
    console.print("  2. Run [bold]sdd new <feature-name>[/] to create your first real spec")
    console.print("  3. Open the project in your AI agent and start building\n")
