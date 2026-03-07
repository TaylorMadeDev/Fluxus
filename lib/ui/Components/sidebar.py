from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS


# ── All searchable pages (icon, display name, tag) ─────────────────
_SEARCHABLE_PAGES = [
    ("🏠", "Home", "home"),
    ("📝", "Editor", "editor"),
    ("📁", "Scripts", "scripts"),
    ("📎", "Snippets", "snippets"),
    ("📖", "Docs", "docs"),
    ("📂", "Files", "files"),
    ("▶", "Runner", "runner"),
    ("📋", "Console", "console"),
    ("⚡", "Jobs", "jobs"),
    ("🔍", "Inspector", "inspector"),
    ("📦", "Packages", "packages"),
    ("🔌", "Plugins", "plugins"),
    ("📚", "Reference", "reference"),
    ("📌", "TODOs", "todos"),
    ("🔀", "Git", "git"),
    ("🏪", "Plugin Store", "plugin_store"),
    ("📥", "Script Store", "script_store"),
    ("🎨", "Themes", "themes"),
    ("🔔", "Webhook", "webhook"),
    ("⚙", "Settings", "settings"),
    ("⌨", "Shortcuts", "shortcuts_editor"),
    ("💾", "Backups", "backups"),
]


class SidebarButton(QPushButton):
    """A single icon+label nav button for the sidebar."""

    def __init__(self, icon_char: str, label: str, tag: str, parent=None):
        super().__init__(parent)
        self.tag = tag
        self._icon_char = icon_char
        self._label_text = label
        self.setObjectName("SidebarButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setFixedHeight(42)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout()
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(10)
        self.setLayout(layout)

        self._icon_label = QLabel(icon_char, self)
        self._icon_label.setObjectName("SidebarIcon")
        self._icon_label.setFixedWidth(22)
        self._icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._icon_label)

        self._text_label = QLabel(label, self)
        self._text_label.setObjectName("SidebarLabel")
        layout.addWidget(self._text_label)
        layout.addStretch()

    def enterEvent(self, event):
        """Slight scale-up feel via padding tweak."""
        self.setContentsMargins(12, 0, 10, 0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setContentsMargins(14, 0, 10, 0)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.setContentsMargins(16, 1, 10, 0)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setContentsMargins(12, 0, 10, 0)
        super().mouseReleaseEvent(event)

    def setChecked(self, checked: bool) -> None:
        super().setChecked(checked)

    def set_collapsed(self, collapsed: bool) -> None:
        self._text_label.setVisible(not collapsed)


class SidebarCategoryLabel(QLabel):
    """Small uppercase header that separates sidebar groups."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("SidebarCategory")
        self.setContentsMargins(16, 10, 0, 3)


class SidebarSearchBar(QFrame):
    """Animated search bar that filters and navigates to sidebar pages."""

    page_selected = Signal(str)  # emits tag of selected page

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarSearchBar")
        self.setFixedHeight(0)  # starts collapsed
        self._expanded = False
        self._all_pages = list(_SEARCHABLE_PAGES)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        self.setLayout(layout)

        self._input = QLineEdit()
        self._input.setObjectName("SidebarSearchInput")
        self._input.setPlaceholderText("Search pages…")
        self._input.textChanged.connect(self._on_filter)
        self._input.returnPressed.connect(self._select_top)
        layout.addWidget(self._input)

        self._results = QListWidget()
        self._results.setObjectName("SidebarSearchResults")
        self._results.setMaximumHeight(200)
        self._results.setVisible(False)
        self._results.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._results)

    def toggle(self) -> None:
        self._expanded = not self._expanded
        target_h = 44 if self._expanded else 0

        anim = QPropertyAnimation(self, b"maximumHeight")
        anim.setDuration(200)
        anim.setStartValue(self.height())
        anim.setEndValue(target_h)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.start()
        self._anim = anim

        anim2 = QPropertyAnimation(self, b"minimumHeight")
        anim2.setDuration(200)
        anim2.setStartValue(self.height())
        anim2.setEndValue(target_h)
        anim2.setEasingCurve(QEasingCurve.InOutQuad)
        anim2.start()
        self._anim2 = anim2

        if self._expanded:
            self._input.setFocus()
        else:
            self._input.clear()
            self._results.setVisible(False)

    def set_collapsed(self, sidebar_collapsed: bool) -> None:
        """Hide when sidebar collapses."""
        if sidebar_collapsed and self._expanded:
            self._expanded = False
            self.setFixedHeight(0)
            self._input.clear()
            self._results.setVisible(False)

    def _on_filter(self, text: str) -> None:
        text = text.strip().lower()
        self._results.clear()
        if not text:
            self._results.setVisible(False)
            # Shrink back to input-only
            self._animate_height(44)
            return

        matches = [(icon, name, tag) for icon, name, tag in self._all_pages
                    if text in name.lower() or text in tag.lower()]

        if matches:
            for icon, name, tag in matches:
                item = QListWidgetItem(f"{icon}  {name}")
                item.setData(Qt.UserRole, tag)
                self._results.addItem(item)
            self._results.setVisible(True)
            list_h = min(len(matches) * 28 + 4, 200)
            self._animate_height(44 + list_h + 8)
        else:
            self._results.setVisible(False)
            self._animate_height(44)

    def _animate_height(self, target: int) -> None:
        anim = QPropertyAnimation(self, b"maximumHeight")
        anim.setDuration(150)
        anim.setStartValue(self.height())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._h_anim = anim

        anim2 = QPropertyAnimation(self, b"minimumHeight")
        anim2.setDuration(150)
        anim2.setStartValue(self.height())
        anim2.setEndValue(target)
        anim2.setEasingCurve(QEasingCurve.OutCubic)
        anim2.start()
        self._h_anim2 = anim2

    def _select_top(self) -> None:
        if self._results.count() > 0:
            tag = self._results.item(0).data(Qt.UserRole)
            self.page_selected.emit(tag)
            self._input.clear()
            self._results.setVisible(False)
            self._animate_height(44)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        tag = item.data(Qt.UserRole)
        self.page_selected.emit(tag)
        self._input.clear()
        self._results.setVisible(False)
        self._animate_height(44)


class Sidebar(QFrame):
    """Collapsible left navigation rail with categorised groups."""

    page_changed = Signal(str)
    collapse_toggled = Signal(bool)  # True = collapsed

    # Categories: (label, [(icon, name, tag), ...])
    CATEGORIES = [
        (None, [
            ("🏠", "Home", "home"),
        ]),
        ("DEVELOP", [
            ("📝", "Develop",   "develop"),
        ]),
        ("EXECUTE", [
            ("▶",  "Execute",   "execute"),
        ]),
        ("TOOLS", [
            ("🔧", "Tools",     "tools"),
        ]),
        ("STORE", [
            ("🏪", "Store",     "store"),
        ]),
        ("CONFIGURE", [
            ("⚙",  "Configure", "configure"),
        ]),
    ]

    EXPANDED_WIDTH = 200
    COLLAPSED_WIDTH = 54

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(self.EXPANDED_WIDTH)
        self._buttons: list[SidebarButton] = []
        self._category_labels: list[SidebarCategoryLabel] = []
        self._collapsed = False
        self._build()

    @property
    def collapsed(self) -> bool:
        return self._collapsed

    def _build(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(2)
        self.setLayout(layout)

        # Collapse / expand toggle
        self._toggle_btn = QPushButton("☰")
        self._toggle_btn.setObjectName("SidebarCollapseBtn")
        self._toggle_btn.setCursor(Qt.PointingHandCursor)
        self._toggle_btn.setFixedSize(36, 30)
        self._toggle_btn.setToolTip("Collapse sidebar")
        self._toggle_btn.clicked.connect(self.toggle_collapse)

        self._search_btn = QPushButton("🔍")
        self._search_btn.setObjectName("SidebarCollapseBtn")
        self._search_btn.setCursor(Qt.PointingHandCursor)
        self._search_btn.setFixedSize(36, 30)
        self._search_btn.setToolTip("Search pages")
        self._search_btn.clicked.connect(self._toggle_search)

        toggle_row = QHBoxLayout()
        toggle_row.setContentsMargins(10, 0, 10, 4)
        toggle_row.addWidget(self._toggle_btn)
        toggle_row.addStretch()
        toggle_row.addWidget(self._search_btn)
        layout.addLayout(toggle_row)

        # Search bar (animated)
        self._search_bar = SidebarSearchBar(self)
        self._search_bar.page_selected.connect(lambda tag: self.page_changed.emit(tag))
        layout.addWidget(self._search_bar)

        for cat_label, pages in self.CATEGORIES:
            if cat_label:
                lbl = SidebarCategoryLabel(cat_label, self)
                layout.addWidget(lbl)
                self._category_labels.append(lbl)

            for icon, label, tag in pages:
                btn = SidebarButton(icon, label, tag, self)
                btn.clicked.connect(lambda checked, t=tag: self._on_click(t))
                layout.addWidget(btn)
                self._buttons.append(btn)

        layout.addStretch(1)

        # Version badge at bottom
        self._ver = QLabel("Minescript v5.0")
        self._ver.setObjectName("SidebarVersion")
        self._ver.setAlignment(Qt.AlignCenter)
        self._ver.setContentsMargins(0, 0, 0, 8)
        layout.addWidget(self._ver)

        # Select home by default
        self.select("home")

    def toggle_collapse(self) -> None:
        self._collapsed = not self._collapsed
        target = self.COLLAPSED_WIDTH if self._collapsed else self.EXPANDED_WIDTH

        anim = QPropertyAnimation(self, b"minimumWidth")
        anim.setDuration(180)
        anim.setStartValue(self.width())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.start()
        self._anim_w = anim  # prevent GC

        anim2 = QPropertyAnimation(self, b"maximumWidth")
        anim2.setDuration(180)
        anim2.setStartValue(self.width())
        anim2.setEndValue(target)
        anim2.setEasingCurve(QEasingCurve.InOutQuad)
        anim2.start()
        self._anim_w2 = anim2

        for btn in self._buttons:
            btn.set_collapsed(self._collapsed)
        for lbl in self._category_labels:
            lbl.setVisible(not self._collapsed)
        self._ver.setVisible(not self._collapsed)
        self._search_btn.setVisible(not self._collapsed)
        self._search_bar.set_collapsed(self._collapsed)
        self._toggle_btn.setToolTip("Expand sidebar" if self._collapsed else "Collapse sidebar")

        self.collapse_toggled.emit(self._collapsed)

    def _toggle_search(self) -> None:
        if not self._collapsed:
            self._search_bar.toggle()

    def set_collapsed(self, collapsed: bool) -> None:
        """Restore collapsed state without animation."""
        if collapsed != self._collapsed:
            self._collapsed = collapsed
            w = self.COLLAPSED_WIDTH if collapsed else self.EXPANDED_WIDTH
            self.setFixedWidth(w)
            for btn in self._buttons:
                btn.set_collapsed(collapsed)
            for lbl in self._category_labels:
                lbl.setVisible(not collapsed)
            self._ver.setVisible(not collapsed)

    def _on_click(self, tag: str) -> None:
        self.select(tag)
        self.page_changed.emit(tag)

    def select(self, tag: str) -> None:
        for btn in self._buttons:
            btn.setChecked(btn.tag == tag)
