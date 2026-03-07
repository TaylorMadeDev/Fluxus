"""
Plugins Panel — manage, toggle, and import editor plugins (.py files).

Scans the plugins/ directory for .py files and displays them alongside
built-in plugins.  Provides enable/disable toggle, delete, and a
checkbox-based import dialog for the code editor.
"""

import os
import shutil
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS
from .plugins import get_plugin_registry, BUILTIN_PLUGINS, _PLUGINS_DIR


# ── Plugin Card ────────────────────────────────────────────────────

class PluginCard(QFrame):
    """Visual card for a single plugin."""

    toggled = Signal(str, bool)    # plugin_id, enabled
    delete_clicked = Signal(str)   # plugin_id

    def __init__(self, plugin_id: str, data: dict, is_builtin: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("PluginCard")
        self.plugin_id = plugin_id
        self._data = data
        self._is_builtin = is_builtin
        self.setFixedHeight(90)
        self.setStyleSheet(
            f"QFrame#PluginCard {{"
            f"  background: {COLORS['bg_surface']};"
            f"  border: 1px solid {COLORS['border']};"
            f"  border-radius: 8px;"
            f"  margin: 2px 4px;"
            f"}}"
            f"QFrame#PluginCard:hover {{"
            f"  border-color: {COLORS['accent_dim']};"
            f"}}"
        )

        layout = QHBoxLayout()
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)
        self.setLayout(layout)

        # Icon
        icon = QLabel("🔌")
        icon.setFixedWidth(28)
        icon.setStyleSheet("font-size: 20px; border: none;")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        # Info column
        info = QVBoxLayout()
        info.setSpacing(2)

        name_row = QHBoxLayout()
        name_row.setSpacing(6)
        name_lbl = QLabel(data.get("name", plugin_id))
        name_lbl.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-weight: 700; font-size: 13px;"
            f" font-family: 'Segoe UI'; border: none;"
        )
        name_row.addWidget(name_lbl)

        ver_lbl = QLabel(f"v{data.get('version', '?')}")
        ver_lbl.setStyleSheet(
            f"color: {COLORS['accent']}; font-size: 10px; font-weight: 600;"
            f" font-family: 'Segoe UI'; border: none;"
        )
        name_row.addWidget(ver_lbl)

        if is_builtin:
            badge = QLabel("Built-in")
            badge.setStyleSheet(
                f"color: {COLORS['success']}; font-size: 9px; font-weight: 700;"
                f" font-family: 'Segoe UI'; border: none;"
            )
            name_row.addWidget(badge)

        name_row.addStretch()
        info.addLayout(name_row)

        desc = QLabel(data.get("description", "No description"))
        desc.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; font-family: 'Segoe UI'; border: none;"
        )
        desc.setWordWrap(True)
        info.addWidget(desc)

        # Source file info
        source = data.get("_source_file", "")
        src_text = f"📄 {os.path.basename(source)}" if source else ""
        comps = len(data.get("completions", []))
        snips = len(data.get("snippets", {}))
        meta = QLabel(f"{src_text}  •  {comps} completions  •  {snips} snippets")
        meta.setStyleSheet(
            f"color: {COLORS['text_dim']}; font-size: 10px; font-family: 'Segoe UI'; border: none;"
        )
        info.addWidget(meta)

        layout.addLayout(info, 1)

        # Enable toggle
        self._toggle = QCheckBox("Enabled")
        self._toggle.setChecked(data.get("enabled", True))
        self._toggle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        self._toggle.toggled.connect(lambda checked: self.toggled.emit(plugin_id, checked))
        layout.addWidget(self._toggle, 0, Qt.AlignVCenter)

        # Delete button (only non-builtin)
        if not self._is_builtin:
            del_btn = QPushButton("🗑")
            del_btn.setObjectName("DangerSmallButton")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setFixedSize(28, 28)
            del_btn.setToolTip("Delete plugin")
            del_btn.clicked.connect(lambda: self.delete_clicked.emit(plugin_id))
            layout.addWidget(del_btn, 0, Qt.AlignVCenter)


# ── Import Plugins Dialog (checkbox popup) ─────────────────────────

class PluginImportDialog(QDialog):
    """Popup with checkboxes for all available plugins to import into the editor."""

    import_selected = Signal(list)  # list of import lines

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Plugins")
        self.setFixedSize(440, 400)
        self.setStyleSheet(
            f"QDialog {{ background: {COLORS['bg_root']}; }}"
            f"QLabel {{ color: {COLORS['text_primary']}; font-family: 'Segoe UI'; }}"
        )
        self._checks: list[tuple[QCheckBox, str]] = []
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)
        self.setLayout(layout)

        title = QLabel("📦  Select Plugins to Import")
        title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {COLORS['accent']};")
        layout.addWidget(title)

        hint = QLabel("Check the plugins you want and their import lines will be inserted at the top of your file.")
        hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # Scrollable plugin list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        form = QVBoxLayout()
        form.setContentsMargins(0, 4, 0, 4)
        form.setSpacing(6)
        container.setLayout(form)

        registry = get_plugin_registry()
        all_plugins = registry.get_all_plugins()

        for pid, data in all_plugins.items():
            import_line = data.get("import_line", "")
            if not import_line:
                continue

            row = QFrame()
            row.setStyleSheet(
                f"QFrame {{ background: {COLORS['bg_surface']};"
                f" border: 1px solid {COLORS['border']}; border-radius: 6px; }}"
            )
            rl = QHBoxLayout()
            rl.setContentsMargins(12, 8, 12, 8)
            rl.setSpacing(10)
            row.setLayout(rl)

            cb = QCheckBox()
            cb.setChecked(data.get("enabled", True))
            rl.addWidget(cb)

            info_col = QVBoxLayout()
            info_col.setSpacing(1)
            name_lbl = QLabel(data.get("name", pid))
            name_lbl.setStyleSheet(
                f"color: {COLORS['text_primary']}; font-weight: 600; font-size: 12px; border: none;"
            )
            info_col.addWidget(name_lbl)

            import_lbl = QLabel(import_line)
            import_lbl.setStyleSheet(
                f"color: {COLORS['text_muted']}; font-size: 10px; font-family: 'Consolas'; border: none;"
            )
            info_col.addWidget(import_lbl)
            rl.addLayout(info_col, 1)

            form.addWidget(row)
            self._checks.append((cb, import_line))

        form.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        sel_all = QPushButton("Select All")
        sel_all.setObjectName("SmallButton")
        sel_all.setCursor(Qt.PointingHandCursor)
        sel_all.clicked.connect(lambda: [cb.setChecked(True) for cb, _ in self._checks])
        btn_row.addWidget(sel_all)

        desel_all = QPushButton("Deselect All")
        desel_all.setObjectName("SmallButton")
        desel_all.setCursor(Qt.PointingHandCursor)
        desel_all.clicked.connect(lambda: [cb.setChecked(False) for cb, _ in self._checks])
        btn_row.addWidget(desel_all)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("SmallButton")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        insert_btn = QPushButton("Insert Selected")
        insert_btn.setObjectName("AccentButton")
        insert_btn.setCursor(Qt.PointingHandCursor)
        insert_btn.clicked.connect(self._on_insert)
        btn_row.addWidget(insert_btn)

        layout.addLayout(btn_row)

    def _on_insert(self) -> None:
        selected = [line for cb, line in self._checks if cb.isChecked()]
        self.import_selected.emit(selected)
        self.accept()


# ── Plugins Panel ──────────────────────────────────────────────────

class PluginsPanel(QFrame):
    """Panel for managing editor plugins — view, toggle, import, delete."""

    plugins_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PluginsPanel")
        self._build()
        self.refresh()

    def _build(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Header
        header = QFrame(self)
        header.setObjectName("PackagesHeader")
        header.setFixedHeight(40)
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(12, 0, 12, 0)
        h_layout.setSpacing(8)
        header.setLayout(h_layout)

        title = QLabel("🔌  Plugins")
        title.setObjectName("PanelTitle")
        h_layout.addWidget(title)
        h_layout.addStretch()

        import_btn = QPushButton("+ Import .py")
        import_btn.setObjectName("SmallButton")
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.setToolTip("Import a plugin .py file")
        import_btn.clicked.connect(self._import_plugin)
        h_layout.addWidget(import_btn)

        refresh_btn = QPushButton("↻")
        refresh_btn.setObjectName("SmallButton")
        refresh_btn.setToolTip("Refresh")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh)
        h_layout.addWidget(refresh_btn)

        layout.addWidget(header)

        # Info bar
        info = QLabel("  Plugins extend the editor with additional completions, imports, and snippets.")
        info.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; font-family: 'Segoe UI';"
            f" padding: 6px 12px; background: {COLORS['bg_surface']};"
            f" border-bottom: 1px solid {COLORS['border']};"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Plugin list (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setObjectName("PluginsScroll")

        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout()
        self._list_layout.setContentsMargins(8, 8, 8, 8)
        self._list_layout.setSpacing(6)
        self._list_layout.setAlignment(Qt.AlignTop)
        self._list_widget.setLayout(self._list_layout)
        scroll.setWidget(self._list_widget)
        layout.addWidget(scroll, 1)

        # Drag & drop hint
        hint = QLabel("💡 Drag-and-drop a .py plugin file to import it")
        hint.setStyleSheet(
            f"color: {COLORS['text_dim']}; font-size: 10px; font-family: 'Segoe UI';"
            f" padding: 6px 12px;"
        )
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        self.setAcceptDrops(True)

    def refresh(self) -> None:
        """Reload all plugins and rebuild the card list."""
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        registry = get_plugin_registry()
        registry._load_user_plugins()
        plugins = registry.get_all_plugins()

        # Also scan for .py files that aren't in the registry yet
        if _PLUGINS_DIR.exists():
            for f in _PLUGINS_DIR.iterdir():
                if f.suffix == ".py" and f.stem not in plugins:
                    plugins[f.stem] = {
                        "name": f.stem,
                        "description": f"Plugin file: {f.name}",
                        "version": "—",
                        "import_line": f"import {f.stem}",
                        "completions": [],
                        "api_entries": [],
                        "snippets": {},
                        "enabled": True,
                        "_source_file": str(f),
                    }

        for pid, data in plugins.items():
            is_builtin = pid in BUILTIN_PLUGINS
            if "_source_file" not in data:
                py_path = _PLUGINS_DIR / f"{pid}.py"
                if py_path.exists():
                    data["_source_file"] = str(py_path)
            card = PluginCard(pid, data, is_builtin=is_builtin)
            card.toggled.connect(self._on_toggle)
            card.delete_clicked.connect(self._delete_plugin)
            self._list_layout.addWidget(card)

        if not plugins:
            empty = QLabel("No plugins installed yet.\nClick '+ Import .py' to add one!")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(
                f"color: {COLORS['text_dim']}; font-size: 12px; padding: 40px;"
            )
            self._list_layout.addWidget(empty)

    def _on_toggle(self, plugin_id: str, enabled: bool) -> None:
        registry = get_plugin_registry()
        registry.set_enabled(plugin_id, enabled)
        self.plugins_changed.emit()

    def _delete_plugin(self, plugin_id: str) -> None:
        if plugin_id in BUILTIN_PLUGINS:
            QMessageBox.information(self, "Cannot Delete", "Built-in plugins cannot be deleted.")
            return
        reply = QMessageBox.question(
            self, "Delete Plugin",
            f"Delete plugin '{plugin_id}'?\n\nThis removes the file from the plugins folder.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        for ext in (".py", ".pyj", ".json"):
            p = _PLUGINS_DIR / f"{plugin_id}{ext}"
            if p.exists():
                p.unlink()
        registry = get_plugin_registry()
        registry._plugins.pop(plugin_id, None)
        self.refresh()
        self.plugins_changed.emit()

    def _import_plugin(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Plugin", "", "Python Files (*.py);;All Files (*)"
        )
        if path:
            self._install_plugin_file(path)

    def _install_plugin_file(self, src_path: str) -> None:
        src = Path(src_path)
        if not src.exists():
            return
        if src.suffix not in (".py", ".pyj"):
            QMessageBox.warning(self, "Invalid File", "Plugins must be .py files.")
            return
        dest = _PLUGINS_DIR / src.name
        _PLUGINS_DIR.mkdir(exist_ok=True)
        shutil.copy2(str(src), str(dest))
        self.refresh()
        self.plugins_changed.emit()

    # Drag & Drop
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith((".py", ".pyj")):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.endswith((".py", ".pyj")):
                self._install_plugin_file(path)
