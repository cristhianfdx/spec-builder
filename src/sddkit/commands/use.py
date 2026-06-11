"""
sdd use <agent> — install or switch the agent instruction files.

Usage:
  sdd use claude-code
  sdd use claude-code --profile full
  sdd use copilot --profile standard
"""

from pathlib import Path
from datetime import date
import stat
import typer
from rich.console import Console
from rich.prompt import Confirm

from sddkit.agents.registry import get_agent, list_agents, AgentFile
from sddkit.engines.template import _templates_dir

console = Console()

PROFILES = ["basic", "standard", "full"]


def _render(template_path: Path, ctx: dict) -> str:
    from jinja2 import Environment, StrictUndefined
    env = Environment(undefined=StrictUndefined, keep_trailing_newline=True)
    return env.from_string(template_path.read_text(encoding="utf-8")).render(**ctx)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    console.print(f"  [green]written[/] {path}")


def use_command(
    agent: str = typer.Argument(..., help="Agent name (e.g. claude-code, copilot, cursor)"),
    profile: str = typer.Option("standard", "--profile", "-p", help="Profile: basic, standard, full"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files without asking"),
) -> None:
    """Install or switch agent instruction files in the current project."""
    try:
        agent_cfg = get_agent(agent)
    except KeyError as e:
        console.print(f"[red]{e}[/]")
        console.print("\nAvailable agents:")
        for a in list_agents():
            console.print(f"  [cyan]{a.name}[/] — {a.display_name}")
        raise typer.Exit(1)

    if profile not in PROFILES:
        console.print(f"[red]Unknown profile '{profile}'.[/] Choose from: {', '.join(PROFILES)}")
        raise typer.Exit(1)

    project_root = Path.cwd()
    tpl_root = _templates_dir()
    agent_tpl = tpl_root / "agents" / agent

    constitution = project_root / ".specify" / "memory" / "constitution.md"
    project_name = project_root.name
    if constitution.exists():
        for line in constitution.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                project_name = line.lstrip("# ").strip()
                break

    ctx = {
        "project_name": project_name,
        "agent": agent,
        "agent_display": agent_cfg.display_name,
        "date": date.today().isoformat(),
    }

    files: list[AgentFile] = agent_cfg.files_for_profile(profile)

    console.print(f"\n[bold cyan]sdd use[/] {agent} / {profile}\n")

    for af in files:
        src = agent_tpl / af.src
        dst = project_root / af.dst

        if not src.exists():
            console.print(f"  [yellow]skipped[/] {af.dst} (template not found)")
            continue

        if dst.exists() and not force:
            if not Confirm.ask(f"  [yellow]{af.dst}[/] already exists. Overwrite?"):
                continue

        content = src.read_text(encoding="utf-8") if af.raw else _render(src, ctx)
        _write(dst, content)

        if af.executable:
            dst.chmod(dst.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    console.print(f"\n[bold green]Done![/] Agent: [bold]{agent_cfg.display_name}[/]  Profile: [bold]{profile}[/]\n")
