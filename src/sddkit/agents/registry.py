"""
Agent registry — defines all supported AI coding agents, their instruction
file locations, and the files generated per profile level.

Profile levels:
  basic    — instruction file only (always generated)
  standard — basic + hooks/skills/prompts (default)
  full     — standard + sub-agents / extended config

Each AgentFile describes one file to generate:
  - src: template path relative to templates/agents/<agent-name>/
  - dst: destination path relative to project root
  - raw: if True, copy as-is without Jinja2 rendering
  - executable: if True, chmod +x on Unix after writing
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentFile:
    src: str
    dst: str
    raw: bool = False
    executable: bool = False


@dataclass
class AgentConfig:
    name: str
    display_name: str
    basic: list[AgentFile] = field(default_factory=list)
    standard: list[AgentFile] = field(default_factory=list)
    full: list[AgentFile] = field(default_factory=list)

    def files_for_profile(self, profile: str) -> list[AgentFile]:
        files = list(self.basic)
        if profile in ("standard", "full"):
            files += self.standard
        if profile == "full":
            files += self.full
        return files

    @property
    def instruction_path(self) -> str:
        return self.basic[0].dst if self.basic else "AGENTS.md"

    @property
    def extra_dirs(self) -> list[str]:
        dirs = set()
        for f in self.basic + self.standard + self.full:
            parent = "/".join(f.dst.split("/")[:-1])
            if parent:
                dirs.add(parent)
        return sorted(dirs)


AGENTS: dict[str, AgentConfig] = {

    # ── Claude Code ───────────────────────────────────────────────────────────
    "claude-code": AgentConfig(
        name="claude-code",
        display_name="Claude Code",
        basic=[
            AgentFile("CLAUDE.md.j2",           "CLAUDE.md"),
            AgentFile("settings.json.j2",        ".claude/settings.json"),
        ],
        standard=[
            AgentFile("hooks/pre-edit.sh.j2",   ".claude/hooks/pre-edit.sh",  executable=True),
            AgentFile("hooks/pre-edit.ps1.j2",  ".claude/hooks/pre-edit.ps1"),
            AgentFile("hooks/post-edit.sh.j2",  ".claude/hooks/post-edit.sh", executable=True),
            AgentFile("hooks/post-edit.ps1.j2", ".claude/hooks/post-edit.ps1"),
            AgentFile("hooks/stop.sh.j2",       ".claude/hooks/stop.sh",      executable=True),
            AgentFile("hooks/stop.ps1.j2",      ".claude/hooks/stop.ps1"),
            AgentFile("skills/run-tests.md.j2", ".claude/skills/run-tests.md"),
            AgentFile("skills/lint.md.j2",      ".claude/skills/lint.md"),
        ],
        full=[
            AgentFile("agents/reviewer.md.j2",   ".claude/agents/reviewer.md"),
            AgentFile("agents/debugger.md.j2",   ".claude/agents/debugger.md"),
            AgentFile("agents/scaffolder.md.j2", ".claude/agents/scaffolder.md"),
        ],
    ),

    # ── GitHub Copilot ────────────────────────────────────────────────────────
    "copilot": AgentConfig(
        name="copilot",
        display_name="GitHub Copilot",
        basic=[
            AgentFile("copilot-instructions.md.j2", ".github/copilot-instructions.md"),
        ],
        standard=[
            AgentFile("prompts/execute-spec.prompt.md.j2",        ".github/prompts/execute-spec.prompt.md",        raw=True),
            AgentFile("prompts/sync-agent.prompt.md.j2",          ".github/prompts/sync-agent.prompt.md",          raw=True),
            AgentFile("prompts/new-spec.prompt.md.j2",            ".github/prompts/new-spec.prompt.md",            raw=True),
            AgentFile("prompts/update-constitution.prompt.md.j2", ".github/prompts/update-constitution.prompt.md", raw=True),
            AgentFile("prompts/update-spec.prompt.md.j2",         ".github/prompts/update-spec.prompt.md",         raw=True),
            AgentFile("prompts/update-plan.prompt.md.j2",         ".github/prompts/update-plan.prompt.md",         raw=True),
            AgentFile("prompts/update-tasks.prompt.md.j2",        ".github/prompts/update-tasks.prompt.md",        raw=True),
        ],
        full=[],
    ),

    # ── Cursor ────────────────────────────────────────────────────────────────
    "cursor": AgentConfig(
        name="cursor",
        display_name="Cursor",
        basic=[
            AgentFile(".cursorrules.j2", ".cursorrules"),
        ],
        standard=[
            AgentFile("rules/sdd.mdc.j2", ".cursor/rules/sdd.mdc"),
        ],
        full=[],
    ),

    # ── Gemini CLI ────────────────────────────────────────────────────────────
    "gemini-cli": AgentConfig(
        name="gemini-cli",
        display_name="Gemini CLI",
        basic=[
            AgentFile("GEMINI.md.j2", "GEMINI.md"),
        ],
        standard=[
            AgentFile("GEMINI_TOOLS.md.j2", "GEMINI_TOOLS.md"),
        ],
        full=[],
    ),

    # ── Windsurf ──────────────────────────────────────────────────────────────
    "windsurf": AgentConfig(
        name="windsurf",
        display_name="Windsurf",
        basic=[
            AgentFile(".windsurfrules.j2", ".windsurfrules"),
        ],
        standard=[],
        full=[],
    ),

    # ── Aider ─────────────────────────────────────────────────────────────────
    "aider": AgentConfig(
        name="aider",
        display_name="Aider",
        basic=[
            AgentFile(".aider.conf.yml.j2", ".aider.conf.yml"),
            AgentFile("CONVENTIONS.md.j2",  "CONVENTIONS.md"),
        ],
        standard=[],
        full=[],
    ),

    # ── Generic ───────────────────────────────────────────────────────────────
    "generic": AgentConfig(
        name="generic",
        display_name="Generic Agent",
        basic=[
            AgentFile("AGENTS.md.j2", "AGENTS.md"),
        ],
        standard=[],
        full=[],
    ),
}


def get_agent(name: str) -> AgentConfig:
    if name not in AGENTS:
        valid = ", ".join(AGENTS.keys())
        raise KeyError(f"Unknown agent '{name}'. Valid options: {valid}")
    return AGENTS[name]


def list_agents() -> list[AgentConfig]:
    return list(AGENTS.values())
