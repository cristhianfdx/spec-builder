"""
Template engine — renders Jinja2 templates bundled inside the package.

Templates live in src/sddkit/templates/ and are included in the wheel
via pyproject.toml [tool.hatch.build.targets.wheel] package-data.

importlib.resources is used so the path resolves correctly whether the
package is installed from git, a wheel, or run in editable mode.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined


def _templates_dir() -> Path:
    """Return the absolute path to the bundled templates directory."""
    return Path(str(files("sddkit").joinpath("templates")))


def get_env(templates_dir: Path | None = None) -> Environment:
    base = templates_dir or _templates_dir()
    return Environment(
        loader=FileSystemLoader(str(base)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


def render(template_path: str, context: dict, templates_dir: Path | None = None) -> str:
    """
    Render a template file relative to the bundled templates directory.

    Args:
        template_path: Relative path, e.g. 'agents/claude-code.md.j2'
        context: Variables to inject.
        templates_dir: Override (useful for tests or custom template dirs).

    Returns:
        Rendered string.
    """
    env = get_env(templates_dir)
    template = env.get_template(template_path)
    return template.render(**context)


def render_string(source: str, context: dict) -> str:
    """Render an inline Jinja2 string (used for prompt variable substitution)."""
    env = Environment(undefined=StrictUndefined, keep_trailing_newline=True)
    return env.from_string(source).render(**context)
