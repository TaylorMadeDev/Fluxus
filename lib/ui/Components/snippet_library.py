"""
SnippetLibrary — save & search reusable code snippets.
Stored as JSON at ``fluxus_snippets.json``.
"""

import json
import time
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPlainTextEdit, QPushButton, QScrollArea,
    QTextEdit, QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS

_SNIPPETS_FILE = Path(__file__).resolve().parents[3] / "fluxus_snippets.json"

# Built-in starter snippets
_BUILTINS = [
    {
        "name": "Echo to Chat",
        "tags": "chat, echo, hello",
        "code": 'import minescript\n\nminescript.echo("Hello from Fluxus!")\n',
    },
    {
        "name": "Get Player Position",
        "tags": "player, position, coords",
        "code": 'import minescript\n\npos = minescript.player_position()\nminescript.echo(f"You are at {pos}")\n',
    },
    {
        "name": "Place Blocks Loop",
        "tags": "blocks, build, loop",
        "code": (
            'import minescript\n\n'
            'x, y, z = minescript.player_position()\n'
            'for i in range(10):\n'
            '    minescript.execute(f"setblock {x+i} {y} {z} stone")\n'
            'minescript.echo("Done building!")\n'
        ),
    },
    {
        "name": "Teleport Player",
        "tags": "teleport, tp, move",
        "code": 'import minescript\n\nminescript.execute("tp ~ ~10 ~")  # teleport 10 blocks up\nminescript.echo("Teleported!")\n',
    },
    {
        "name": "Chat Bot Template",
        "tags": "chat, bot, listener",
        "code": (
            'import minescript\n\n'
            '# Simple chat responder\n'
            'minescript.echo("Chat bot active!")\n'
            '# Note: full chat listeners require minescript.register_chat_listener()\n'
        ),
    },
    {
        "name": "Block Scanner",
        "tags": "blocks, scan, detect",
        "code": (
            'import minescript\n\n'
            'x, y, z = minescript.player_position()\n'
            'block = minescript.getblock(x, y-1, z)\n'
            'minescript.echo(f"Standing on: {block}")\n'
        ),
    },
    {
        "name": "For Each Block in Region",
        "tags": "blocks, region, iterate",
        "code": (
            'import minescript\n\n'
            '# Iterate a 5x5x5 region around the player\n'
            'px, py, pz = minescript.player_position()\n'
            'for dx in range(-2, 3):\n'
            '    for dy in range(-2, 3):\n'
            '        for dz in range(-2, 3):\n'
            '            block = minescript.getblock(px+dx, py+dy, pz+dz)\n'
            '            if block != "minecraft:air":\n'
            '                minescript.echo(f"({px+dx},{py+dy},{pz+dz}): {block}")\n'
        ),
    },
]


def _load() -> list[dict]:
    try:
        if _SNIPPETS_FILE.exists():
            return json.loads(_SNIPPETS_FILE.read_text("utf-8"))
    except Exception:
        pass
    return list(_BUILTINS)


def _save(snippets: list[dict]) -> None:
    try:
        _SNIPPETS_FILE.write_text(json.dumps(snippets, indent=2, ensure_ascii=False), "utf-8")
    except Exception:
        pass


class SnippetLibrary(QFrame):
    """Snippet browser / manager panel."""

    insert_requested = Signal(str)  # code text to insert into editor

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SnippetLibrary")
        self._snippets = _load()
        self._build()
        self._populate()

    def _build(self) -> None:
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.setLayout(outer)

        # Header
        header = QFrame()
        header.setObjectName("BrowserHeader")
        header.setFixedHeight(40)
        h = QHBoxLayout()
        h.setContentsMargins(12, 0, 12, 0)
        h.setSpacing(8)
        header.setLayout(h)

        h.addWidget(self._lbl("📋  Snippet Library", "PanelTitle"))
        h.addStretch()

        add_btn = QPushButton("+ New")
        add_btn.setObjectName("SmallButton")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._new_snippet)
        h.addWidget(add_btn)

        outer.addWidget(header)

        # Search
        self._search = QLineEdit()
        self._search.setObjectName("SearchInput")
        self._search.setPlaceholderText("Search snippets…")
        self._search.setContentsMargins(10, 6, 10, 6)
        self._search.textChanged.connect(self._populate)
        outer.addWidget(self._search)

        # List
        self._list = QListWidget()
        self._list.setObjectName("ScriptList")
        self._list.currentRowChanged.connect(self._on_select)
        outer.addWidget(self._list, 1)

        # Preview area
        self._preview = QPlainTextEdit()
        self._preview.setObjectName("ConsoleOutput")
        self._preview.setReadOnly(True)
        self._preview.setFixedHeight(120)
        outer.addWidget(self._preview)

        # Action row
        action_row = QHBoxLayout()
        action_row.setContentsMargins(10, 6, 10, 8)
        action_row.setSpacing(8)

        insert_btn = QPushButton("📥 Insert into Editor")
        insert_btn.setObjectName("AccentButton")
        insert_btn.setCursor(Qt.PointingHandCursor)
        insert_btn.clicked.connect(self._insert)
        action_row.addWidget(insert_btn)

        copy_btn = QPushButton("📋 Copy")
        copy_btn.setObjectName("SmallButton")
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.clicked.connect(self._copy)
        action_row.addWidget(copy_btn)

        del_btn = QPushButton("🗑 Delete")
        del_btn.setObjectName("DangerSmallButton")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(self._delete)
        action_row.addWidget(del_btn)

        action_row.addStretch()
        outer.addLayout(action_row)

    def _lbl(self, text: str, obj: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj)
        return l

    def _populate(self, query: str = "") -> None:
        self._list.clear()
        q = query.lower().strip() if query else ""
        for i, snip in enumerate(self._snippets):
            name = snip.get("name", "Untitled")
            tags = snip.get("tags", "")
            if q and q not in name.lower() and q not in tags.lower():
                continue
            item = QListWidgetItem(f"  {name}")
            item.setData(Qt.UserRole, i)
            item.setToolTip(tags)
            self._list.addItem(item)

    def _on_select(self, row: int) -> None:
        item = self._list.item(row)
        if item is None:
            self._preview.clear()
            return
        idx = item.data(Qt.UserRole)
        if idx is not None and idx < len(self._snippets):
            self._preview.setPlainText(self._snippets[idx].get("code", ""))

    def _current_index(self) -> int | None:
        item = self._list.currentItem()
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def _insert(self) -> None:
        idx = self._current_index()
        if idx is not None:
            code = self._snippets[idx].get("code", "")
            self.insert_requested.emit(code)

    def _copy(self) -> None:
        idx = self._current_index()
        if idx is not None:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(self._snippets[idx].get("code", ""))

    def _delete(self) -> None:
        idx = self._current_index()
        if idx is not None:
            self._snippets.pop(idx)
            _save(self._snippets)
            self._populate(self._search.text())

    def _new_snippet(self) -> None:
        dlg = _SnippetDialog(self)
        if dlg.exec():
            self._snippets.insert(0, dlg.get_snippet())
            _save(self._snippets)
            self._populate(self._search.text())

    def save_from_selection(self, name: str, code: str) -> None:
        """Save a snippet from the editor selection."""
        self._snippets.insert(0, {"name": name, "tags": "", "code": code})
        _save(self._snippets)
        self._populate()


class _SnippetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Snippet")
        self.setMinimumSize(400, 320)
        self.setStyleSheet(
            f"QDialog {{ background-color: {COLORS['bg_dialog']}; }}"
        )
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        self.setLayout(layout)

        layout.addWidget(QLabel("Name:"))
        self._name = QLineEdit()
        self._name.setObjectName("SettingsInput")
        layout.addWidget(self._name)

        layout.addWidget(QLabel("Tags:"))
        self._tags = QLineEdit()
        self._tags.setObjectName("SettingsInput")
        self._tags.setPlaceholderText("comma, separated, tags")
        layout.addWidget(self._tags)

        layout.addWidget(QLabel("Code:"))
        self._code = QPlainTextEdit()
        self._code.setObjectName("ConsoleOutput")
        layout.addWidget(self._code, 1)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setObjectName("EditorToolButton")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        save = QPushButton("Save")
        save.setObjectName("AccentButton")
        save.clicked.connect(self.accept)
        btns.addWidget(save)
        layout.addLayout(btns)

    def get_snippet(self) -> dict:
        return {
            "name": self._name.text().strip() or "Untitled",
            "tags": self._tags.text().strip(),
            "code": self._code.toPlainText(),
        }
