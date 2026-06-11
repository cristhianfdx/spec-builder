"""
Agent registry — maps agent names to their instruction file locations
and any special install behavior.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AgentConfig:
    name: str
    display_name: str
    # Where the instruction file is written inside the project root
    instruction_path: str
    # Template file inside templates/agents/
    template_file: str
    # Slash-command / prompt path inside .specify/
    prompts_subdir: str = "prompts"
    # Extra paths to create (relative to project root)
    extra_dirs: list[str] = field(default_factory=list)


AGENTS: dict[str, AgentConfig] = {
    "claude-code": AgentConfig(
        name="claude-code",
        display_name="Claude Code",
        instruction_path="CLAUDE.md",
        template_file="claude-code.md.j2",
    ),
    "copilot": AgentConfig(
        name="copilot",
        display_name="GitHub Copilot",
        instruction_path=".github/copilot-instructions.md",
        template_file="copilot.md.j2",
        extra_dirs=[".github/prompts"],
    ),
    "cursor": AgentConfig(
        name="cursor",
        display_name="Cursor",
        instruction_path=".cursorrules",
        template_file="cursor.md.j2",
    ),
    "gemini-cli": AgentConfig(
        name="gemini-cli",
        display_name="Gemini CLI",
        instruction_path="GEMINI.md",
        template_file="gemini-cli.md.j2",
    ),
    "generic": AgentConfig(
        name="generic",
        display_name="Generic Agent",
        instruction_path="AGENTS.md",
        template_file="generic.md.j2",
    ),
}


def get_agent(name: str) -> AgentConfig:
    """Return AgentConfig by name. Raises KeyError if not found."""
    if name not in AGENTS:
        valid = ", ".join(AGENTS.keys())
        raise KeyError(f"Unknown agent '{name}'. Valid options: {valid}")
    return AGENTS[name]


def list_agents() -> list[AgentConfig]:
    return list(AGENTS.values())
