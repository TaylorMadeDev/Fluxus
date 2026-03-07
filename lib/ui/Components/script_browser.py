import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS
from .script_card import ScriptCard
from . import script_manifest as manifest


class ScriptBrowser(QFrame):
    """Script browser with card-based UI, search, sort, pin/configure."""

    script_selected = Signal(str)      # open in editor
    run_requested = Signal(str)        # run script
    configure_requested = Signal(str)  # open config dialog
    delete_requested = Signal(str)     # delete script

    EXTENSIONS = {".py", ".pyj"}

    def __init__(self, scripts_root: str | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("ScriptBrowser")
        self._root = scripts_root or str(
            Path(__file__).resolve().parents[3]
        )
        self._all_scripts: list[Path] = []
        self._cards: list[ScriptCard] = []
        self._build()
        self.refresh()

    def _build(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Header
        header = QFrame(self)
        header.setObjectName("BrowserHeader")
        header.setFixedHeight(40)
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(12, 0, 12, 0)
        h_layout.setSpacing(8)
        header.setLayout(h_layout)

        title = QLabel("📁  Scripts")
        title.setObjectName("PanelTitle")
        h_layout.addWidget(title)
        h_layout.addStretch()

        # View toggle
        self._view_cards = True
        self._toggle_btn = QPushButton("☰ List")
        self._toggle_btn.setObjectName("SmallButton")
        self._toggle_btn.setToolTip("Toggle list / card view")
        self._toggle_btn.setCursor(Qt.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._toggle_view)
        h_layout.addWidget(self._toggle_btn)

        refresh_btn = QPushButton("↻")
        refresh_btn.setObjectName("SmallButton")
        refresh_btn.setToolTip("Refresh")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh)
        h_layout.addWidget(refresh_btn)

        new_btn = QPushButton("+")
        new_btn.setObjectName("SmallButton")
        new_btn.setToolTip("New Script")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(self._new_script)
        h_layout.addWidget(new_btn)

        layout.addWidget(header)

        # Search / Sort bar
        filter_bar = QFrame(self)
        filter_bar.setObjectName("FilterBar")
        fb_layout = QHBoxLayout()
        fb_layout.setContentsMargins(10, 6, 10, 6)
        fb_layout.setSpacing(6)
        filter_bar.setLayout(fb_layout)

        self._search = QLineEdit()
        self._search.setObjectName("SearchInput")
        self._search.setPlaceholderText("Search scripts…")
        self._search.textChanged.connect(self._apply_filter)
        fb_layout.addWidget(self._search)

        self._tag_combo = QComboBox()
        self._tag_combo.setObjectName("SortCombo")
        self._tag_combo.addItem("All Tags")
        self._tag_combo.currentIndexChanged.connect(self._apply_filter)
        fb_layout.addWidget(self._tag_combo)

        self._sort_combo = QComboBox()
        self._sort_combo.setObjectName("SortCombo")
        self._sort_combo.addItems(["Name ↑", "Name ↓", "Modified ↑", "Modified ↓", "Size ↑", "Size ↓", "Most Used"])
        self._sort_combo.currentIndexChanged.connect(self._apply_filter)
        fb_layout.addWidget(self._sort_combo)

        self._fav_btn = QPushButton("★")
        self._fav_btn.setObjectName("SmallButton")
        self._fav_btn.setToolTip("Show favorites only")
        self._fav_btn.setCursor(Qt.PointingHandCursor)
        self._fav_btn.setCheckable(True)
        self._fav_btn.setFixedWidth(28)
        self._fav_btn.clicked.connect(self._apply_filter)
        fb_layout.addWidget(self._fav_btn)

        layout.addWidget(filter_bar)

        # Card scroll area
        self._scroll = QScrollArea(self)
        self._scroll.setObjectName("BrowserScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._card_container = QWidget()
        self._card_container.setObjectName("FrontPageContainer")
        self._card_layout = QVBoxLayout()
        self._card_layout.setContentsMargins(10, 10, 10, 10)
        self._card_layout.setSpacing(8)
        self._card_container.setLayout(self._card_layout)
        self._scroll.setWidget(self._card_container)

        # List view (hidden by default)
        self._list = QListWidget()
        self._list.setObjectName("ScriptList")
        self._list.itemDoubleClicked.connect(self._on_item_double_click)
        self._list.setVisible(False)

        layout.addWidget(self._scroll, 1)
        layout.addWidget(self._list, 1)

        # Info footer
        self._info = QLabel("0 scripts")
        self._info.setObjectName("BrowserInfo")
        self._info.setContentsMargins(12, 4, 12, 6)
        layout.addWidget(self._info)

    def refresh(self) -> None:
        self._all_scripts = []
        root = Path(self._root)
        if root.is_dir():
            for f in root.rglob("*"):
                if f.suffix in self.EXTENSIONS and f.is_file():
                    self._all_scripts.append(f)

        # Populate tag filter dynamically
        all_tags: set[str] = set()
        for s in self._all_scripts:
            meta = manifest.get_meta(str(s))
            for t in meta.get("tags", []):
                all_tags.add(t)
        self._tag_combo.blockSignals(True)
        current = self._tag_combo.currentText()
        self._tag_combo.clear()
        self._tag_combo.addItem("All Tags")
        for t in sorted(all_tags):
            self._tag_combo.addItem(t)
        idx = self._tag_combo.findText(current)
        if idx >= 0:
            self._tag_combo.setCurrentIndex(idx)
        self._tag_combo.blockSignals(False)

        self._apply_filter()

    def _apply_filter(self) -> None:
        query = self._search.text().lower().strip()
        sort_mode = self._sort_combo.currentText()
        tag_filter = self._tag_combo.currentText()
        show_fav_only = self._fav_btn.isChecked()

        filtered = []
        for s in self._all_scripts:
            path_str = str(s)
            meta = manifest.get_meta(path_str)

            # Text search
            if query and query not in s.name.lower():
                try:
                    rel = str(s.relative_to(self._root)).lower()
                except ValueError:
                    rel = ""
                if query not in rel:
                    continue

            # Tag filter
            if tag_filter != "All Tags" and tag_filter not in meta.get("tags", []):
                continue

            # Favorites filter
            if show_fav_only and not meta.get("favorite", False):
                continue

            filtered.append(s)

        key_map = {
            "Name ↑": lambda p: p.name.lower(),
            "Name ↓": lambda p: p.name.lower(),
            "Modified ↑": lambda p: p.stat().st_mtime,
            "Modified ↓": lambda p: p.stat().st_mtime,
            "Size ↑": lambda p: p.stat().st_size,
            "Size ↓": lambda p: p.stat().st_size,
            "Most Used": lambda p: manifest.get_meta(str(p)).get("run_count", 0),
        }
        reverse = "↓" in sort_mode or sort_mode == "Most Used"
        try:
            filtered.sort(key=key_map.get(sort_mode, lambda p: p.name.lower()), reverse=reverse)
        except Exception:
            pass

        # ---- Card view ----
        self._cards.clear()
        while self._card_layout.count():
            child = self._card_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for script in filtered:
            path_str = str(script)
            meta = manifest.get_meta(path_str)
            card = ScriptCard(path_str, meta)
            card.run_clicked.connect(self.run_requested.emit)
            card.edit_clicked.connect(self.script_selected.emit)
            card.configure_clicked.connect(self.configure_requested.emit)
            card.delete_clicked.connect(self._delete_script)
            card.favorite_clicked.connect(self._toggle_favorite)
            # Click card body to open in editor
            self._cards.append(card)
            self._card_layout.addWidget(card)

        self._card_layout.addStretch()

        # ---- List view ----
        self._list.clear()
        for script in filtered:
            try:
                rel = script.relative_to(self._root)
            except ValueError:
                rel = script
            item = QListWidgetItem(f"  {rel}")
            item.setData(Qt.UserRole, str(script))
            item.setToolTip(str(script))
            self._list.addItem(item)

        self._info.setText(f"{len(filtered)} script{'s' if len(filtered) != 1 else ''}")

    def _toggle_view(self) -> None:
        self._view_cards = not self._view_cards
        self._scroll.setVisible(self._view_cards)
        self._list.setVisible(not self._view_cards)
        self._toggle_btn.setText("☰ List" if self._view_cards else "▦ Cards")

    def _delete_script(self, path: str) -> None:
        """Delete a script file after confirmation."""
        name = Path(path).name
        reply = QMessageBox.question(
            self, "Delete Script",
            f"Are you sure you want to delete '{name}'?\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                Path(path).unlink(missing_ok=True)
                manifest.delete_meta(path)
                self.delete_requested.emit(path)
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete: {e}")

    def _toggle_script(self, path: str) -> None:
        meta = manifest.get_meta(path)
        meta["enabled"] = not meta.get("enabled", True)
        manifest.set_meta(path, meta)
        self._apply_filter()

    def _toggle_favorite(self, path: str) -> None:
        manifest.toggle_favorite(path)
        self._apply_filter()

    def _on_item_double_click(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.UserRole)
        if path:
            self.script_selected.emit(path)

    def _new_script(self) -> None:
        from .script_creator import ScriptCreatorDialog
        dlg = ScriptCreatorDialog(self._root, parent=self)
        dlg.script_created.connect(lambda p: (self.refresh(), self.script_selected.emit(p)))
        dlg.exec()
