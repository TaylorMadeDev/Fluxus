"""
Script manifest system — stores metadata (icon, name, version, description,
author, tags, enabled state) per script in a central JSON registry.
"""

import json
import time
from pathlib import Path
from typing import Any

_MANIFEST_FILE = Path(__file__).resolve().parents[3] / "fluxus_scripts.json"

# Available built-in emoji icons the user can pick from
SCRIPT_ICONS = [
    "⚡", "🔥", "🛡️", "⛏️", "🏗️", "🌍", "🎮", "🤖",
    "📜", "🔧", "🧪", "💎", "🚀", "🌙", "🎯", "📡",
    "🗡️", "🏹", "🧱", "🪄", "🔮", "🧭", "📦", "🌿",
]

_DEFAULT_META: dict[str, Any] = {
    "name": "",
    "description": "",
    "icon": "📜",
    "version": "1.0.0",
    "author": "",
    "tags": [],
    "enabled": True,
    "pinned": False,           # show on Front Page
    "favorite": False,         # ★ starred by user
    "run_count": 0,            # total execution count
    "last_run_ts": 0.0,        # timestamp of last run
    "created_ts": 0.0,
    "modified_ts": 0.0,
}


def _load_registry() -> dict[str, dict]:
    """Load the full registry dict keyed by absolute script path."""
    try:
        if _MANIFEST_FILE.exists():
            return json.loads(_MANIFEST_FILE.read_text("utf-8"))
    except Exception:
        pass
    return {}


def _save_registry(reg: dict[str, dict]) -> None:
    try:
        _MANIFEST_FILE.write_text(json.dumps(reg, indent=2, ensure_ascii=False), "utf-8")
    except Exception:
        pass


def get_meta(script_path: str) -> dict:
    """Return metadata for *script_path*, merging defaults for missing keys."""
    reg = _load_registry()
    stored = reg.get(script_path, {})
    merged = {**_DEFAULT_META, **stored}
    # Auto-fill name from filename if blank
    if not merged["name"]:
        merged["name"] = Path(script_path).stem.replace("_", " ").title()
    return merged


def set_meta(script_path: str, meta: dict) -> None:
    """Persist *meta* for *script_path*."""
    reg = _load_registry()
    meta["modified_ts"] = time.time()
    reg[script_path] = meta
    _save_registry(reg)


def delete_meta(script_path: str) -> None:
    reg = _load_registry()
    reg.pop(script_path, None)
    _save_registry(reg)


def list_all() -> dict[str, dict]:
    """Return the full registry (path -> meta), merging defaults."""
    reg = _load_registry()
    return {p: {**_DEFAULT_META, **m} for p, m in reg.items()}


def list_pinned(scripts_root: str) -> list[tuple[str, dict]]:
    """Return [(path, meta)] for scripts marked as pinned (Front Page)."""
    reg = _load_registry()
    results = []
    for path, raw in reg.items():
        m = {**_DEFAULT_META, **raw}
        if m.get("pinned") and Path(path).exists():
            results.append((path, m))
    # Also add scripts in root that have no manifest but exist
    return results


def ensure_defaults(script_path: str) -> dict:
    """Create a manifest entry with defaults if one doesn't already exist."""
    reg = _load_registry()
    if script_path not in reg:
        meta = dict(_DEFAULT_META)
        meta["name"] = Path(script_path).stem.replace("_", " ").title()
        meta["created_ts"] = time.time()
        meta["modified_ts"] = time.time()
        reg[script_path] = meta
        _save_registry(reg)
        return meta
    return {**_DEFAULT_META, **reg[script_path]}


def increment_run_count(script_path: str) -> None:
    """Increment run count and update last-run timestamp."""
    reg = _load_registry()
    stored = reg.get(script_path, dict(_DEFAULT_META))
    stored["run_count"] = stored.get("run_count", 0) + 1
    stored["last_run_ts"] = time.time()
    reg[script_path] = stored
    _save_registry(reg)


def toggle_favorite(script_path: str) -> bool:
    """Toggle favorite status and return the new value."""
    reg = _load_registry()
    stored = reg.get(script_path, dict(_DEFAULT_META))
    stored["favorite"] = not stored.get("favorite", False)
    reg[script_path] = stored
    _save_registry(reg)
    return stored["favorite"]


def list_favorites() -> list[tuple[str, dict]]:
    """Return [(path, meta)] for scripts marked as favorites."""
    reg = _load_registry()
    results = []
    for path, raw in reg.items():
        m = {**_DEFAULT_META, **raw}
        if m.get("favorite") and Path(path).exists():
            results.append((path, m))
    return results


def list_most_used(limit: int = 10) -> list[tuple[str, dict]]:
    """Return top *limit* scripts by run count."""
    reg = _load_registry()
    entries = []
    for path, raw in reg.items():
        m = {**_DEFAULT_META, **raw}
        if m.get("run_count", 0) > 0 and Path(path).exists():
            entries.append((path, m))
    entries.sort(key=lambda x: x[1].get("run_count", 0), reverse=True)
    return entries[:limit]
