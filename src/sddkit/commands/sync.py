"""
sdd sync — regenerate AGENTS.md from the current project state.
"""

from pathlib import Path
from datetime import date
import typer
from rich.console import Console
from sddkit.engines.template import render
from sddkit.agents.resolver import detect_agent

console = Console()


def sync_command() -> None:
    """Regenerate AGENTS.md by scanning .specify/ and the project structure."""
    project_root = Path.cwd()
    specify_dir = project_root / ".specify"

    if not specify_dir.exists():
        console.print("[red]No .specify/ directory found.[/] Run [bold]sdd init[/] first.")
        raise typer.Exit(1)

    agent_cfg = detect_agent(project_root)
    agent_name = agent_cfg.name if agent_cfg else "generic"
    agent_display = agent_cfg.display_name if agent_cfg else "Generic Agent"

    # Collect specs
    specs_dir = specify_dir / "specs"
    specs = []
    if specs_dir.exists():
        for spec_dir in sorted(d for d in specs_dir.iterdir() if d.is_dir()):
            spec_file = spec_dir / "spec.md"
            tasks_file = spec_dir / "tasks.md"
            total = done = 0
            if tasks_file.exists():
                for line in tasks_file.read_text(encoding="utf-8").splitlines():
                    if line.strip().startswith("- ["):
                        total += 1
                        if line.strip().startswith("- [x]"):
                            done += 1
            status = "complete" if total > 0 and done == total else "in progress" if done > 0 else "pending"
            specs.append({
                "folder": spec_dir.name,
                "total_tasks": total,
                "done_tasks": done,
                "status": status,
            })

    constitution = specify_dir / "memory" / "constitution.md"
    project_name = project_root.name
    if constitution.exists():
        for line in constitution.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                project_name = line.lstrip("# ").strip()
                break

    ctx = {
        "project_name": project_name,
        "agent": agent_name,
        "agent_display": agent_display,
        "specs": specs,
        "date": date.today().isoformat(),
    }

    content = render("agents/generic.md.j2", ctx)
    dest = project_root / "AGENTS.md"
    dest.write_text(content, encoding="utf-8", newline="\n")
    console.print(f"\n[bold green]Synced[/] AGENTS.md — {len(specs)} spec(s) indexed.\n")
