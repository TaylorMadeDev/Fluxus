"""
Theme registry — built-in color themes and JSON import/export.
Each theme is a complete ``COLORS`` dict.  The active theme is stored
in ``fluxus_settings.json["theme"]``.
"""

import json
from pathlib import Path
from typing import Any

_THEMES_DIR = Path(__file__).resolve().parents[2] / "themes"
_THEMES_DIR.mkdir(exist_ok=True)

# ── Midnight  (the original default) ──────────────────────────────
MIDNIGHT = {
    "bg_root": "#0d0f12", "bg_surface": "#11151b", "bg_topbar": "#161b22",
    "bg_sidebar": "#0f1217", "bg_panel": "#131820", "bg_editor": "#0e1117",
    "bg_input": "#0c0e13", "bg_console": "#0a0c10", "bg_hover": "#1f2630",
    "bg_pressed": "#273140", "bg_selected": "#1a2332", "bg_tab_active": "#161b22",
    "bg_tab_inactive": "#0f1217", "bg_badge": "#1e2a3a", "bg_card": "#141922",
    "bg_card_hover": "#1a2030", "bg_dialog": "#131820",
    "border": "#222b36", "border_light": "#2a3545",
    "border_focus": "#4da3ff", "border_card": "#1e2738",
    "text_primary": "#e8edf3", "text_secondary": "#c0c8d4",
    "text_muted": "#9aa6b2", "text_dim": "#6b7685",
    "accent": "#4da3ff", "accent_hover": "#6ab4ff", "accent_dim": "#2a5f9e",
    "success": "#4ade80", "success_dim": "#1a5c34",
    "warning": "#f0b429", "warning_dim": "#6b4f14",
    "danger": "#e25a5a", "danger_hover": "#f06b6b", "info": "#8b9cf7",
    "syn_keyword": "#c678dd", "syn_string": "#98c379", "syn_number": "#d19a66",
    "syn_comment": "#5c6370", "syn_function": "#61afef", "syn_class": "#e5c07b",
    "syn_builtin": "#56b6c2", "syn_decorator": "#c678dd", "syn_operator": "#abb2bf",
    "syn_self": "#e06c75",
}

# ── Monokai ───────────────────────────────────────────────────────
MONOKAI = {
    "bg_root": "#1e1f1c", "bg_surface": "#272822", "bg_topbar": "#2d2e27",
    "bg_sidebar": "#222318", "bg_panel": "#272822", "bg_editor": "#272822",
    "bg_input": "#1e1f1c", "bg_console": "#1a1b17", "bg_hover": "#3e3d32",
    "bg_pressed": "#4a4940", "bg_selected": "#49483e", "bg_tab_active": "#2d2e27",
    "bg_tab_inactive": "#222318", "bg_badge": "#3e3d32", "bg_card": "#2d2e27",
    "bg_card_hover": "#3e3d32", "bg_dialog": "#272822",
    "border": "#3e3d32", "border_light": "#4a4940",
    "border_focus": "#a6e22e", "border_card": "#3e3d32",
    "text_primary": "#f8f8f2", "text_secondary": "#cfcfc2",
    "text_muted": "#a0a08b", "text_dim": "#75715e",
    "accent": "#a6e22e", "accent_hover": "#b6f23e", "accent_dim": "#5a7a14",
    "success": "#a6e22e", "success_dim": "#3a5c0e",
    "warning": "#e6db74", "warning_dim": "#6b6324",
    "danger": "#f92672", "danger_hover": "#ff4488", "info": "#ae81ff",
    "syn_keyword": "#f92672", "syn_string": "#e6db74", "syn_number": "#ae81ff",
    "syn_comment": "#75715e", "syn_function": "#a6e22e", "syn_class": "#66d9ef",
    "syn_builtin": "#66d9ef", "syn_decorator": "#f92672", "syn_operator": "#f8f8f2",
    "syn_self": "#fd971f",
}

# ── Dracula ───────────────────────────────────────────────────────
DRACULA = {
    "bg_root": "#1e1f29", "bg_surface": "#282a36", "bg_topbar": "#2c2f3e",
    "bg_sidebar": "#21222c", "bg_panel": "#282a36", "bg_editor": "#282a36",
    "bg_input": "#1e1f29", "bg_console": "#1a1b25", "bg_hover": "#343746",
    "bg_pressed": "#3e4256", "bg_selected": "#44475a", "bg_tab_active": "#2c2f3e",
    "bg_tab_inactive": "#21222c", "bg_badge": "#44475a", "bg_card": "#2c2f3e",
    "bg_card_hover": "#343746", "bg_dialog": "#282a36",
    "border": "#44475a", "border_light": "#555870",
    "border_focus": "#bd93f9", "border_card": "#44475a",
    "text_primary": "#f8f8f2", "text_secondary": "#d4d4dc",
    "text_muted": "#a4a4b4", "text_dim": "#6272a4",
    "accent": "#bd93f9", "accent_hover": "#d0a8ff", "accent_dim": "#6e50a0",
    "success": "#50fa7b", "success_dim": "#1a5c30",
    "warning": "#f1fa8c", "warning_dim": "#6b6e24",
    "danger": "#ff5555", "danger_hover": "#ff6e6e", "info": "#8be9fd",
    "syn_keyword": "#ff79c6", "syn_string": "#f1fa8c", "syn_number": "#bd93f9",
    "syn_comment": "#6272a4", "syn_function": "#50fa7b", "syn_class": "#8be9fd",
    "syn_builtin": "#8be9fd", "syn_decorator": "#ff79c6", "syn_operator": "#f8f8f2",
    "syn_self": "#ffb86c",
}

# ── Solarized Dark ────────────────────────────────────────────────
SOLARIZED = {
    "bg_root": "#002b36", "bg_surface": "#073642", "bg_topbar": "#0a3d4a",
    "bg_sidebar": "#002530", "bg_panel": "#073642", "bg_editor": "#002b36",
    "bg_input": "#002028", "bg_console": "#001e24", "bg_hover": "#0d4654",
    "bg_pressed": "#105060", "bg_selected": "#0d4654", "bg_tab_active": "#0a3d4a",
    "bg_tab_inactive": "#002530", "bg_badge": "#0d4654", "bg_card": "#073642",
    "bg_card_hover": "#0d4654", "bg_dialog": "#073642",
    "border": "#0d4654", "border_light": "#186070",
    "border_focus": "#268bd2", "border_card": "#0d4654",
    "text_primary": "#fdf6e3", "text_secondary": "#eee8d5",
    "text_muted": "#93a1a1", "text_dim": "#657b83",
    "accent": "#268bd2", "accent_hover": "#3a9de0", "accent_dim": "#144a70",
    "success": "#859900", "success_dim": "#3a4c00",
    "warning": "#b58900", "warning_dim": "#5a4400",
    "danger": "#dc322f", "danger_hover": "#ee4440", "info": "#6c71c4",
    "syn_keyword": "#859900", "syn_string": "#2aa198", "syn_number": "#d33682",
    "syn_comment": "#586e75", "syn_function": "#268bd2", "syn_class": "#b58900",
    "syn_builtin": "#2aa198", "syn_decorator": "#6c71c4", "syn_operator": "#93a1a1",
    "syn_self": "#cb4b16",
}

# ── Minecraft Green ───────────────────────────────────────────────
MINECRAFT = {
    "bg_root": "#0c1a0c", "bg_surface": "#112211", "bg_topbar": "#163016",
    "bg_sidebar": "#0e1c0e", "bg_panel": "#122612", "bg_editor": "#0e1a0e",
    "bg_input": "#091409", "bg_console": "#070f07", "bg_hover": "#1e3a1e",
    "bg_pressed": "#264a26", "bg_selected": "#1e3a1e", "bg_tab_active": "#163016",
    "bg_tab_inactive": "#0e1c0e", "bg_badge": "#1e3a1e", "bg_card": "#142a14",
    "bg_card_hover": "#1e3a1e", "bg_dialog": "#122612",
    "border": "#1e3a1e", "border_light": "#2a502a",
    "border_focus": "#55ff55", "border_card": "#1e3a1e",
    "text_primary": "#e0ffe0", "text_secondary": "#b0d8b0",
    "text_muted": "#80b080", "text_dim": "#507050",
    "accent": "#55ff55", "accent_hover": "#77ff77", "accent_dim": "#228822",
    "success": "#55ff55", "success_dim": "#1a5c1a",
    "warning": "#ffcc00", "warning_dim": "#6b5500",
    "danger": "#ff5555", "danger_hover": "#ff7777", "info": "#55bbff",
    "syn_keyword": "#55ff55", "syn_string": "#ffcc00", "syn_number": "#ff8855",
    "syn_comment": "#507050", "syn_function": "#55bbff", "syn_class": "#ffaa00",
    "syn_builtin": "#00cccc", "syn_decorator": "#ff55ff", "syn_operator": "#b0d8b0",
    "syn_self": "#ff8855",
}

# ── Light ─────────────────────────────────────────────────────────
LIGHT = {
    "bg_root": "#f5f5f5", "bg_surface": "#ffffff", "bg_topbar": "#e8e8e8",
    "bg_sidebar": "#ebebeb", "bg_panel": "#ffffff", "bg_editor": "#ffffff",
    "bg_input": "#f0f0f0", "bg_console": "#f8f8f8", "bg_hover": "#e0e0e0",
    "bg_pressed": "#d0d0d0", "bg_selected": "#d8e8f8", "bg_tab_active": "#ffffff",
    "bg_tab_inactive": "#ebebeb", "bg_badge": "#e0e8f0", "bg_card": "#ffffff",
    "bg_card_hover": "#f0f4f8", "bg_dialog": "#ffffff",
    "border": "#d0d0d0", "border_light": "#c0c0c0",
    "border_focus": "#2080d0", "border_card": "#e0e0e0",
    "text_primary": "#1a1a1a", "text_secondary": "#333333",
    "text_muted": "#666666", "text_dim": "#999999",
    "accent": "#2080d0", "accent_hover": "#3090e0", "accent_dim": "#a0c8e8",
    "success": "#22863a", "success_dim": "#dcffe4",
    "warning": "#b08800", "warning_dim": "#fff8dc",
    "danger": "#d73a49", "danger_hover": "#e04858", "info": "#6f42c1",
    "syn_keyword": "#d73a49", "syn_string": "#22863a", "syn_number": "#005cc5",
    "syn_comment": "#6a737d", "syn_function": "#6f42c1", "syn_class": "#e36209",
    "syn_builtin": "#005cc5", "syn_decorator": "#6f42c1", "syn_operator": "#1a1a1a",
    "syn_self": "#d73a49",
}

# ── Registry ──────────────────────────────────────────────────────
BUILTIN_THEMES: dict[str, dict[str, str]] = {
    "Midnight (Default)": MIDNIGHT,
    "Monokai": MONOKAI,
    "Dracula": DRACULA,
    "Solarized Dark": SOLARIZED,
    "Minecraft Green": MINECRAFT,
    "Light": LIGHT,
}


def get_theme(name: str) -> dict[str, str]:
    """Return the color dict for *name*, falling back to Midnight."""
    if name in BUILTIN_THEMES:
        return dict(BUILTIN_THEMES[name])
    # Try loading from JSON file
    fpath = _THEMES_DIR / f"{name}.json"
    if fpath.exists():
        try:
            data = json.loads(fpath.read_text("utf-8"))
            merged = {**MIDNIGHT, **data}
            return merged
        except Exception:
            pass
    return dict(MIDNIGHT)


def save_custom_theme(name: str, colors: dict[str, str]) -> Path:
    """Persist a user-created theme to the themes directory."""
    fpath = _THEMES_DIR / f"{name}.json"
    fpath.write_text(json.dumps(colors, indent=2), "utf-8")
    return fpath


def list_all_themes() -> list[str]:
    """Return sorted list of all available theme names."""
    names = list(BUILTIN_THEMES.keys())
    if _THEMES_DIR.is_dir():
        for f in sorted(_THEMES_DIR.glob("*.json")):
            custom_name = f.stem
            if custom_name not in names:
                names.append(custom_name)
    return names


def delete_custom_theme(name: str) -> bool:
    """Delete a custom theme. Returns True on success."""
    if name in BUILTIN_THEMES:
        return False          # can't delete built-ins
    fpath = _THEMES_DIR / f"{name}.json"
    if fpath.exists():
        fpath.unlink()
        return True
    return False
