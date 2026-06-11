"""
Agent resolver — detects which agent is currently active in a project
by inspecting known instruction files.
"""

from pathlib import Path
from sddkit.agents.registry import AGENTS, AgentConfig


def detect_agent(project_root: Path) -> AgentConfig | None:
    """
    Scan the project root for known instruction files and return
    the matching AgentConfig, or None if none is found.
    """
    for agent in AGENTS.values():
        target = project_root / agent.instruction_path
        if target.exists():
            return agent
    return None
