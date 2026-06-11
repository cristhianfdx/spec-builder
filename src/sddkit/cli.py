"""
sdd-kit — Spec-Driven Development toolkit CLI.
Entry point: `sdd`
"""

import typer
from rich.console import Console

from sddkit.commands.init import init_app
from sddkit.commands.new import new_app
from sddkit.commands.prompt import prompt_app
from sddkit.commands.use import use_command
from sddkit.commands.sync import sync_command
from sddkit.commands.check import check_command

app = typer.Typer(
    name="sdd",
    help="spec-builder — Spec-Driven Development toolkit",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()

app.add_typer(init_app, name="init", help="Initialize a new or existing project")
app.add_typer(new_app, name="new", help="Create a new spec")
app.add_typer(prompt_app, name="prompt", help="Manage and run custom prompts")

app.command("use")(use_command)
app.command("sync")(sync_command)
app.command("check")(check_command)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        console.print("[bold cyan]sdd-kit[/] — Spec-Driven Development toolkit")
        console.print("Run [bold]sdd --help[/] to see available commands.")


if __name__ == "__main__":
    app()
