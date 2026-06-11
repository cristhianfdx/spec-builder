"""
sdd check — validate that the .specify/ structure is complete and consistent.
"""

from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

console = Console()


def check_command() -> None:
    """Validate the .specify/ structure and report any issues."""
    project_root = Path.cwd()
    specify_dir = project_root / ".specify"

    issues: list[str] = []
    ok: list[str] = []

    def check(condition: bool, success: str, failure: str) -> None:
        if condition:
            ok.append(success)
        else:
            issues.append(failure)

    check(specify_dir.exists(), ".specify/ directory exists", "Missing .specify/ — run sdd init")
    check(
        (specify_dir / "memory" / "constitution.md").exists(),
        "constitution.md present",
        "Missing .specify/memory/constitution.md",
    )

    specs_dir = specify_dir / "prompts"
    check(specs_dir.exists(), ".specify/prompts/ directory exists", "Missing .specify/prompts/")

    # Check each spec folder
    specs_root = specify_dir / "specs"
    if specs_root.exists():
        for spec_dir in sorted(d for d in specs_root.iterdir() if d.is_dir()):
            for required in ["spec.md", "plan.md", "tasks.md"]:
                f = spec_dir / required
                check(
                    f.exists(),
                    f"{spec_dir.name}/{required} present",
                    f"Missing {spec_dir.name}/{required}",
                )
    else:
        issues.append("No specs found in .specify/specs/ — run sdd new <feature>")

    # Summary
    console.print()
    for msg in ok:
        console.print(f"  [green]✓[/] {msg}")
    for msg in issues:
        console.print(f"  [red]✗[/] {msg}")

    if issues:
        console.print(f"\n[red bold]{len(issues)} issue(s) found.[/]\n")
        raise typer.Exit(1)
    else:
        console.print(f"\n[green bold]All checks passed.[/]\n")
