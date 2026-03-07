"""
FileTree — directory tree panel for browsing the scripts workspace.
Supports expand/collapse, file icons, context menu, and drag-to-open.
"""

import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QInputDialog,
    QMessageBox,
)

from ..Colors.palette import COLORS


_ICON_MAP = {
    ".py": "🐍",
    ".pyj": "⚡",
    ".json": "📋",
    ".txt": "📄",
    ".md": "📝",
    ".toml": "⚙",
    ".yaml": "⚙",
    ".yml": "⚙",
    ".zip": "📦",
    ".log": "📜",
}


class FileTreePanel(QFrame):
    """File system tree browser for the scripts workspace."""

    file_selected = Signal(str)       # open file in editor
    file_renamed = Signal(str, str)   # old_path, new_path
    file_deleted = Signal(str)        # deleted file path
    file_created = Signal(str)        # new file path

    def __init__(self, root_dir: str, parent=None):
        super().__init__(parent)
        self.setObjectName("FileTreePanel")
        self._root = root_dir
        self._build()
        self.refresh()

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

        title = QLabel("📂 File Explorer")
        title.setObjectName("PanelTitle")
        hl.addWidget(title)
        hl.addStretch()

        refresh_btn = QPushButton("↻")
        refresh_btn.setObjectName("SmallButton")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setToolTip("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        hl.addWidget(refresh_btn)

        new_btn = QPushButton("+")
        new_btn.setObjectName("SmallButton")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setToolTip("New file")
        new_btn.clicked.connect(self._new_file)
        hl.addWidget(new_btn)

        layout.addWidget(header)

        # Search
        self._search = QLineEdit()
        self._search.setObjectName("SearchInput")
        self._search.setPlaceholderText("Filter files…")
        self._search.setContentsMargins(8, 4, 8, 4)
        self._search.textChanged.connect(self._apply_filter)
        layout.addWidget(self._search)

        # Tree
        self._tree = QTreeWidget()
        self._tree.setObjectName("FileTree")
        self._tree.setHeaderHidden(True)
        self._tree.setAnimated(True)
        self._tree.setIndentation(16)
        self._tree.setRootIsDecorated(True)
        self._tree.itemDoubleClicked.connect(self._on_double_click)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._context_menu)
        self._tree.setStyleSheet(f"""
            QTreeWidget {{
                background: {COLORS.get('bg_surface', '#16162e')};
                color: {COLORS.get('text_primary', '#e8e6f0')};
                border: none;
                font-family: 'Segoe UI';
                font-size: 11px;
            }}
            QTreeWidget::item {{
                padding: 3px 4px;
            }}
            QTreeWidget::item:selected {{
                background: {COLORS.get('accent', '#7c6aef')};
                color: white;
                border-radius: 3px;
            }}
            QTreeWidget::item:hover {{
                background: {COLORS.get('bg_hover', '#1e1e3a')};
            }}
            QTreeWidget::branch {{
                background: transparent;
            }}
        """)
        layout.addWidget(self._tree, 1)

        # Info
        self._info = QLabel("0 files")
        self._info.setObjectName("BrowserInfo")
        self._info.setContentsMargins(10, 4, 10, 4)
        layout.addWidget(self._info)

    def refresh(self):
        self._tree.clear()
        root_path = Path(self._root)
        if not root_path.is_dir():
            return

        file_count = [0]
        root_item = QTreeWidgetItem(self._tree, [f"📁 {root_path.name}"])
        root_item.setData(0, Qt.UserRole, str(root_path))
        root_item.setExpanded(True)
        self._populate(root_item, root_path, file_count)
        self._info.setText(f"{file_count[0]} files")

    def _populate(self, parent_item: QTreeWidgetItem, path: Path, count: list):
        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return

        for entry in entries:
            if entry.name.startswith((".", "__pycache__")):
                continue
            if entry.is_dir():
                folder_item = QTreeWidgetItem(parent_item, [f"📁 {entry.name}"])
                folder_item.setData(0, Qt.UserRole, str(entry))
                self._populate(folder_item, entry, count)
            else:
                ext = entry.suffix.lower()
                icon = _ICON_MAP.get(ext, "📄")
                file_item = QTreeWidgetItem(parent_item, [f"{icon} {entry.name}"])
                file_item.setData(0, Qt.UserRole, str(entry))
                count[0] += 1

    def _apply_filter(self, text: str):
        text = text.strip().lower()

        def _filter_item(item: QTreeWidgetItem) -> bool:
            path = item.data(0, Qt.UserRole)
            name = Path(path).name.lower() if path else ""
            is_match = not text or text in name

            # Check children
            any_child_visible = False
            for i in range(item.childCount()):
                child_visible = _filter_item(item.child(i))
                if child_visible:
                    any_child_visible = True

            visible = is_match or any_child_visible
            item.setHidden(not visible)
            if any_child_visible:
                item.setExpanded(True)
            return visible

        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            _filter_item(root.child(i))

    def _on_double_click(self, item: QTreeWidgetItem, column: int):
        path = item.data(0, Qt.UserRole)
        if path and Path(path).is_file():
            self.file_selected.emit(path)

    def _context_menu(self, pos):
        item = self._tree.itemAt(pos)
        if not item:
            return
        path = item.data(0, Qt.UserRole)
        if not path:
            return

        menu = QMenu(self)
        p = Path(path)

        if p.is_file():
            menu.addAction("Open", lambda: self.file_selected.emit(path))
            menu.addSeparator()
            menu.addAction("Rename", lambda: self._rename_file(path))
            menu.addAction("Duplicate", lambda: self._duplicate_file(path))
            menu.addSeparator()
            menu.addAction("Delete", lambda: self._delete_file(path))
        elif p.is_dir():
            menu.addAction("New File Here", lambda: self._new_file_in(path))
            menu.addAction("New Folder", lambda: self._new_folder_in(path))
            menu.addSeparator()
            menu.addAction("Rename", lambda: self._rename_file(path))
            if str(p) != self._root:
                menu.addAction("Delete Folder", lambda: self._delete_folder(path))

        menu.exec(self._tree.mapToGlobal(pos))

    def _new_file(self):
        self._new_file_in(self._root)

    def _new_file_in(self, directory: str):
        name, ok = QInputDialog.getText(self, "New File", "File name:", text="new_script.py")
        if ok and name:
            new_path = Path(directory) / name
            try:
                new_path.write_text("import minescript\n\n", encoding="utf-8")
                self.file_created.emit(str(new_path))
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _new_folder_in(self, directory: str):
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            try:
                (Path(directory) / name).mkdir(parents=True, exist_ok=True)
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _rename_file(self, path: str):
        p = Path(path)
        name, ok = QInputDialog.getText(self, "Rename", "New name:", text=p.name)
        if ok and name and name != p.name:
            new_path = p.parent / name
            try:
                p.rename(new_path)
                self.file_renamed.emit(path, str(new_path))
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _duplicate_file(self, path: str):
        p = Path(path)
        new_name = f"{p.stem}_copy{p.suffix}"
        new_path = p.parent / new_name
        counter = 1
        while new_path.exists():
            counter += 1
            new_name = f"{p.stem}_copy{counter}{p.suffix}"
            new_path = p.parent / new_name
        try:
            new_path.write_bytes(p.read_bytes())
            self.file_created.emit(str(new_path))
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _delete_file(self, path: str):
        name = Path(path).name
        reply = QMessageBox.question(
            self, "Delete File",
            f"Delete '{name}'?\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                Path(path).unlink(missing_ok=True)
                self.file_deleted.emit(path)
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _delete_folder(self, path: str):
        import shutil
        name = Path(path).name
        reply = QMessageBox.question(
            self, "Delete Folder",
            f"Delete folder '{name}' and ALL contents?\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                shutil.rmtree(path)
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
