"""
FindReplaceBar — inline search/replace bar for the code editor.
Supports plain text and regex modes.
"""

import re

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QPlainTextEdit, QVBoxLayout,
)

from ..Colors.palette import COLORS


class FindReplaceBar(QFrame):
    """Compact search-and-replace bar for embedding above the editor."""

    close_requested = Signal()

    def __init__(self, editor: QPlainTextEdit | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("FindReplaceBar")
        self._editor = editor
        self._matches: list[tuple[int, int]] = []
        self._current_idx = -1
        self._build()
        self.setMaximumHeight(0)
        self.hide()

        # Opacity effect for fade
        self._opacity_eff = QGraphicsOpacityEffect(self)
        self._opacity_eff.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_eff)

    def show(self):
        """Animate reveal: expand height + fade in."""
        super().show()
        # Animate maximum height from 0 → actual height
        self.setMaximumHeight(0)
        anim = QPropertyAnimation(self, b"maximumHeight")
        anim.setDuration(200)
        anim.setStartValue(0)
        anim.setEndValue(120)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._show_anim = anim

        self._opacity_eff.setOpacity(0.0)
        fade = QPropertyAnimation(self._opacity_eff, b"opacity")
        fade.setDuration(200)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.OutCubic)
        fade.start()
        self._show_fade = fade

    def hide(self):
        """Animate collapse: shrink height + fade out, then really hide."""
        if self.maximumHeight() == 0:
            super().hide()
            return
        anim = QPropertyAnimation(self, b"maximumHeight")
        anim.setDuration(150)
        anim.setStartValue(self.maximumHeight())
        anim.setEndValue(0)
        anim.setEasingCurve(QEasingCurve.InCubic)
        anim.finished.connect(lambda: super(FindReplaceBar, self).hide())
        anim.start()
        self._hide_anim = anim

        fade = QPropertyAnimation(self._opacity_eff, b"opacity")
        fade.setDuration(150)
        fade.setStartValue(self._opacity_eff.opacity())
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.InCubic)
        fade.start()
        self._hide_fade = fade

    def set_editor(self, editor: QPlainTextEdit) -> None:
        """Attach a (possibly different) editor widget."""
        self._editor = editor

    def _build(self) -> None:
        outer = QVBoxLayout()
        outer.setContentsMargins(8, 4, 8, 4)
        outer.setSpacing(4)
        self.setLayout(outer)

        # Find row
        find_row = QHBoxLayout()
        find_row.setSpacing(6)

        self._find_input = QLineEdit()
        self._find_input.setObjectName("SearchInput")
        self._find_input.setPlaceholderText("Find…")
        self._find_input.textChanged.connect(self._do_search)
        self._find_input.returnPressed.connect(self.find_next)
        find_row.addWidget(self._find_input, 1)

        self._regex_cb = QCheckBox("Regex")
        self._regex_cb.setObjectName("SettingsCheck")
        self._regex_cb.toggled.connect(self._do_search)
        find_row.addWidget(self._regex_cb)

        self._case_cb = QCheckBox("Aa")
        self._case_cb.setObjectName("SettingsCheck")
        self._case_cb.setToolTip("Case sensitive")
        self._case_cb.toggled.connect(self._do_search)
        find_row.addWidget(self._case_cb)

        self._count_label = QLabel("0/0")
        self._count_label.setObjectName("EditorStatusText")
        self._count_label.setFixedWidth(50)
        self._count_label.setAlignment(Qt.AlignCenter)
        find_row.addWidget(self._count_label)

        prev_btn = QPushButton("◀")
        prev_btn.setObjectName("SmallButton")
        prev_btn.setFixedWidth(28)
        prev_btn.setCursor(Qt.PointingHandCursor)
        prev_btn.clicked.connect(self.find_prev)
        find_row.addWidget(prev_btn)

        next_btn = QPushButton("▶")
        next_btn.setObjectName("SmallButton")
        next_btn.setFixedWidth(28)
        next_btn.setCursor(Qt.PointingHandCursor)
        next_btn.clicked.connect(self.find_next)
        find_row.addWidget(next_btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("SmallButton")
        close_btn.setFixedWidth(28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self._close)
        find_row.addWidget(close_btn)

        outer.addLayout(find_row)

        # Replace row
        replace_row = QHBoxLayout()
        replace_row.setSpacing(6)

        self._replace_input = QLineEdit()
        self._replace_input.setObjectName("SearchInput")
        self._replace_input.setPlaceholderText("Replace…")
        replace_row.addWidget(self._replace_input, 1)

        repl_btn = QPushButton("Replace")
        repl_btn.setObjectName("SmallButton")
        repl_btn.setCursor(Qt.PointingHandCursor)
        repl_btn.clicked.connect(self.replace_current)
        replace_row.addWidget(repl_btn)

        repl_all_btn = QPushButton("All")
        repl_all_btn.setObjectName("SmallButton")
        repl_all_btn.setCursor(Qt.PointingHandCursor)
        repl_all_btn.clicked.connect(self.replace_all)
        replace_row.addWidget(repl_all_btn)

        outer.addLayout(replace_row)

    # ── Public API ─────────────────────────────────────────────────
    def open_find(self) -> None:
        self.show()
        self._find_input.setFocus()
        if self._editor:
            sel = self._editor.textCursor().selectedText()
            if sel:
                self._find_input.setText(sel)
        self._do_search()

    def open_replace(self) -> None:
        self.open_find()
        self._replace_input.setFocus()

    def find_next(self) -> None:
        if not self._matches or not self._editor:
            return
        self._current_idx = (self._current_idx + 1) % len(self._matches)
        self._highlight_current()

    def find_prev(self) -> None:
        if not self._matches or not self._editor:
            return
        self._current_idx = (self._current_idx - 1) % len(self._matches)
        self._highlight_current()

    def replace_current(self) -> None:
        if not self._matches or self._current_idx < 0 or not self._editor:
            return
        start, length = self._matches[self._current_idx]
        cursor = self._editor.textCursor()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, length)
        cursor.insertText(self._replace_input.text())
        self._editor.setTextCursor(cursor)
        self._do_search()

    def replace_all(self) -> None:
        if not self._editor:
            return
        text = self._editor.toPlainText()
        query = self._find_input.text()
        replacement = self._replace_input.text()
        if not query:
            return
        if self._regex_cb.isChecked():
            flags = 0 if self._case_cb.isChecked() else re.IGNORECASE
            new_text = re.sub(query, replacement, text, flags=flags)
        else:
            if self._case_cb.isChecked():
                new_text = text.replace(query, replacement)
            else:
                # case-insensitive replace
                compiled = re.compile(re.escape(query), re.IGNORECASE)
                new_text = compiled.sub(replacement, text)
        self._editor.setPlainText(new_text)
        self._do_search()

    # ── Internal ───────────────────────────────────────────────────
    def _do_search(self) -> None:
        self._matches.clear()
        self._current_idx = -1
        query = self._find_input.text()
        if not query or not self._editor:
            self._count_label.setText("0/0")
            self._clear_highlights()
            return

        text = self._editor.toPlainText()
        try:
            if self._regex_cb.isChecked():
                flags = 0 if self._case_cb.isChecked() else re.IGNORECASE
                for m in re.finditer(query, text, flags):
                    self._matches.append((m.start(), m.end() - m.start()))
            else:
                flags = 0 if self._case_cb.isChecked() else re.IGNORECASE
                for m in re.finditer(re.escape(query), text, flags):
                    self._matches.append((m.start(), m.end() - m.start()))
        except re.error:
            pass

        total = len(self._matches)
        self._count_label.setText(f"0/{total}" if total else "0/0")
        if total:
            self._current_idx = 0
            self._highlight_current()

    def _highlight_current(self) -> None:
        if self._current_idx < 0 or self._current_idx >= len(self._matches):
            return
        if not self._editor:
            return
        start, length = self._matches[self._current_idx]
        cursor = self._editor.textCursor()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, length)
        self._editor.setTextCursor(cursor)
        self._editor.centerCursor()
        self._count_label.setText(f"{self._current_idx + 1}/{len(self._matches)}")

    def _clear_highlights(self) -> None:
        if not self._editor:
            return
        cursor = self._editor.textCursor()
        cursor.clearSelection()
        self._editor.setTextCursor(cursor)

    def _close(self) -> None:
        self._clear_highlights()
        self.hide()
        self.close_requested.emit()
        if self._editor:
            self._editor.setFocus()
