"""
Keyboard shortcut manager — central place for keybinds.
Stores bindings as JSON and installs QShortcut objects at runtime.
"""

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QWidget

_SHORTCUTS_FILE = Path(__file__).resolve().parents[3] / "fluxus_shortcuts.json"

# Default keybindings: action_name → key sequence string
DEFAULTS: dict[str, str] = {
    "new_file": "Ctrl+N",
    "open_file": "Ctrl+O",
    "save_file": "Ctrl+S",
    "save_file_as": "Ctrl+Shift+S",
    "run_script": "F5",
    "run_in_mc": "Ctrl+F5",
    "stop_script": "Shift+F5",
    "find": "Ctrl+F",
    "replace": "Ctrl+H",
    "command_palette": "Ctrl+Shift+P",
    "toggle_console": "Ctrl+`",
    "toggle_sidebar": "Ctrl+B",
    "go_home": "Ctrl+1",
    "go_editor": "Ctrl+2",
    "go_scripts": "Ctrl+3",
    "go_runner": "Ctrl+4",
    "go_console": "Ctrl+5",
    "go_jobs": "Ctrl+6",
    "go_packages": "Ctrl+7",
    "go_settings": "Ctrl+8",
    "go_themes": "Ctrl+9",
    "close_tab": "Ctrl+W",
    "next_tab": "Ctrl+Tab",
    "prev_tab": "Ctrl+Shift+Tab",
    "undo": "Ctrl+Z",
    "redo": "Ctrl+Y",
}


def load_shortcuts() -> dict[str, str]:
    try:
        if _SHORTCUTS_FILE.exists():
            data = json.loads(_SHORTCUTS_FILE.read_text("utf-8"))
            return {**DEFAULTS, **data}
    except Exception:
        pass
    return dict(DEFAULTS)


def save_shortcuts(shortcuts: dict[str, str]) -> None:
    try:
        _SHORTCUTS_FILE.write_text(json.dumps(shortcuts, indent=2), "utf-8")
    except Exception:
        pass


class ShortcutManager:
    """
    Installs keyboard shortcuts on a parent widget and routes them
    to named callbacks.

    Usage::

        sm = ShortcutManager(window)
        sm.register("save_file", editor.save_file)
        sm.register("run_script", lambda: console.run_script(path))
    """

    def __init__(self, parent: QWidget):
        self._parent = parent
        self._bindings = load_shortcuts()
        self._shortcuts: dict[str, QShortcut] = {}
        self._callbacks: dict[str, callable] = {}

    def register(self, action: str, callback: callable) -> None:
        """Register a callback for an action. Creates the QShortcut."""
        self._callbacks[action] = callback
        key_str = self._bindings.get(action)
        if not key_str:
            return
        seq = QKeySequence(key_str)
        shortcut = QShortcut(seq, self._parent)
        shortcut.activated.connect(callback)
        self._shortcuts[action] = shortcut

    def rebind(self, action: str, new_key: str) -> None:
        """Change the key sequence for an action."""
        self._bindings[action] = new_key
        if action in self._shortcuts:
            self._shortcuts[action].setKey(QKeySequence(new_key))
        save_shortcuts(self._bindings)

    def get_bindings(self) -> dict[str, str]:
        return dict(self._bindings)

    def reset_defaults(self) -> None:
        self._bindings = dict(DEFAULTS)
        save_shortcuts(self._bindings)
        for action, shortcut in self._shortcuts.items():
            key = self._bindings.get(action, "")
            shortcut.setKey(QKeySequence(key))
