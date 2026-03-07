"""
ScriptCreator — a dialog for creating / editing a script's metadata.
Lets you set icon, name, version, description, author, tags, pinned state.
"""

import time
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFrame, QGraphicsOpacityEffect,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QTextEdit, QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS
from . import script_manifest as manifest
from .script_manifest import SCRIPT_ICONS


class IconPicker(QFrame):
    """Grid of clickable emoji icons."""

    icon_selected = Signal(str)

    def __init__(self, current: str = "📜", parent=None):
        super().__init__(parent)
        self.setObjectName("IconPicker")
        self._current = current
        self._buttons: list[QPushButton] = []
        self._build()

    def _build(self) -> None:
        grid = QGridLayout()
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setSpacing(4)
        self.setLayout(grid)

        for i, icon in enumerate(SCRIPT_ICONS):
            btn = QPushButton(icon)
            btn.setObjectName("IconPickerButton")
            btn.setFixedSize(36, 36)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.setChecked(icon == self._current)
            btn.clicked.connect(lambda checked, ic=icon: self._pick(ic))
            grid.addWidget(btn, i // 6, i % 6)
            self._buttons.append(btn)

    def _pick(self, icon: str) -> None:
        self._current = icon
        for btn in self._buttons:
            btn.setChecked(btn.text() == icon)
        self.icon_selected.emit(icon)

    def current_icon(self) -> str:
        return self._current


class ScriptCreatorDialog(QDialog):
    """Dialog to create a new script or edit existing script metadata."""

    script_created = Signal(str)   # emits script path
    script_updated = Signal(str)   # emits script path

    def __init__(self, scripts_root: str, edit_path: str | None = None, parent=None):
        super().__init__(parent)
        self._root = scripts_root
        self._edit_path = edit_path
        self._is_edit = edit_path is not None
        self.setWindowTitle("Edit Script" if self._is_edit else "Create New Script")
        self.setMinimumSize(520, 520)
        self.setObjectName("ScriptCreatorDialog")
        self._build()
        if self._is_edit:
            self._load_existing()

    def showEvent(self, event):
        super().showEvent(event)
        # Smooth fade-in
        eff = QGraphicsOpacityEffect(self)
        eff.setOpacity(0.0)
        self.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity")
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._fade_anim = anim

    def _build(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(14)
        self.setLayout(layout)

        # Title
        title = QLabel("✨  Edit Script Metadata" if self._is_edit else "✨  Create New Script")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)

        # Icon picker
        icon_label = QLabel("Choose Icon:")
        icon_label.setObjectName("FieldLabel")
        layout.addWidget(icon_label)

        self._icon_picker = IconPicker("📜")
        layout.addWidget(self._icon_picker)

        # Form fields
        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        row = 0

        if not self._is_edit:
            form.addWidget(self._label("Filename:"), row, 0)
            self._filename = QLineEdit()
            self._filename.setObjectName("SettingsInput")
            self._filename.setPlaceholderText("my_script.py")
            form.addWidget(self._filename, row, 1)
            row += 1
        else:
            self._filename = None

        form.addWidget(self._label("Name:"), row, 0)
        self._name = QLineEdit()
        self._name.setObjectName("SettingsInput")
        self._name.setPlaceholderText("My Awesome Script")
        form.addWidget(self._name, row, 1)
        row += 1

        form.addWidget(self._label("Version:"), row, 0)
        self._version = QLineEdit()
        self._version.setObjectName("SettingsInput")
        self._version.setText("1.0.0")
        form.addWidget(self._version, row, 1)
        row += 1

        form.addWidget(self._label("Author:"), row, 0)
        self._author = QLineEdit()
        self._author.setObjectName("SettingsInput")
        form.addWidget(self._author, row, 1)
        row += 1

        form.addWidget(self._label("Tags:"), row, 0)
        self._tags = QLineEdit()
        self._tags.setObjectName("SettingsInput")
        self._tags.setPlaceholderText("utility, blocks, automation  (comma-separated)")
        form.addWidget(self._tags, row, 1)
        row += 1

        layout.addLayout(form)

        # Description
        desc_label = QLabel("Description:")
        desc_label.setObjectName("FieldLabel")
        layout.addWidget(desc_label)

        self._description = QTextEdit()
        self._description.setObjectName("DescriptionInput")
        self._description.setPlaceholderText("What does this script do?")
        self._description.setFixedHeight(80)
        layout.addWidget(self._description)

        # Checkboxes
        checks = QHBoxLayout()
        checks.setSpacing(16)

        self._pinned = QCheckBox("Pin to Front Page")
        self._pinned.setObjectName("SettingsCheck")
        self._pinned.setChecked(True)
        checks.addWidget(self._pinned)

        self._enabled = QCheckBox("Enabled")
        self._enabled.setObjectName("SettingsCheck")
        self._enabled.setChecked(True)
        checks.addWidget(self._enabled)

        checks.addStretch()
        layout.addLayout(checks)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("EditorToolButton")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save" if self._is_edit else "Create")
        save_btn.setObjectName("AccentButton")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("FieldLabel")
        lbl.setFixedWidth(80)
        return lbl

    def _load_existing(self) -> None:
        meta = manifest.get_meta(self._edit_path)
        self._name.setText(meta.get("name", ""))
        self._version.setText(meta.get("version", "1.0.0"))
        self._author.setText(meta.get("author", ""))
        self._tags.setText(", ".join(meta.get("tags", [])))
        self._description.setPlainText(meta.get("description", ""))
        self._pinned.setChecked(meta.get("pinned", False))
        self._enabled.setChecked(meta.get("enabled", True))
        self._icon_picker._pick(meta.get("icon", "📜"))

    def _collect_meta(self) -> dict:
        tags_raw = self._tags.text().strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
        return {
            "name": self._name.text().strip() or "Untitled",
            "description": self._description.toPlainText().strip(),
            "icon": self._icon_picker.current_icon(),
            "version": self._version.text().strip() or "1.0.0",
            "author": self._author.text().strip(),
            "tags": tags,
            "enabled": self._enabled.isChecked(),
            "pinned": self._pinned.isChecked(),
        }

    def _on_save(self) -> None:
        meta = self._collect_meta()

        if self._is_edit:
            # Update existing
            existing = manifest.get_meta(self._edit_path)
            existing.update(meta)
            manifest.set_meta(self._edit_path, existing)
            self.script_updated.emit(self._edit_path)
            self.accept()
        else:
            # Create new file
            filename = self._filename.text().strip()
            if not filename:
                return
            if not filename.endswith((".py", ".pyj")):
                filename += ".py"
            path = Path(self._root) / filename
            if path.exists():
                self._filename.setStyleSheet(f"border-color: {COLORS['danger']};")
                return
            try:
                boilerplate = (
                    f'# {meta["name"]}\n'
                    f'# Version: {meta["version"]}\n'
                    f'# Author: {meta["author"]}\n'
                    f'# {meta["description"]}\n'
                    f'\nimport minescript\n\n'
                )
                path.write_text(boilerplate, encoding="utf-8")
                meta["created_ts"] = time.time()
                manifest.set_meta(str(path), meta)
                self.script_created.emit(str(path))
                self.accept()
            except Exception:
                pass
