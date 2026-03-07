"""
Dynamic palette — loads the active theme from settings and exposes ``COLORS``.
Other modules import ``COLORS`` from here as before; calling ``apply_theme()``
swaps the values at runtime.
"""

from .theme_registry import MIDNIGHT, get_theme

# Start with the default (Midnight).  ``apply_theme`` mutates this dict in-place
# so every module that imported ``COLORS`` sees the update instantly.
COLORS: dict[str, str] = dict(MIDNIGHT)


def apply_theme(name: str) -> None:
    """Replace **COLORS** values in-place with the named theme."""
    new = get_theme(name)
    COLORS.clear()
    COLORS.update(new)


def _load_initial_theme() -> None:
    """Called once at startup to read the persisted theme from settings."""
    try:
        import json
        from pathlib import Path
        cfg = Path(__file__).resolve().parents[3] / "fluxus_settings.json"
        if cfg.exists():
            data = json.loads(cfg.read_text("utf-8"))
            theme_name = data.get("theme", "Midnight (Default)")
            if theme_name and theme_name != "Dark (Default)":
                apply_theme(theme_name)
    except Exception:
        pass


# Auto-load on first import
_load_initial_theme()

