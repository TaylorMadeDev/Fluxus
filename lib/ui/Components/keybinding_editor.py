"""
Keybinding Editor — visual editor for keyboard shortcuts.
Allows viewing, editing, and resetting keybindings.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS
from .shortcuts import ShortcutManager, DEFAULTS, load_shortcuts, save_shortcuts


class _KeyBindRow(QFrame):
    """Single row showing action name + key binding + edit button."""

    binding_changed = Signal(str, str)  # action, new_key

    def __init__(self, action: str, key: str, parent=None):
        super().__init__(parent)
        self.action = action
        self._key = key
        self._recording = False
        self._build()

    def _build(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        self.setLayout(layout)

        # Action name
        nice_name = self.action.replace("_", " ").title()
        self._name_lbl = QLabel(nice_name)
        self._name_lbl.setFixedWidth(200)
        self._name_lbl.setStyleSheet(
            f"color: {COLORS.get('text_primary', '#e8e6f0')};"
            f" font-size: 11px; font-weight: 600;"
        )
        layout.addWidget(self._name_lbl)

        # Key display
        self._key_lbl = QLabel(self._key)
        self._key_lbl.setFixedWidth(140)
        self._key_lbl.setAlignment(Qt.AlignCenter)
        self._key_lbl.setStyleSheet(
            f"color: {COLORS.get('accent', '#7c6aef')};"
            f" font-family: Consolas; font-size: 11px;"
            f" background: {COLORS.get('bg_root', '#0e0e1e')};"
            f" border: 1px solid {COLORS.get('border', '#2a2a4a')};"
            f" border-radius: 4px; padding: 4px;"
        )
        layout.addWidget(self._key_lbl)

        # Edit button
        self._edit_btn = QPushButton("Edit")
        self._edit_btn.setObjectName("SmallButton")
        self._edit_btn.setCursor(Qt.PointingHandCursor)
        self._edit_btn.setFixedWidth(50)
        self._edit_btn.clicked.connect(self._start_recording)
        layout.addWidget(self._edit_btn)

        # Reset to default
        default_key = DEFAULTS.get(self.action, "")
        if default_key != self._key:
            reset_btn = QPushButton("↩")
            reset_btn.setObjectName("SmallButton")
            reset_btn.setCursor(Qt.PointingHandCursor)
            reset_btn.setToolTip(f"Reset to default: {default_key}")
            reset_btn.setFixedWidth(28)
            reset_btn.clicked.connect(self._reset_to_default)
            layout.addWidget(reset_btn)

        layout.addStretch()

    def _start_recording(self):
        self._recording = True
        self._key_lbl.setText("Press a key…")
        self._key_lbl.setStyleSheet(
            f"color: {COLORS.get('warning', '#f0a030')};"
            f" font-family: Consolas; font-size: 11px;"
            f" background: {COLORS.get('bg_root', '#0e0e1e')};"
            f" border: 1px solid {COLORS.get('warning', '#f0a030')};"
            f" border-radius: 4px; padding: 4px;"
        )
        self._key_lbl.setFocus()
        self._key_lbl.grabKeyboard()

    def keyPressEvent(self, event):
        if self._recording:
            seq = QKeySequence(event.keyCombination())
            text = seq.toString()
            if text and event.key() not in (Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta):
                self._recording = False
                self._key = text
                self._key_lbl.setText(text)
                self._key_lbl.releaseKeyboard()
                self._key_lbl.setStyleSheet(
                    f"color: {COLORS.get('accent', '#7c6aef')};"
                    f" font-family: Consolas; font-size: 11px;"
                    f" background: {COLORS.get('bg_root', '#0e0e1e')};"
                    f" border: 1px solid {COLORS.get('border', '#2a2a4a')};"
                    f" border-radius: 4px; padding: 4px;"
                )
                self.binding_changed.emit(self.action, text)
            return
        super().keyPressEvent(event)

    def _reset_to_default(self):
        default_key = DEFAULTS.get(self.action, "")
        self._key = default_key
        self._key_lbl.setText(default_key)
        self.binding_changed.emit(self.action, default_key)


class KeybindingEditor(QFrame):
    """Full keybinding editor panel with search, edit, reset."""

    bindings_changed = Signal(dict)  # all bindings

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("KeybindingEditor")
        self._bindings = load_shortcuts()
        self._rows: list[_KeyBindRow] = []
        self._build()

    def _build(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Header
        header = QFrame()
        header.setObjectName("SettingsHeader")
        header.setFixedHeight(36)
        hl = QHBoxLayout()
        hl.setContentsMargins(12, 0, 12, 0)
        hl.setSpacing(8)
        header.setLayout(hl)

        title = QLabel("⌨ Keyboard Shortcuts")
        title.setObjectName("PanelTitle")
        hl.addWidget(title)
        hl.addStretch()

        reset_all = QPushButton("Reset All")
        reset_all.setObjectName("DangerSmallButton")
        reset_all.setCursor(Qt.PointingHandCursor)
        reset_all.clicked.connect(self._reset_all)
        hl.addWidget(reset_all)

        layout.addWidget(header)

        # Search
        self._search = QLineEdit()
        self._search.setObjectName("SearchInput")
        self._search.setPlaceholderText("Search shortcuts…")
        self._search.setContentsMargins(8, 6, 8, 6)
        self._search.textChanged.connect(self._filter)
        layout.addWidget(self._search)

        # Scrollable list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        container = QWidget()
        self._list_layout = QVBoxLayout()
        self._list_layout.setContentsMargins(4, 4, 4, 4)
        self._list_layout.setSpacing(2)
        container.setLayout(self._list_layout)

        for action, key in sorted(self._bindings.items()):
            row = _KeyBindRow(action, key)
            row.binding_changed.connect(self._on_binding_changed)
            row.setStyleSheet(
                f"QFrame {{ border-bottom: 1px solid {COLORS.get('border', '#2a2a4a')}; }}"
            )
            self._rows.append(row)
            self._list_layout.addWidget(row)

        self._list_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

    def _filter(self, text: str):
        text = text.strip().lower()
        for row in self._rows:
            visible = not text or text in row.action.lower()
            row.setVisible(visible)

    def _on_binding_changed(self, action: str, new_key: str):
        self._bindings[action] = new_key
        save_shortcuts(self._bindings)
        self.bindings_changed.emit(self._bindings)

    def _reset_all(self):
        self._bindings = dict(DEFAULTS)
        save_shortcuts(self._bindings)
        # Rebuild rows
        for row in self._rows:
            row.deleteLater()
        self._rows.clear()
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for action, key in sorted(self._bindings.items()):
            row = _KeyBindRow(action, key)
            row.binding_changed.connect(self._on_binding_changed)
            row.setStyleSheet(
                f"QFrame {{ border-bottom: 1px solid {COLORS.get('border', '#2a2a4a')}; }}"
            )
            self._rows.append(row)
            self._list_layout.insertWidget(self._list_layout.count() - 1, row)

        self.bindings_changed.emit(self._bindings)
