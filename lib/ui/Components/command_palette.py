"""
CommandPalette — Ctrl+Shift+P searchable popup for executing actions quickly.
Inspired by VS Code's command palette.
"""

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QDialog, QGraphicsOpacityEffect, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QVBoxLayout,
)

from ..Colors.palette import COLORS


class CommandPalette(QDialog):
    """Modal popup with fuzzy-filtered command list."""

    action_selected = Signal(str)  # action key

    def __init__(self, actions: dict[str, str], parent=None):
        """
        *actions* maps action_key → display label, e.g.
        ``{"save_file": "Save File  (Ctrl+S)", ...}``
        """
        super().__init__(parent)
        self.setObjectName("CommandPalette")
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFixedSize(480, 360)
        self._actions = actions
        self._build()
        self._populate("")

    def showEvent(self, event):
        super().showEvent(event)
        # Fade-in on open
        eff = QGraphicsOpacityEffect(self)
        eff.setOpacity(0.0)
        self.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity")
        anim.setDuration(180)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._show_anim = anim

    def _build(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.setStyleSheet(
            f"QDialog#CommandPalette {{ background-color: {COLORS['bg_dialog']}; "
            f"border: 1px solid {COLORS['accent']}; border-radius: 10px; }}"
        )

        # Search input
        self._input = QLineEdit()
        self._input.setObjectName("PaletteInput")
        self._input.setPlaceholderText("Type a command…")
        self._input.setStyleSheet(
            f"background-color: {COLORS['bg_input']}; color: {COLORS['text_primary']}; "
            f"border: none; border-bottom: 1px solid {COLORS['border']}; "
            f"font-family: 'Segoe UI'; font-size: 14px; padding: 12px 16px;"
        )
        self._input.textChanged.connect(self._populate)
        self._input.returnPressed.connect(self._accept_current)
        layout.addWidget(self._input)

        # Results list
        self._list = QListWidget()
        self._list.setObjectName("PaletteList")
        self._list.setStyleSheet(
            f"QListWidget {{ background-color: {COLORS['bg_dialog']}; color: {COLORS['text_primary']}; "
            f"border: none; font-family: 'Segoe UI'; font-size: 13px; outline: none; }} "
            f"QListWidget::item {{ padding: 8px 16px; }} "
            f"QListWidget::item:hover {{ background-color: {COLORS['bg_hover']}; }} "
            f"QListWidget::item:selected {{ background-color: {COLORS['bg_selected']}; color: {COLORS['accent']}; }}"
        )
        self._list.itemActivated.connect(self._on_activate)
        layout.addWidget(self._list, 1)

    def _populate(self, query: str) -> None:
        self._list.clear()
        q = query.lower().strip()
        for key, label in self._actions.items():
            if not q or q in label.lower() or q in key.lower():
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, key)
                self._list.addItem(item)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _accept_current(self) -> None:
        item = self._list.currentItem()
        if item:
            self._on_activate(item)

    def _on_activate(self, item: QListWidgetItem) -> None:
        key = item.data(Qt.UserRole)
        if key:
            self.action_selected.emit(key)
        self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key_Down, Qt.Key_Up):
            self._list.keyPressEvent(event)
        else:
            super().keyPressEvent(event)
