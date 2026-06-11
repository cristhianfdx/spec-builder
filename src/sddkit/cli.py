"""
sdd-kit — Spec-Driven Development toolkit CLI.
Entry point: `sdd`
"""

import typer
from rich.console import Console

from sddkit.commands.init import init_command
from sddkit.commands.new import new_command
from sddkit.commands.prompt import prompt_app
from sddkit.commands.agent import agent_app
from sddkit.commands.skill import skill_app
from sddkit.commands.hook import hook_app
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

app.command("init")(init_command)
app.command("new")(new_command)
app.add_typer(prompt_app, name="prompt",  help="Manage and run prompts")
app.add_typer(agent_app,  name="agent",   help="Manage sub-agents")
app.add_typer(skill_app,  name="skill",   help="Manage skills")
app.add_typer(hook_app,   name="hook",    help="Manage hooks (Claude Code)")
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
