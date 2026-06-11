# spec-builder

A lightweight, agent-agnostic toolkit for **Spec-Driven Development (SDD)**.

Instead of prompting your AI agent with "build me X" and hoping for the best, spec-builder gives you a structured, repeatable workflow:

```
constitution.md → spec.md → plan.md → tasks.md → code
```

Works with Claude Code, GitHub Copilot, Cursor, Gemini CLI, Windsurf, Aider, or any agent that reads Markdown files.

---

## Why spec-builder?

AI coding agents are literal-minded. They build exactly what you describe — not what you meant. spec-builder forces you to describe it precisely before the agent touches a single file.

Key differences from [spec-kit](https://github.com/github/spec-kit):

| | spec-kit | spec-builder |
|---|---|---|
| Prompts | Static per agent | Custom with variables + frontmatter |
| Update workflow | Not available | `update-spec`, `update-plan`, `update-tasks` prompts |
| Scripts | Bash only | `.sh` + `.ps1` generated in parallel |
| Platform | Mac / Linux | Mac, Linux, Windows |
| Agent profiles | One size fits all | `basic` / `standard` / `full` per agent |
| Sub-agents | Not available | Reviewer, Debugger, Scaffolder + custom |
| Skills | Not available | Built-in + custom, `/skill <name>` |
| Hooks | Not available | `pre-edit`, `post-edit`, `stop` + custom |
| Prompt runner | Not available | `sdd prompt run` renders to stdout or clipboard |

---

## Requirements

- **Python 3.11+**
- **[uv](https://github.com/astral-sh/uv)**

### Install Python

| Platform | Instructions |
|---|---|
| **macOS** | `brew install python@3.11` or [python.org](https://www.python.org/downloads/) |
| **Linux** | `sudo apt install python3.11` · `sudo dnf install python3.11` |
| **Windows** | [python.org](https://www.python.org/downloads/) — check "Add Python to PATH" |

### Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Installation

```bash
uv tool install git+https://github.com/cristhianfdx/spec-builder.git
```

Verify: `sdd --help`

### Update

```bash
uv tool install git+https://github.com/cristhianfdx/spec-builder.git --force
```

### Uninstall

```bash
uv tool uninstall spec-builder
```

---

## Quick Start

```bash
# New project — fully interactive
sdd init my-project

# New project — skip all prompts
sdd init my-project --agent claude-code --profile full

# Existing repo
cd my-repo
sdd init --here --agent copilot --profile standard

# Create a spec for a feature
sdd new user-authentication

# Render a prompt and copy to clipboard
sdd prompt run execute-spec --var SPEC_NAME=001-user-authentication --copy

# Validate structure
sdd check
```

---

## How to use it — practical workflow

### Starting a new task in an existing project

```bash
# 1. Initialize SDD (once per project)
cd my-project
sdd init --here --agent claude-code --profile full

# 2. Edit the constitution — define your stack, patterns, constraints
#    .specify/memory/constitution.md

# 3. Create a spec for your task
sdd new payment-refunds

# 4. Fill in the three files:
#    .specify/specs/002-payment-refunds/spec.md   → acceptance criteria
#    .specify/specs/002-payment-refunds/plan.md   → technical decisions
#    .specify/specs/002-payment-refunds/tasks.md  → atomic checkbox list

# 5. Run it with your agent
sdd prompt run execute-spec --var SPEC_NAME=002-payment-refunds --copy
# Paste into Claude Code / Copilot Chat
```

### Updating a spec mid-implementation

```bash
# A new requirement appeared — update the spec criteria
sdd prompt run update-spec \
  --var SPEC_NAME=002-payment-refunds \
  --var CHANGE_REQUEST="add support for partial refunds" --copy

# Architecture changed — update the technical plan
sdd prompt run update-plan \
  --var SPEC_NAME=002-payment-refunds \
  --var CHANGE_REQUEST="use async queue instead of direct call" --copy

# New tasks needed — add without touching completed ones
sdd prompt run update-tasks \
  --var SPEC_NAME=002-payment-refunds \
  --var CHANGE_REQUEST="add validation task for partial amount" --copy
```

### Architectural change that affects the whole project

```bash
# 1. Update the constitution first
sdd prompt run update-constitution \
  --var CHANGE_REQUEST="add Redis as cache layer, prohibit direct DB calls from controllers" --copy

# 2. Then create specs for the affected features
sdd new redis-cache-integration
```

### Rule of thumb

If you need to explain context to your agent in chat, that context belongs in `constitution.md` or `spec.md`. A well-written spec should make `execute-spec` self-sufficient — no additional explanation needed.

---

## Commands

### `sdd init`

Initialize a new or existing project.

```bash
sdd init                                                   # fully interactive
sdd init my-project                                        # creates ./my-project/
sdd init --here                                            # current directory
sdd init my-project --agent claude-code --profile full     # non-interactive
```

| Option | Description |
|---|---|
| `--here` | Initialize in the current directory |
| `--agent`, `-a` | Agent name (see supported agents) |
| `--profile`, `-p` | `basic`, `standard` (default), or `full` |

Generated structure:

```
my-project/
├── .specify/
│   ├── memory/
│   │   └── constitution.md       # Immutable rules — edit this first
│   ├── specs/
│   │   └── 001-initial-setup/
│   │       ├── spec.md           # What to build (acceptance criteria)
│   │       ├── plan.md           # How to build it (technical decisions)
│   │       └── tasks.md          # Executable checklist
│   ├── prompts/                  # All prompts, ready to use
│   │   ├── execute-spec.md
│   │   ├── new-spec.md
│   │   ├── sync-agent.md
│   │   ├── update-constitution.md
│   │   ├── update-spec.md
│   │   ├── update-plan.md
│   │   ├── update-tasks.md
│   │   └── custom/               # Your custom prompts
│   └── scripts/
│       ├── new-spec.sh / .ps1    # Create spec from terminal
│       └── validate.sh / .ps1   # Validate structure
├── AGENTS.md                     # Agent guide (regenerated by sdd sync)
└── [agent-specific files]        # Varies by agent — see below
```

---

### `sdd new <feature-name>`

Create a new spec folder.

```bash
sdd new manage-users
sdd new "Payment Processing"      # spaces are auto-slugified
```

Auto-numbers specs: `001-manage-users`, `002-payment-processing`, etc.

---

### `sdd prompt`

Manage and run prompts.

```bash
sdd prompt list                                                      # list all prompts
sdd prompt new my-prompt                                             # scaffold custom prompt (sdd format)
sdd prompt new my-prompt --format copilot                            # scaffold Copilot .prompt.md
sdd prompt run execute-spec --var SPEC_NAME=001-my-feature           # render to stdout
sdd prompt run execute-spec --var SPEC_NAME=001-my-feature --copy    # copy to clipboard
sdd prompt show execute-spec                                         # show metadata + variables
```

**Built-in prompts:**

| Prompt | Variables | Description |
|---|---|---|
| `execute-spec` | `SPEC_NAME*`, `AGENT` | Run a full spec through the SDD workflow |
| `new-spec` | `FEATURE_NAME*`, `AGENT` | Create a new spec via your agent |
| `sync-agent` | `AGENT` | Regenerate AGENTS.md |
| `update-constitution` | `CHANGE_REQUEST*`, `AGENT` | Update the project constitution |
| `update-spec` | `SPEC_NAME*`, `CHANGE_REQUEST*`, `AGENT` | Update spec.md (criteria, status, scope) |
| `update-plan` | `SPEC_NAME*`, `CHANGE_REQUEST*`, `AGENT` | Update plan.md (decisions, architecture) |
| `update-tasks` | `SPEC_NAME*`, `CHANGE_REQUEST*`, `AGENT` | Update tasks.md without touching completed |

`*` = required

**Custom prompts** live in `.specify/prompts/custom/` and use YAML frontmatter:

```markdown
---
name: my-prompt
description: Does something useful
variables:
  - name: SPEC_NAME
    required: true
  - name: AGENT
    default: "claude-code"
agents: [claude-code, copilot]
---

Read `.specify/specs/{{ SPEC_NAME }}/spec.md` and do the thing.
```

---

### `sdd agent`

Manage sub-agents (Claude Code: `/agent <name>`; others: paste as context).

```bash
sdd agent list                                                  # list all agents
sdd agent new tester --description "Generates tests from spec"  # scaffold custom agent
sdd agent edit reviewer                                         # open in $EDITOR
sdd agent show debugger                                         # print content
```

**Built-in agents** (generated with `--profile full`):

| Agent | Invoke | Description |
|---|---|---|
| `reviewer` | `/agent reviewer` | Reviews code against spec acceptance criteria |
| `debugger` | `/agent debugger` | Diagnoses errors in the context of the active spec |
| `scaffolder` | `/agent scaffolder` | Generates file structure from spec + plan |

Custom agents go in `.claude/agents/custom/`.

---

### `sdd skill`

Manage skills (Claude Code: `/skill <name>`; others: paste as context).

```bash
sdd skill list                                                       # list all skills
sdd skill new check-types --description "Run type checker"           # scaffold custom skill
sdd skill edit lint                                                   # open in $EDITOR
sdd skill show run-tests                                             # print content
```

**Built-in skills** (generated with `--profile standard`):

| Skill | Invoke | Description |
|---|---|---|
| `run-tests` | `/skill run-tests` | Detects and runs the appropriate test runner |
| `lint` | `/skill lint` | Detects and runs the appropriate linter/formatter |

Custom skills go in `.claude/skills/custom/`.

---

### `sdd hook`

Manage Claude Code hooks in `.claude/hooks/`.

```bash
sdd hook list                           # list all hooks
sdd hook new post-tool-use              # scaffold a new hook (.sh + .ps1)
sdd hook edit pre-edit                  # open .sh in $EDITOR
sdd hook edit pre-edit --platform ps1  # open .ps1 in $EDITOR
sdd hook show stop                      # print hook content
```

**Built-in hooks** (generated with `--profile standard`):

| Hook | Trigger | Default behavior |
|---|---|---|
| `pre-edit` | Before any file edit | Warns if no pending tasks exist |
| `post-edit` | After any file edit | Placeholder for linter/formatter |
| `stop` | End of session | Prints pending/completed task summary |

Hooks receive event JSON via stdin. Exit `0` to continue, exit `1` to block with a message to stderr.

---

### `sdd use <agent>`

Install or switch agent instruction files in an existing project.

```bash
sdd use claude-code --profile full
sdd use copilot --profile standard
sdd use cursor
sdd use gemini-cli
sdd use windsurf
sdd use aider
sdd use generic
```

---

### `sdd sync`

Regenerate `AGENTS.md` by scanning `.specify/` and indexing all specs.

```bash
sdd sync
```

---

### `sdd check`

Validate that the `.specify/` structure is complete and consistent.

```bash
sdd check
```

---

## Supported Agents

### Claude Code

| Profile | Generated files |
|---|---|
| `basic` | `CLAUDE.md` + `.claude/settings.json` |
| `standard` | + hooks (`pre-edit`, `post-edit`, `stop`) as `.sh` + `.ps1` + skills (`run-tests`, `lint`) |
| `full` | + sub-agents (`reviewer`, `debugger`, `scaffolder`) |

```
CLAUDE.md
.claude/
  settings.json
  hooks/
    pre-edit.sh / pre-edit.ps1
    post-edit.sh / post-edit.ps1
    stop.sh / stop.ps1
  skills/
    run-tests.md
    lint.md
  agents/
    reviewer.md
    debugger.md
    scaffolder.md
```

### GitHub Copilot

| Profile | Generated files |
|---|---|
| `basic` | `.github/copilot-instructions.md` |
| `standard` | + `.github/prompts/*.prompt.md` (execute-spec, new-spec, sync-agent, update-*) |

Use prompts in VS Code Copilot Chat by typing `#<prompt-name>`.

To add a custom Copilot prompt: `sdd prompt new my-prompt --format copilot`

### Cursor

| Profile | Generated files |
|---|---|
| `basic` | `.cursorrules` |
| `standard` | + `.cursor/rules/sdd.mdc` |

### Gemini CLI

| Profile | Generated files |
|---|---|
| `basic` | `GEMINI.md` |
| `standard` | + `GEMINI_TOOLS.md` |

### Windsurf

| Profile | Generated files |
|---|---|
| `basic` | `.windsurfrules` |

### Aider

| Profile | Generated files |
|---|---|
| `basic` | `.aider.conf.yml` + `CONVENTIONS.md` |

### Generic

Works with any agent that reads Markdown files.

| Profile | Generated files |
|---|---|
| `basic` | `AGENTS.md` |

---

## SDD Workflow

### 1. Constitution first

Edit `.specify/memory/constitution.md` — your project's immutable rules. Define the real stack, forbidden patterns, domain entities, and file structure. This is the highest source of truth. No spec can contradict it.

### 2. One spec per feature

Run `sdd new <feature>` for each business capability:
- `spec.md` — acceptance criteria (what, not how)
- `plan.md` — technical decisions and architecture
- `tasks.md` — atomic checkbox list

### 3. Run with your agent

```bash
sdd prompt run execute-spec --var SPEC_NAME=001-my-feature --copy
```

Paste the rendered prompt. The agent reads the spec, implements only pending tasks, marks them complete.

### 4. Update when things change

```bash
# Spec changed
sdd prompt run update-spec --var SPEC_NAME=001-my-feature --var CHANGE_REQUEST="..." --copy

# Plan changed
sdd prompt run update-plan --var SPEC_NAME=001-my-feature --var CHANGE_REQUEST="..." --copy

# Tasks changed
sdd prompt run update-tasks --var SPEC_NAME=001-my-feature --var CHANGE_REQUEST="..." --copy

# Architecture changed globally
sdd prompt run update-constitution --var CHANGE_REQUEST="..." --copy
```

### 5. Keep AGENTS.md current

```bash
sdd sync
```

### Conflict resolution

`constitution.md` > `spec.md` > `plan.md` > `tasks.md`

---

## Scripts (no CLI required)

```bash
# Mac / Linux
./.specify/scripts/new-spec.sh "payment-processing"
./.specify/scripts/validate.sh

# Windows (PowerShell)
.\.specify\scripts\new-spec.ps1 "payment-processing"
.\.specify\scripts\validate.ps1
```

---

## License

MIT
