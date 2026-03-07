import json
import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QSpinBox,
    QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS
from ..Colors.theme_registry import list_all_themes

_CONFIG_PATH = Path(__file__).resolve().parents[3] / "fluxus_settings.json"

_DEFAULTS = {
    "python_exe": "",
    "font_size": 11,
    "font_family": "Consolas",
    "tab_size": 4,
    "word_wrap": False,
    "auto_save": True,
    "auto_save_interval": 30,
    "show_line_numbers": True,
    "highlight_current_line": True,
    "theme": "Midnight",
    "console_max_lines": 5000,
    "run_in_cwd": True,
    "minimap_enabled": True,
    "bracket_matching": True,
    "autocomplete": True,
    "session_restore": True,
    "execution_method": "minescript",
}


def load_settings() -> dict:
    try:
        if _CONFIG_PATH.exists():
            data = json.loads(_CONFIG_PATH.read_text("utf-8"))
            merged = {**_DEFAULTS, **data}
            return merged
    except Exception:
        pass
    return dict(_DEFAULTS)


def save_settings(settings: dict) -> None:
    try:
        _CONFIG_PATH.write_text(json.dumps(settings, indent=2), "utf-8")
    except Exception:
        pass


class SettingsPanel(QFrame):
    """Application settings panel."""

    settings_changed = Signal(dict)
    theme_changed = Signal(str)  # emits theme name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsPanel")
        self._settings = load_settings()
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.setLayout(outer)

        # Header
        header = QFrame(self)
        header.setObjectName("SettingsHeader")
        header.setFixedHeight(40)
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(12, 0, 12, 0)
        h_layout.setSpacing(8)
        header.setLayout(h_layout)

        title = QLabel("⚙  Settings")
        title.setObjectName("PanelTitle")
        h_layout.addWidget(title)
        h_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setObjectName("AccentButton")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save)
        h_layout.addWidget(save_btn)

        reset_btn = QPushButton("Reset")
        reset_btn.setObjectName("SmallButton")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.clicked.connect(self._reset)
        h_layout.addWidget(reset_btn)

        outer.addWidget(header)

        # Search bar for filtering settings
        search_frame = QFrame(self)
        search_frame.setObjectName("FilterBar")
        sf_layout = QHBoxLayout()
        sf_layout.setContentsMargins(12, 4, 12, 4)
        search_frame.setLayout(sf_layout)

        self._search = QLineEdit()
        self._search.setObjectName("SearchInput")
        self._search.setPlaceholderText("Search settings…")
        self._search.textChanged.connect(self._filter_settings)
        sf_layout.addWidget(self._search)

        outer.addWidget(search_frame)

        # Scrollable body
        scroll = QScrollArea(self)
        scroll.setObjectName("SettingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("SettingsBody")
        body_layout = QVBoxLayout()
        body_layout.setContentsMargins(16, 12, 16, 16)
        body_layout.setSpacing(6)
        body.setLayout(body_layout)

        # Track all setting rows for filtering
        self._filterable_rows: list[tuple[str, QWidget | QHBoxLayout]] = []

        # --- Appearance section ---
        body_layout.addWidget(self._section("Appearance"))

        # Theme selector
        theme_row = QHBoxLayout()
        theme_row.setSpacing(8)
        theme_lbl = QLabel("Theme")
        theme_lbl.setObjectName("SettingsLabel")
        theme_lbl.setFixedWidth(180)
        theme_row.addWidget(theme_lbl)
        self._theme_combo = QComboBox()
        self._theme_combo.setObjectName("SettingsCombo")
        for t in list_all_themes():
            self._theme_combo.addItem(t)
        idx = self._theme_combo.findText(self._settings.get("theme", "Midnight"))
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        self._theme_combo.currentTextChanged.connect(self._on_theme_change)
        theme_row.addWidget(self._theme_combo)
        theme_row.addStretch()
        body_layout.addLayout(theme_row)

        # --- Editor section ---
        body_layout.addSpacing(10)
        body_layout.addWidget(self._section("Editor"))

        self._font_family = self._add_text_row(body_layout, "Font Family", self._settings["font_family"])
        self._font_size = self._add_spin_row(body_layout, "Font Size", self._settings["font_size"], 6, 48)
        self._tab_size = self._add_spin_row(body_layout, "Tab Size", self._settings["tab_size"], 1, 16)
        self._word_wrap = self._add_check_row(body_layout, "Word Wrap", self._settings["word_wrap"])
        self._line_numbers = self._add_check_row(body_layout, "Show Line Numbers", self._settings["show_line_numbers"])
        self._highlight_line = self._add_check_row(body_layout, "Highlight Current Line", self._settings["highlight_current_line"])
        self._minimap = self._add_check_row(body_layout, "Show Minimap", self._settings.get("minimap_enabled", True))
        self._bracket_match = self._add_check_row(body_layout, "Bracket Matching", self._settings.get("bracket_matching", True))
        self._autocomplete_chk = self._add_check_row(body_layout, "Autocomplete", self._settings.get("autocomplete", True))

        # --- Execution section ---
        body_layout.addSpacing(10)
        body_layout.addWidget(self._section("Execution"))

        self._python_exe = self._add_text_row(body_layout, "Python Executable", self._settings["python_exe"], placeholder="(auto-detect)")
        self._run_cwd = self._add_check_row(body_layout, "Run in Script Directory", self._settings["run_in_cwd"])

        # Execution method selector
        exec_row = QHBoxLayout()
        exec_row.setSpacing(8)
        exec_lbl = QLabel("Execution Method")
        exec_lbl.setObjectName("SettingsLabel")
        exec_lbl.setFixedWidth(180)
        exec_row.addWidget(exec_lbl)
        self._exec_method = QComboBox()
        self._exec_method.setObjectName("SettingsCombo")
        self._exec_method.addItem("minescript.execute()  (Minescript job)", "minescript")
        self._exec_method.addItem("Subprocess  (direct Python)", "subprocess")
        current_method = self._settings.get("execution_method", "minescript")
        idx_method = 0 if current_method == "minescript" else 1
        self._exec_method.setCurrentIndex(idx_method)
        exec_row.addWidget(self._exec_method)
        exec_row.addStretch()
        body_layout.addLayout(exec_row)

        # --- Auto-save section ---
        body_layout.addSpacing(10)
        body_layout.addWidget(self._section("Auto-Save"))

        self._auto_save = self._add_check_row(body_layout, "Enable Auto-Save", self._settings["auto_save"])
        self._auto_save_interval = self._add_spin_row(body_layout, "Interval (seconds)", self._settings["auto_save_interval"], 5, 600)

        # --- Console section ---
        body_layout.addSpacing(10)
        body_layout.addWidget(self._section("Console"))

        self._console_max = self._add_spin_row(body_layout, "Max Lines", self._settings["console_max_lines"], 100, 100000)

        # --- Session section ---
        body_layout.addSpacing(10)
        body_layout.addWidget(self._section("Session"))

        self._session_restore = self._add_check_row(body_layout, "Restore previous session on launch", self._settings.get("session_restore", True))

        body_layout.addStretch()
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

    def _section(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("SettingsSection")
        return lbl

    def _add_text_row(self, layout, label: str, value: str, placeholder: str = "") -> QLineEdit:
        row_w = QFrame()
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row_w.setLayout(row)
        lbl = QLabel(label)
        lbl.setObjectName("SettingsLabel")
        lbl.setFixedWidth(180)
        row.addWidget(lbl)
        inp = QLineEdit(value)
        inp.setObjectName("SettingsInput")
        if placeholder:
            inp.setPlaceholderText(placeholder)
        row.addWidget(inp)
        layout.addWidget(row_w)
        self._filterable_rows.append((label, row_w))
        return inp

    def _add_spin_row(self, layout, label: str, value: int, mn: int, mx: int) -> QSpinBox:
        row_w = QFrame()
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row_w.setLayout(row)
        lbl = QLabel(label)
        lbl.setObjectName("SettingsLabel")
        lbl.setFixedWidth(180)
        row.addWidget(lbl)
        spin = QSpinBox()
        spin.setObjectName("SettingsSpinBox")
        spin.setRange(mn, mx)
        spin.setValue(value)
        row.addWidget(spin)
        row.addStretch()
        layout.addWidget(row_w)
        self._filterable_rows.append((label, row_w))
        return spin

    def _add_check_row(self, layout, label: str, value: bool) -> QCheckBox:
        cb = QCheckBox(label)
        cb.setObjectName("SettingsCheck")
        cb.setChecked(value)
        layout.addWidget(cb)
        self._filterable_rows.append((label, cb))
        return cb

    def _on_theme_change(self, name: str) -> None:
        self.theme_changed.emit(name)

    def _filter_settings(self, text: str) -> None:
        """Show/hide setting rows based on search text."""
        query = text.lower().strip()
        for label_text, widget in self._filterable_rows:
            visible = not query or query in label_text.lower()
            if isinstance(widget, QWidget):
                widget.setVisible(visible)
            # QHBoxLayout items — navigate parent widgets
            elif hasattr(widget, 'count'):
                for i in range(widget.count()):
                    item = widget.itemAt(i)
                    if item and item.widget():
                        item.widget().setVisible(visible)

    def _collect(self) -> dict:
        return {
            "python_exe": self._python_exe.text().strip(),
            "font_size": self._font_size.value(),
            "font_family": self._font_family.text().strip() or "Consolas",
            "tab_size": self._tab_size.value(),
            "word_wrap": self._word_wrap.isChecked(),
            "auto_save": self._auto_save.isChecked(),
            "auto_save_interval": self._auto_save_interval.value(),
            "show_line_numbers": self._line_numbers.isChecked(),
            "highlight_current_line": self._highlight_line.isChecked(),
            "theme": self._theme_combo.currentText(),
            "console_max_lines": self._console_max.value(),
            "run_in_cwd": self._run_cwd.isChecked(),
            "minimap_enabled": self._minimap.isChecked(),
            "bracket_matching": self._bracket_match.isChecked(),
            "autocomplete": self._autocomplete_chk.isChecked(),
            "session_restore": self._session_restore.isChecked(),
            "execution_method": self._exec_method.currentData(),
        }

    def _save(self) -> None:
        self._settings = self._collect()
        save_settings(self._settings)
        self.settings_changed.emit(self._settings)

    def _reset(self) -> None:
        self._settings = dict(_DEFAULTS)
        save_settings(self._settings)
        self.settings_changed.emit(self._settings)
        # Rebuild UI (simplest way)
        for i in reversed(range(self.layout().count())):
            w = self.layout().itemAt(i).widget()
            if w:
                w.deleteLater()
        self._build()

    def get_settings(self) -> dict:
        return dict(self._settings)
