"""
TODO Panel — scans scripts for TODO/FIXME/HACK/NOTE comments and displays
them in a navigable list.  Also provides a bookmark system.
"""

import re
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS

_TODO_PATTERN = re.compile(
    r"#\s*(TODO|FIXME|HACK|NOTE|XXX|BUG|OPTIMIZE|REVIEW)\b[:\s]*(.*)",
    re.IGNORECASE,
)


class TodoPanel(QFrame):
    """Panel showing TODO/FIXME annotations from all scripts + bookmarks."""

    navigate_requested = Signal(str, int)  # file_path, line_number

    def __init__(self, scripts_root: str, parent=None):
        super().__init__(parent)
        self.setObjectName("TodoPanel")
        self._root = scripts_root
        self._bookmarks: list[dict] = []  # {"file": str, "line": int, "text": str}
        self._build()

    def _build(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Header
        header = QFrame()
        header.setObjectName("BrowserHeader")
        header.setFixedHeight(36)
        hl = QHBoxLayout()
        hl.setContentsMargins(10, 0, 10, 0)
        hl.setSpacing(6)
        header.setLayout(hl)

        title = QLabel("📌 TODOs & Bookmarks")
        title.setObjectName("PanelTitle")
        hl.addWidget(title)
        hl.addStretch()

        scan_btn = QPushButton("🔄 Scan")
        scan_btn.setObjectName("SmallButton")
        scan_btn.setCursor(Qt.PointingHandCursor)
        scan_btn.clicked.connect(self.scan)
        hl.addWidget(scan_btn)

        layout.addWidget(header)

        # Tabs: TODOs | Bookmarks
        self._tabs = QTabWidget()
        self._tabs.setObjectName("TodoTabs")
        self._tabs.setDocumentMode(True)

        # TODO list
        todo_page = QWidget()
        todo_layout = QVBoxLayout()
        todo_layout.setContentsMargins(6, 6, 6, 6)
        todo_layout.setSpacing(4)
        todo_page.setLayout(todo_layout)

        self._todo_search = QLineEdit()
        self._todo_search.setObjectName("SearchInput")
        self._todo_search.setPlaceholderText("Filter TODOs…")
        self._todo_search.textChanged.connect(self._filter_todos)
        todo_layout.addWidget(self._todo_search)

        self._todo_list = QListWidget()
        self._todo_list.setObjectName("TodoList")
        self._todo_list.setAlternatingRowColors(True)
        self._todo_list.itemDoubleClicked.connect(self._on_todo_click)
        self._style_list(self._todo_list)
        todo_layout.addWidget(self._todo_list, 1)

        self._todo_count = QLabel("0 items")
        self._todo_count.setObjectName("BrowserInfo")
        todo_layout.addWidget(self._todo_count)

        self._tabs.addTab(todo_page, "📝 TODOs")

        # Bookmarks
        bm_page = QWidget()
        bm_layout = QVBoxLayout()
        bm_layout.setContentsMargins(6, 6, 6, 6)
        bm_layout.setSpacing(4)
        bm_page.setLayout(bm_layout)

        self._bm_list = QListWidget()
        self._bm_list.setObjectName("BookmarkList")
        self._bm_list.setAlternatingRowColors(True)
        self._bm_list.itemDoubleClicked.connect(self._on_bm_click)
        self._style_list(self._bm_list)
        bm_layout.addWidget(self._bm_list, 1)

        bm_btns = QHBoxLayout()
        clear_bm = QPushButton("Clear All")
        clear_bm.setObjectName("DangerSmallButton")
        clear_bm.setCursor(Qt.PointingHandCursor)
        clear_bm.clicked.connect(self._clear_bookmarks)
        bm_btns.addStretch()
        bm_btns.addWidget(clear_bm)
        bm_layout.addLayout(bm_btns)

        self._tabs.addTab(bm_page, "🔖 Bookmarks")

        layout.addWidget(self._tabs, 1)

    def _style_list(self, lst: QListWidget):
        lst.setStyleSheet(f"""
            QListWidget {{
                background: {COLORS.get('bg_surface', '#16162e')};
                color: {COLORS.get('text_primary', '#e8e6f0')};
                border: 1px solid {COLORS.get('border', '#2a2a4a')};
                border-radius: 4px;
                font-family: 'Consolas'; font-size: 11px;
            }}
            QListWidget::item {{ padding: 4px 6px; }}
            QListWidget::item:selected {{
                background: {COLORS.get('accent', '#7c6aef')};
            }}
            QListWidget::item:alternate {{
                background: {COLORS.get('bg_root', '#0e0e1e')};
            }}
        """)

    def scan(self):
        """Scan all scripts for TODO/FIXME/HACK/NOTE comments."""
        self._todo_list.clear()
        root = Path(self._root)
        items = []

        for f in root.rglob("*.[p][y]*"):
            if "__pycache__" in str(f) or f.suffix not in (".py", ".pyj"):
                continue
            try:
                lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
                for i, line in enumerate(lines, 1):
                    m = _TODO_PATTERN.search(line)
                    if m:
                        kind = m.group(1).upper()
                        text = m.group(2).strip()
                        items.append({
                            "file": str(f),
                            "line": i,
                            "kind": kind,
                            "text": text,
                            "rel": str(f.relative_to(root)),
                        })
            except Exception:
                continue

        # Sort by kind then file
        items.sort(key=lambda x: (x["kind"], x["rel"], x["line"]))

        _KIND_ICONS = {
            "TODO": "📝", "FIXME": "🔧", "HACK": "⚠️",
            "NOTE": "📌", "XXX": "❌", "BUG": "🐛",
            "OPTIMIZE": "⚡", "REVIEW": "👀",
        }

        for item in items:
            icon = _KIND_ICONS.get(item["kind"], "📝")
            display = f'{icon} [{item["kind"]}] {item["rel"]}:{item["line"]}  {item["text"]}'
            li = QListWidgetItem(display)
            li.setData(Qt.UserRole, item)
            li.setToolTip(f'{item["file"]}:{item["line"]}')
            self._todo_list.addItem(li)

        self._todo_count.setText(f"{len(items)} items found")

    def _filter_todos(self, text: str):
        text = text.strip().lower()
        for i in range(self._todo_list.count()):
            item = self._todo_list.item(i)
            item.setHidden(text not in item.text().lower())

    def _on_todo_click(self, item: QListWidgetItem):
        data = item.data(Qt.UserRole)
        if data:
            self.navigate_requested.emit(data["file"], data["line"])

    # ── Bookmarks ─────────────────────────────────────────────────
    def add_bookmark(self, file_path: str, line: int, text: str = ""):
        """Add a bookmark at a specific file + line."""
        bm = {"file": file_path, "line": line, "text": text}
        # Avoid duplicates
        for existing in self._bookmarks:
            if existing["file"] == file_path and existing["line"] == line:
                return
        self._bookmarks.append(bm)
        self._refresh_bookmarks()

    def remove_bookmark(self, file_path: str, line: int):
        self._bookmarks = [
            b for b in self._bookmarks
            if not (b["file"] == file_path and b["line"] == line)
        ]
        self._refresh_bookmarks()

    def toggle_bookmark(self, file_path: str, line: int, text: str = ""):
        """Toggle a bookmark on/off."""
        for b in self._bookmarks:
            if b["file"] == file_path and b["line"] == line:
                self.remove_bookmark(file_path, line)
                return False
        self.add_bookmark(file_path, line, text)
        return True

    def _refresh_bookmarks(self):
        self._bm_list.clear()
        for bm in self._bookmarks:
            name = Path(bm["file"]).name
            display = f"🔖 {name}:{bm['line']}"
            if bm.get("text"):
                display += f"  — {bm['text']}"
            li = QListWidgetItem(display)
            li.setData(Qt.UserRole, bm)
            self._bm_list.addItem(li)

    def _on_bm_click(self, item: QListWidgetItem):
        data = item.data(Qt.UserRole)
        if data:
            self.navigate_requested.emit(data["file"], data["line"])

    def _clear_bookmarks(self):
        self._bookmarks.clear()
        self._bm_list.clear()

    def get_bookmarks(self) -> list[dict]:
        return list(self._bookmarks)

    def set_bookmarks(self, bookmarks: list[dict]):
        self._bookmarks = bookmarks
        self._refresh_bookmarks()
