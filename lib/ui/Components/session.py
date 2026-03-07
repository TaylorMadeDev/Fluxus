"""
Session — save / restore app state (open files, page, window geometry,
cursor positions, panel states, workspace layouts).
"""

import json
from pathlib import Path

_SESSION_FILE = Path(__file__).resolve().parents[3] / "fluxus_session.json"


def save_session(
    open_files: list[str],
    active_file: str | None = None,
    page_index: int = 0,
    geometry: tuple[int, int, int, int] | None = None,
    sidebar_collapsed: bool = False,
    cursor_positions: dict[str, tuple[int, int]] | None = None,
    panel_states: dict[str, bool] | None = None,
    zen_mode: bool = False,
    word_wrap: bool = False,
) -> None:
    data = {
        "open_files": open_files,
        "active_file": active_file,
        "page_index": page_index,
        "sidebar_collapsed": sidebar_collapsed,
        "cursor_positions": cursor_positions or {},
        "panel_states": panel_states or {},
        "zen_mode": zen_mode,
        "word_wrap": word_wrap,
    }
    if geometry:
        data["geometry"] = list(geometry)
    try:
        _SESSION_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")
    except Exception:
        pass


def load_session() -> dict:
    try:
        if _SESSION_FILE.exists():
            return json.loads(_SESSION_FILE.read_text("utf-8"))
    except Exception:
        pass
    return {}
