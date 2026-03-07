"""
DocsPanel — browsable Minescript API documentation panel.
Organized by category with search, detail view, and copy-to-editor support.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QScrollArea, QSplitter, QTextEdit, QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS
from .minescript_api import (
    CATEGORIES, MINESCRIPT_API, MINESCRIPT_TYPES,
    get_entries_by_category, get_api_entry, APIEntry,
)


class DocsPanel(QFrame):
    """Searchable Minescript documentation browser."""

    insert_requested = Signal(str)  # emit snippet to insert into editor

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DocsPanel")
        self._all_entries = MINESCRIPT_API + MINESCRIPT_TYPES
        self._build()

    def _build(self):
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.setLayout(outer)

        # Header
        header = QFrame()
        header.setObjectName("DocsHeader")
        header.setFixedHeight(44)
        h_lay = QHBoxLayout()
        h_lay.setContentsMargins(12, 0, 12, 0)
        h_lay.setSpacing(8)
        header.setLayout(h_lay)

        title = QLabel("📖  Minescript Docs")
        title.setObjectName("PanelTitle")
        h_lay.addWidget(title)

        h_lay.addStretch()

        ver = QLabel("Minescript v5.0  •  MS+ v0.16.2")
        ver.setObjectName("DocsBadge")
        ver.setStyleSheet(f"""
            background: {COLORS.get('accent', '#7c6aef')};
            color: #fff; border-radius: 8px;
            padding: 2px 8px; font-size: 10px; font-weight: 700;
        """)
        h_lay.addWidget(ver)

        outer.addWidget(header)

        # Search bar
        search_bar = QFrame()
        search_bar.setObjectName("DocsSearchBar")
        search_bar.setFixedHeight(38)
        sb_lay = QHBoxLayout()
        sb_lay.setContentsMargins(12, 4, 12, 4)
        search_bar.setLayout(sb_lay)

        self._search = QLineEdit()
        self._search.setObjectName("DocsSearch")
        self._search.setPlaceholderText("Search API… (e.g. player_position, BlockPack)")
        self._search.textChanged.connect(self._on_search)
        sb_lay.addWidget(self._search)

        outer.addWidget(search_bar)

        # Splitter: left list, right detail
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("DocsSplitter")

        # Left — category + function list
        left = QWidget()
        left_lay = QVBoxLayout()
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)
        left.setLayout(left_lay)

        self._cat_list = QListWidget()
        self._cat_list.setObjectName("DocsCategoryList")
        self._cat_list.setFixedHeight(220)
        for label, tag in CATEGORIES:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, tag)
            self._cat_list.addItem(item)
        self._cat_list.currentItemChanged.connect(self._on_category_changed)
        left_lay.addWidget(self._cat_list)

        self._func_list = QListWidget()
        self._func_list.setObjectName("DocsFuncList")
        self._func_list.currentItemChanged.connect(self._on_func_selected)
        left_lay.addWidget(self._func_list, 1)

        splitter.addWidget(left)

        # Right — detail view
        right = QWidget()
        right_lay = QVBoxLayout()
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)
        right.setLayout(right_lay)

        self._detail = QTextEdit()
        self._detail.setObjectName("DocsDetail")
        self._detail.setReadOnly(True)
        self._detail.setFont(QFont("Consolas", 10))
        right_lay.addWidget(self._detail, 1)

        # Insert snippet button
        btn_bar = QFrame()
        btn_bar.setFixedHeight(36)
        btn_lay = QHBoxLayout()
        btn_lay.setContentsMargins(8, 2, 8, 2)
        btn_bar.setLayout(btn_lay)
        btn_lay.addStretch()

        self._insert_btn = QPushButton("Insert into Editor")
        self._insert_btn.setObjectName("AccentButton")
        self._insert_btn.setCursor(Qt.PointingHandCursor)
        self._insert_btn.clicked.connect(self._on_insert)
        btn_lay.addWidget(self._insert_btn)

        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setObjectName("SmallButton")
        self._copy_btn.setCursor(Qt.PointingHandCursor)
        self._copy_btn.clicked.connect(self._on_copy)
        btn_lay.addWidget(self._copy_btn)

        right_lay.addWidget(btn_bar)

        splitter.addWidget(right)
        splitter.setSizes([260, 440])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        outer.addWidget(splitter, 1)

        # Select first category
        if self._cat_list.count():
            self._cat_list.setCurrentRow(0)

    # ── Slots ──────────────────────────────────────────────────────
    def _on_category_changed(self, current, _previous):
        if not current:
            return
        tag = current.data(Qt.UserRole)
        entries = get_entries_by_category(tag)
        self._func_list.clear()
        for e in entries:
            item = QListWidgetItem(e.name)
            item.setData(Qt.UserRole, e.name)
            self._func_list.addItem(item)
        if self._func_list.count():
            self._func_list.setCurrentRow(0)

    def _on_func_selected(self, current, _previous):
        if not current:
            self._detail.clear()
            return
        name = current.data(Qt.UserRole)
        entry = get_api_entry(name)
        if entry:
            self._show_entry(entry)

    def _show_entry(self, e: APIEntry):
        accent = COLORS.get("accent", "#7c6aef")
        text_primary = COLORS.get("text_primary", "#e8e6f0")
        text_dim = COLORS.get("text_dim", "#6b6b8d")
        bg = COLORS.get("bg_surface", "#16162e")

        sig = f"({e.signature})" if e.signature else ""
        html = f"""
        <div style="font-family: 'Segoe UI', sans-serif; color: {text_primary}; padding: 8px;">
            <h2 style="color: {accent}; margin-bottom: 2px;">{e.name}</h2>
            <code style="color: {text_dim}; font-size: 12px; background: {bg}; padding: 4px 8px; border-radius: 4px;">
                {e.module}.{e.name}{sig}
            </code>
            <p style="margin-top: 12px; line-height: 1.6;">{e.description}</p>
        """
        if e.params:
            html += f'<h3 style="color: {accent}; margin-top: 12px;">Parameters</h3><ul>'
            for p in e.params:
                html += f'<li style="color: {text_primary};">{p}</li>'
            html += "</ul>"

        if e.returns:
            html += f'<h3 style="color: {accent}; margin-top: 12px;">Returns</h3>'
            html += f'<p style="color: {text_primary};">{e.returns}</p>'

        if e.since:
            html += f'<p style="color: {text_dim}; margin-top: 12px; font-size: 11px;">Since: {e.since}</p>'

        html += "</div>"
        self._detail.setHtml(html)

    def _on_search(self, text: str):
        text = text.strip().lower()
        if not text:
            # Restore category view
            if self._cat_list.currentItem():
                self._on_category_changed(self._cat_list.currentItem(), None)
            return

        matches = [e for e in self._all_entries if text in e.name.lower() or text in e.description.lower()]
        self._func_list.clear()
        for e in matches:
            item = QListWidgetItem(e.name)
            item.setData(Qt.UserRole, e.name)
            self._func_list.addItem(item)
        if self._func_list.count():
            self._func_list.setCurrentRow(0)

    def _on_insert(self):
        current = self._func_list.currentItem()
        if not current:
            return
        name = current.data(Qt.UserRole)
        entry = get_api_entry(name)
        if entry:
            # Build a useful snippet
            if entry.signature:
                snippet = f"{entry.name}({entry.signature})"
            else:
                snippet = entry.name
            self.insert_requested.emit(snippet)

    def _on_copy(self):
        current = self._func_list.currentItem()
        if not current:
            return
        name = current.data(Qt.UserRole)
        entry = get_api_entry(name)
        if entry:
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(entry.detail_text)
