"""
sdd use <agent> — install or switch the agent instruction file.
"""

from pathlib import Path
from datetime import date
import typer
from rich.console import Console
from rich.prompt import Confirm

from sddkit.agents.registry import get_agent, list_agents
from sddkit.engines.template import render

console = Console()


def use_command(
    agent: str = typer.Argument(..., help="Agent name (e.g. claude-code, copilot, cursor)"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing instruction file"),
) -> None:
    """Install or switch agent instruction file in the current project."""
    try:
        agent_cfg = get_agent(agent)
    except KeyError as e:
        console.print(f"[red]{e}[/]")
        console.print("\nAvailable agents:")
        for a in list_agents():
            console.print(f"  [cyan]{a.name}[/] — {a.display_name}")
        raise typer.Exit(1)

    project_root = Path.cwd()
    target = project_root / agent_cfg.instruction_path

    if target.exists() and not force:
        if not Confirm.ask(f"[yellow]{target}[/] already exists. Overwrite?"):
            raise typer.Abort()

    for extra in agent_cfg.extra_dirs:
        (project_root / extra).mkdir(parents=True, exist_ok=True)

    constitution = project_root / ".specify" / "memory" / "constitution.md"
    project_name = project_root.name
    stack = ""
    if constitution.exists():
        for line in constitution.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                project_name = line.lstrip("# ").strip()
                break

    ctx = {
        "project_name": project_name,
        "stack": stack,
        "agent": agent,
        "agent_display": agent_cfg.display_name,
        "date": date.today().isoformat(),
    }

    content = render(f"agents/{agent_cfg.template_file}", ctx)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")

    console.print(f"\n[bold green]Done![/] Agent instruction file written to [cyan]{target}[/]")
    console.print(f"Agent: [bold]{agent_cfg.display_name}[/]\n")
