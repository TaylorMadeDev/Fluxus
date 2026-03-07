"""
Script Parameters — Unity-like inspector for script variables.

Parses @param / @header comments from scripts and provides a dialog
to edit values at runtime.  Saved values live in the manifest and can
be injected into a temp copy of the script before execution.

Annotation format (place at the top of your script):

    # @header Display Settings
    # @param string message "Hello World" -- Message to display
    # @param int count 5 -- Number of iterations
    # @param float speed 1.5 -- Movement speed
    # @param bool verbose false -- Verbose output
    # @param dropdown mode ["fast","slow","normal"] -- Speed mode
"""

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
    QSpinBox, QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS


# ── Data ───────────────────────────────────────────────────────────

@dataclass
class ParamDef:
    """A single parameter definition parsed from source."""
    kind: str          # "header", "string", "int", "float", "bool", "dropdown"
    name: str          # variable name (or header text for headers)
    default: Any       # default value
    description: str   # tooltip / inline description
    options: list = field(default_factory=list)  # dropdown choices


# ── Pattern matching ───────────────────────────────────────────────

_HEADER_RE = re.compile(r'#\s*@header\s+"?([^"]+)"?\s*$')
_PARAM_RE = re.compile(
    r'#\s*@param\s+(\w+)\s+(\w+)\s+(.*?)(?:\s*--\s*(.*))?$'
)


def parse_params(code: str) -> list[ParamDef]:
    """Parse ``# @param`` and ``# @header`` annotations from source."""
    params: list[ParamDef] = []

    for line in code.splitlines():
        stripped = line.strip()

        # ── Header ─────────────────────────────────────────────
        m = _HEADER_RE.match(stripped)
        if m:
            params.append(ParamDef("header", m.group(1).strip(), None, ""))
            continue

        # ── Parameter ──────────────────────────────────────────
        m = _PARAM_RE.match(stripped)
        if not m:
            continue

        kind = m.group(1).lower()
        name = m.group(2)
        raw_default = m.group(3).strip()
        desc = (m.group(4) or "").strip()

        if kind == "string":
            default = raw_default.strip('"').strip("'")
        elif kind == "int":
            try:
                default = int(raw_default)
            except ValueError:
                default = 0
        elif kind == "float":
            try:
                default = float(raw_default)
            except ValueError:
                default = 0.0
        elif kind == "bool":
            default = raw_default.lower() in ("true", "1", "yes")
        elif kind == "dropdown":
            try:
                options = json.loads(raw_default)
                if not isinstance(options, list):
                    options = [str(options)]
            except Exception:
                options = [o.strip().strip('"').strip("'") for o in raw_default.split(",")]
            default = options[0] if options else ""
            params.append(ParamDef(kind, name, default, desc, options))
            continue
        else:
            kind = "string"
            default = raw_default

        params.append(ParamDef(kind, name, default, desc))

    return params


def build_injection_block(values: dict[str, Any]) -> str:
    """Build a block of Python variable assignments from *values*."""
    if not values:
        return ""
    lines = ["# ── Fluxus Parameters ──────────────────────────────"]
    for name, val in values.items():
        if isinstance(val, bool):
            lines.append(f"{name} = {val}")
        elif isinstance(val, str):
            escaped = val.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{name} = "{escaped}"')
        elif isinstance(val, (int, float)):
            lines.append(f"{name} = {val}")
        else:
            lines.append(f"{name} = {repr(val)}")
    lines.append("# ── End Parameters ────────────────────────────────\n")
    return "\n".join(lines) + "\n"


def create_injected_script(script_path: str, values: dict[str, Any]) -> str:
    """Write a temp copy of *script_path* with *values* prepended.

    Returns the path to the temporary file.  Caller is responsible for
    cleaning it up after execution.
    """
    code = Path(script_path).read_text(encoding="utf-8")
    injection = build_injection_block(values)
    combined = injection + code

    tmp_dir = Path(script_path).parent
    suffix = Path(script_path).suffix  # Preserve .py or .pyj
    fd, tmp_path = tempfile.mkstemp(suffix=suffix, dir=str(tmp_dir), prefix="_fluxus_params_")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(combined)
    return tmp_path


# ── Dialog ─────────────────────────────────────────────────────────

class ScriptParametersDialog(QDialog):
    """Unity-like inspector dialog for editing script parameters."""

    params_saved = Signal(dict)        # {name: value}
    run_with_params = Signal(str)      # temp script path to run

    def __init__(self, script_path: str, saved_values: dict | None = None, parent=None):
        super().__init__(parent)
        self._path = script_path
        self._saved: dict = saved_values or {}
        self._widgets: dict[str, QWidget] = {}
        self._params: list[ParamDef] = []

        self.setWindowTitle("Script Parameters")
        self.setMinimumSize(460, 420)
        self.setStyleSheet(
            f"QDialog {{ background: {COLORS['bg_root']}; }}"
            f"QLabel {{ color: {COLORS['text_primary']}; font-family: 'Segoe UI'; }}"
        )
        self._build()

    # ── UI build ───────────────────────────────────────────────────
    def _build(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        self.setLayout(layout)

        # Title
        title = QLabel(f"⚙  Parameters — {Path(self._path).stem}")
        title.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {COLORS['accent']};"
        )
        layout.addWidget(title)

        # Parse params from source
        try:
            code = Path(self._path).read_text(encoding="utf-8")
            self._params = parse_params(code)
        except Exception:
            self._params = []

        if not self._params:
            self._show_empty_state(layout)
            return

        # Scrollable form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        form = QVBoxLayout()
        form.setContentsMargins(0, 6, 0, 6)
        form.setSpacing(6)
        container.setLayout(form)

        for param in self._params:
            if param.kind == "header":
                hdr = QLabel(param.name)
                hdr.setStyleSheet(
                    f"color: {COLORS['accent']}; font-size: 13px; font-weight: 700;"
                    f" padding: 10px 0 4px 0;"
                    f" border-bottom: 1px solid {COLORS['border']};"
                )
                form.addWidget(hdr)
                continue

            form.addWidget(self._make_param_row(param))

        form.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        reset_btn = QPushButton("Reset Defaults")
        reset_btn.setObjectName("SmallButton")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_defaults)
        btn_row.addWidget(reset_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("SmallButton")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("AccentButton")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        run_btn = QPushButton("▶ Save & Run")
        run_btn.setObjectName("AccentButton")
        run_btn.setCursor(Qt.PointingHandCursor)
        run_btn.clicked.connect(self._save_and_run)
        btn_row.addWidget(run_btn)

        layout.addLayout(btn_row)

    def _show_empty_state(self, layout: QVBoxLayout) -> None:
        hint = QLabel(
            "No @param annotations found in this script.\n\n"
            "Add parameter annotations like:\n\n"
            '  # @header Settings\n'
            '  # @param string message "Hello" -- Message to display\n'
            '  # @param int count 5 -- Number of times\n'
            '  # @param float speed 1.5 -- Movement speed\n'
            '  # @param bool verbose false -- Verbose output\n'
            '  # @param dropdown mode ["fast","slow"] -- Speed'
        )
        hint.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; padding: 20px;"
            f" background: {COLORS['bg_surface']}; border-radius: 8px;"
            f" font-family: 'Consolas';"
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setObjectName("SmallButton")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn, 0, Qt.AlignRight)

    # ── Row builder ────────────────────────────────────────────────
    def _make_param_row(self, param: ParamDef) -> QFrame:
        row = QFrame()
        row.setStyleSheet(
            f"QFrame {{ background: {COLORS['bg_surface']};"
            f" border: 1px solid {COLORS['border']}; border-radius: 6px; }}"
        )
        rl = QHBoxLayout()
        rl.setContentsMargins(10, 8, 10, 8)
        rl.setSpacing(8)
        row.setLayout(rl)

        # Label
        label = QLabel(param.name)
        label.setFixedWidth(130)
        label.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-weight: 600;"
            f" font-size: 12px; border: none;"
        )
        if param.description:
            label.setToolTip(param.description)
        rl.addWidget(label)

        value = self._saved.get(param.name, param.default)

        _INPUT_STYLE = (
            f"background: {COLORS['bg_root']}; color: {COLORS['text_primary']};"
            f" border: 1px solid {COLORS['border']}; border-radius: 4px;"
            f" padding: 4px 6px; font-family: Consolas; font-size: 12px;"
        )

        if param.kind == "string":
            w = QLineEdit(str(value or ""))
            w.setStyleSheet(_INPUT_STYLE)
            self._widgets[param.name] = w
            rl.addWidget(w, 1)

        elif param.kind == "int":
            w = QSpinBox()
            w.setRange(-999999, 999999)
            w.setValue(int(value) if value is not None else 0)
            w.setStyleSheet(_INPUT_STYLE)
            self._widgets[param.name] = w
            rl.addWidget(w, 1)

        elif param.kind == "float":
            w = QDoubleSpinBox()
            w.setRange(-999999.0, 999999.0)
            w.setDecimals(3)
            w.setValue(float(value) if value is not None else 0.0)
            w.setStyleSheet(_INPUT_STYLE)
            self._widgets[param.name] = w
            rl.addWidget(w, 1)

        elif param.kind == "bool":
            w = QCheckBox()
            w.setChecked(bool(value))
            w.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
            self._widgets[param.name] = w
            rl.addWidget(w, 1)

        elif param.kind == "dropdown":
            w = QComboBox()
            w.addItems(param.options)
            if str(value) in param.options:
                w.setCurrentText(str(value))
            w.setStyleSheet(_INPUT_STYLE)
            self._widgets[param.name] = w
            rl.addWidget(w, 1)

        # Description
        if param.description:
            d = QLabel(param.description)
            d.setStyleSheet(
                f"color: {COLORS['text_dim']}; font-size: 10px; border: none;"
            )
            d.setMaximumWidth(140)
            d.setWordWrap(True)
            rl.addWidget(d)

        return row

    # ── Value helpers ──────────────────────────────────────────────
    def _get_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for param in self._params:
            if param.kind == "header":
                continue
            w = self._widgets.get(param.name)
            if w is None:
                continue
            if param.kind == "string":
                values[param.name] = w.text()
            elif param.kind == "int":
                values[param.name] = w.value()
            elif param.kind == "float":
                values[param.name] = w.value()
            elif param.kind == "bool":
                values[param.name] = w.isChecked()
            elif param.kind == "dropdown":
                values[param.name] = w.currentText()
        return values

    def _reset_defaults(self) -> None:
        for param in self._params:
            if param.kind == "header":
                continue
            w = self._widgets.get(param.name)
            if w is None:
                continue
            if param.kind == "string":
                w.setText(str(param.default or ""))
            elif param.kind == "int":
                w.setValue(int(param.default or 0))
            elif param.kind == "float":
                w.setValue(float(param.default or 0.0))
            elif param.kind == "bool":
                w.setChecked(bool(param.default))
            elif param.kind == "dropdown":
                if str(param.default) in param.options:
                    w.setCurrentText(str(param.default))

    def _save(self) -> None:
        values = self._get_values()
        self.params_saved.emit(values)
        self.accept()

    def _save_and_run(self) -> None:
        values = self._get_values()
        self.params_saved.emit(values)
        if values:
            tmp = create_injected_script(self._path, values)
            self.run_with_params.emit(tmp)
        else:
            self.run_with_params.emit(self._path)
        self.accept()
