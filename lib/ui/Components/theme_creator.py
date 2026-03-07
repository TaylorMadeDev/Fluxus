"""
ThemeCreator — A panel that lets users create, edit, preview, and export
colour themes.  Embeds a live colour-swatch grid and preview strip.
"""

import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog, QComboBox, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS, apply_theme
from ..Colors.theme_registry import (
    BUILTIN_THEMES, list_all_themes, get_theme,
    save_custom_theme, delete_custom_theme,
)


class ColorSwatch(QPushButton):
    """A small clickable colour square."""

    color_changed = Signal(str, str)  # key, new_hex

    def __init__(self, key: str, hex_color: str, parent=None):
        super().__init__(parent)
        self.key = key
        self._hex = hex_color
        self.setFixedSize(32, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(f"{key}: {hex_color}")
        self._apply_style()
        self.clicked.connect(self._pick)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"background-color: {self._hex}; border: 2px solid #555; border-radius: 4px;"
        )

    def _pick(self) -> None:
        c = QColorDialog.getColor(QColor(self._hex), self, f"Pick colour for {self.key}")
        if c.isValid():
            self._hex = c.name()
            self._apply_style()
            self.setToolTip(f"{self.key}: {self._hex}")
            self.color_changed.emit(self.key, self._hex)

    def set_hex(self, hex_color: str) -> None:
        self._hex = hex_color
        self._apply_style()
        self.setToolTip(f"{self.key}: {self._hex}")


class ThemeCreator(QFrame):
    """Full-page panel for creating / editing colour themes."""

    theme_applied = Signal(str)  # theme name

    # Color groups for organized display
    _GROUPS = {
        "Backgrounds": [
            "bg_root", "bg_surface", "bg_topbar", "bg_sidebar", "bg_panel",
            "bg_editor", "bg_input", "bg_console", "bg_hover", "bg_pressed",
            "bg_selected", "bg_tab_active", "bg_tab_inactive", "bg_badge",
            "bg_card", "bg_card_hover", "bg_dialog",
        ],
        "Borders": ["border", "border_light", "border_focus", "border_card"],
        "Text": ["text_primary", "text_secondary", "text_muted", "text_dim"],
        "Accents": [
            "accent", "accent_hover", "accent_dim", "success", "success_dim",
            "warning", "warning_dim", "danger", "danger_hover", "info",
        ],
        "Syntax": [
            "syn_keyword", "syn_string", "syn_number", "syn_comment",
            "syn_function", "syn_class", "syn_builtin", "syn_decorator",
            "syn_operator", "syn_self",
        ],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ThemeCreator")
        self._swatches: dict[str, ColorSwatch] = {}
        self._working: dict[str, str] = dict(COLORS)
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.setLayout(outer)

        # Header
        header = QFrame()
        header.setObjectName("BrowserHeader")
        header.setFixedHeight(44)
        h = QHBoxLayout()
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(8)
        header.setLayout(h)

        h.addWidget(self._lbl("🎨  Theme Creator", "PanelTitle"))
        h.addStretch()

        h.addWidget(self._lbl("Base:", "FieldLabel"))
        self._theme_combo = QComboBox()
        self._theme_combo.setObjectName("SortCombo")
        for name in list_all_themes():
            self._theme_combo.addItem(name)
        self._theme_combo.currentTextChanged.connect(self._load_base)
        h.addWidget(self._theme_combo)

        apply_btn = QPushButton("✓ Apply")
        apply_btn.setObjectName("AccentButton")
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.clicked.connect(self._apply_live)
        h.addWidget(apply_btn)

        outer.addWidget(header)

        # Scrollable body
        scroll = QScrollArea()
        scroll.setObjectName("SettingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll, 1)

        body = QWidget()
        body.setObjectName("SettingsBody")
        self._body_layout = QVBoxLayout()
        self._body_layout.setContentsMargins(18, 14, 18, 18)
        self._body_layout.setSpacing(14)
        body.setLayout(self._body_layout)
        scroll.setWidget(body)

        # Colour groups
        for group_name, keys in self._GROUPS.items():
            grp_label = QLabel(group_name.upper())
            grp_label.setObjectName("SectionLabel")
            self._body_layout.addWidget(grp_label)

            grid = QGridLayout()
            grid.setSpacing(6)
            col = 0
            row = 0
            for key in keys:
                hex_val = self._working.get(key, "#ff00ff")
                swatch = ColorSwatch(key, hex_val)
                swatch.color_changed.connect(self._on_swatch_change)
                self._swatches[key] = swatch

                cell = QHBoxLayout()
                cell.setSpacing(4)
                cell.addWidget(swatch)
                lbl = QLabel(key.replace("_", " ").title())
                lbl.setObjectName("FieldLabel")
                lbl.setFixedWidth(120)
                cell.addWidget(lbl)
                grid.addLayout(cell, row, col)
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
            self._body_layout.addLayout(grid)

        # Preview strip
        self._body_layout.addSpacing(8)
        self._preview_label = QLabel("Preview: The quick brown fox jumps over the lazy dog. def hello(): pass # comment")
        self._preview_label.setObjectName("ThemePreview")
        self._preview_label.setWordWrap(True)
        self._preview_label.setMinimumHeight(40)
        self._update_preview()
        self._body_layout.addWidget(self._preview_label)

        # Save row
        save_row = QHBoxLayout()
        save_row.setSpacing(8)

        save_row.addWidget(self._lbl("Theme name:", "FieldLabel"))
        self._name_input = QLineEdit()
        self._name_input.setObjectName("SettingsInput")
        self._name_input.setPlaceholderText("My Custom Theme")
        save_row.addWidget(self._name_input)

        save_btn = QPushButton("💾 Save Theme")
        save_btn.setObjectName("AccentButton")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save_theme)
        save_row.addWidget(save_btn)

        del_btn = QPushButton("🗑 Delete")
        del_btn.setObjectName("DangerSmallButton")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(self._delete_theme)
        save_row.addWidget(del_btn)

        self._body_layout.addLayout(save_row)
        self._body_layout.addStretch()

    # ── Helpers ────────────────────────────────────────────────────
    def _lbl(self, text: str, obj_name: str) -> QLabel:
        l = QLabel(text)
        l.setObjectName(obj_name)
        return l

    def _on_swatch_change(self, key: str, hex_val: str) -> None:
        self._working[key] = hex_val
        self._update_preview()

    def _update_preview(self) -> None:
        bg = self._working.get("bg_editor", "#0e1117")
        fg = self._working.get("text_primary", "#e8edf3")
        acc = self._working.get("accent", "#4da3ff")
        self._preview_label.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border: 2px solid {acc}; "
            f"border-radius: 6px; padding: 10px; font-family: Consolas; font-size: 12px;"
        )

    def _load_base(self, name: str) -> None:
        theme = get_theme(name)
        self._working = dict(theme)
        for key, swatch in self._swatches.items():
            swatch.set_hex(self._working.get(key, "#ff00ff"))
        self._update_preview()

    def _apply_live(self) -> None:
        """Apply the current working colours to the running app."""
        COLORS.clear()
        COLORS.update(self._working)
        # Re-apply stylesheet
        from ..Styling.stylesheet import get_app_stylesheet
        top = self.window()
        if top:
            top.setStyleSheet(get_app_stylesheet())
        current = self._theme_combo.currentText()
        self.theme_applied.emit(current)

    def _save_theme(self) -> None:
        name = self._name_input.text().strip()
        if not name:
            name = self._theme_combo.currentText()
        save_custom_theme(name, dict(self._working))
        # Refresh combo
        self._theme_combo.blockSignals(True)
        self._theme_combo.clear()
        for n in list_all_themes():
            self._theme_combo.addItem(n)
        idx = self._theme_combo.findText(name)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        self._theme_combo.blockSignals(False)

    def _delete_theme(self) -> None:
        name = self._theme_combo.currentText()
        if delete_custom_theme(name):
            self._theme_combo.blockSignals(True)
            self._theme_combo.clear()
            for n in list_all_themes():
                self._theme_combo.addItem(n)
            self._theme_combo.blockSignals(False)
