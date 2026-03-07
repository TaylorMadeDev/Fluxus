"""
Script GUI Builder — annotation-driven custom UI panels for scripts.

Scripts use ``# @ui.*`` comments to define their own trainer/menu panels
that appear on the right side of the editor.  When the script runs, the
current widget values are injected as Python variables.

Supported annotations
─────────────────────
    # @ui.title "My Trainer"
    # @ui.page "Movement"
    # @ui.toggle   var_name "Label" default       -- description
    # @ui.slider   var_name "Label" min max val step -- description
    # @ui.button   func_name "Label"              -- description
    # @ui.dropdown var_name "Label" a,b,c          -- description
    # @ui.number   var_name "Label" min max val step -- description
    # @ui.text     var_name "Label" "default"      -- description
    # @ui.color    var_name "Label" #rrggbb        -- description
    # @ui.label    "Some informational text"
    # @ui.separator
"""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QDoubleSpinBox, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
    QSlider, QSpinBox, QStackedWidget, QTabBar, QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS


# ════════════════════════════════════════════════════════════════════
#  Data model
# ════════════════════════════════════════════════════════════════════

@dataclass
class GUIDef:
    """One parsed UI element."""
    kind: str           # title | page | toggle | slider | button | dropdown |
                        # number | text | color | label | separator
    name: str           # variable/function name  (empty for label/separator/page/title)
    label: str          # display label
    default: Any        # default value
    description: str    # tooltip text
    options: list = field(default_factory=list)   # dropdown choices
    min_val: float = 0
    max_val: float = 100
    step: float = 1


# ════════════════════════════════════════════════════════════════════
#  Regex patterns
# ════════════════════════════════════════════════════════════════════

_TITLE_RE   = re.compile(r'#\s*@ui\.title\s+"([^"]+)"')
_PAGE_RE    = re.compile(r'#\s*@ui\.page\s+"([^"]+)"')
_SEP_RE     = re.compile(r'#\s*@ui\.separator\b')
_LABEL_RE   = re.compile(r'#\s*@ui\.label\s+"([^"]+)"')

# Widgets with  var  "Label"  <defaults>  -- desc
_TOGGLE_RE   = re.compile(
    r'#\s*@ui\.toggle\s+(\w+)\s+"([^"]+)"\s+(true|false|0|1)'
    r'(?:\s*--\s*(.*))?$', re.IGNORECASE
)
_SLIDER_RE   = re.compile(
    r'#\s*@ui\.slider\s+(\w+)\s+"([^"]+)"\s+'
    r'([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)(?:\s+([\d.\-]+))?'
    r'(?:\s*--\s*(.*))?$', re.IGNORECASE
)
_BUTTON_RE   = re.compile(
    r'#\s*@ui\.button\s+(\w+)\s+"([^"]+)"'
    r'(?:\s*--\s*(.*))?$', re.IGNORECASE
)
_DROPDOWN_RE = re.compile(
    r'#\s*@ui\.dropdown\s+(\w+)\s+"([^"]+)"\s+([^\-]+?)'
    r'(?:\s*--\s*(.*))?$', re.IGNORECASE
)
_NUMBER_RE   = re.compile(
    r'#\s*@ui\.number\s+(\w+)\s+"([^"]+)"\s+'
    r'([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)(?:\s+([\d.\-]+))?'
    r'(?:\s*--\s*(.*))?$', re.IGNORECASE
)
_TEXT_RE     = re.compile(
    r'#\s*@ui\.text\s+(\w+)\s+"([^"]+)"\s+"([^"]*)"'
    r'(?:\s*--\s*(.*))?$', re.IGNORECASE
)
_COLOR_RE    = re.compile(
    r'#\s*@ui\.color\s+(\w+)\s+"([^"]+)"\s+(#[0-9a-fA-F]{6})'
    r'(?:\s*--\s*(.*))?$', re.IGNORECASE
)


# ════════════════════════════════════════════════════════════════════
#  Parser
# ════════════════════════════════════════════════════════════════════

def parse_gui(code: str) -> list[GUIDef]:
    """Parse ``# @ui.*`` annotations from source code."""
    defs: list[GUIDef] = []

    for line in code.splitlines():
        s = line.strip()

        # title
        m = _TITLE_RE.match(s)
        if m:
            defs.append(GUIDef("title", "", m.group(1), None, ""))
            continue

        # page
        m = _PAGE_RE.match(s)
        if m:
            defs.append(GUIDef("page", "", m.group(1), None, ""))
            continue

        # separator
        if _SEP_RE.match(s):
            defs.append(GUIDef("separator", "", "", None, ""))
            continue

        # label
        m = _LABEL_RE.match(s)
        if m:
            defs.append(GUIDef("label", "", m.group(1), None, ""))
            continue

        # toggle
        m = _TOGGLE_RE.match(s)
        if m:
            val = m.group(3).lower() in ("true", "1")
            defs.append(GUIDef("toggle", m.group(1), m.group(2), val,
                                (m.group(4) or "").strip()))
            continue

        # slider
        m = _SLIDER_RE.match(s)
        if m:
            mn, mx, v = float(m.group(3)), float(m.group(4)), float(m.group(5))
            st = float(m.group(6)) if m.group(6) else 1.0
            defs.append(GUIDef("slider", m.group(1), m.group(2), v,
                                (m.group(7) or "").strip(),
                                min_val=mn, max_val=mx, step=st))
            continue

        # button
        m = _BUTTON_RE.match(s)
        if m:
            defs.append(GUIDef("button", m.group(1), m.group(2), None,
                                (m.group(3) or "").strip()))
            continue

        # dropdown
        m = _DROPDOWN_RE.match(s)
        if m:
            opts = [o.strip().strip('"').strip("'") for o in m.group(3).split(",")]
            defs.append(GUIDef("dropdown", m.group(1), m.group(2),
                                opts[0] if opts else "",
                                (m.group(4) or "").strip(), options=opts))
            continue

        # number
        m = _NUMBER_RE.match(s)
        if m:
            mn, mx, v = float(m.group(3)), float(m.group(4)), float(m.group(5))
            st = float(m.group(6)) if m.group(6) else 1.0
            defs.append(GUIDef("number", m.group(1), m.group(2), v,
                                (m.group(7) or "").strip(),
                                min_val=mn, max_val=mx, step=st))
            continue

        # text
        m = _TEXT_RE.match(s)
        if m:
            defs.append(GUIDef("text", m.group(1), m.group(2), m.group(3),
                                (m.group(4) or "").strip()))
            continue

        # color
        m = _COLOR_RE.match(s)
        if m:
            defs.append(GUIDef("color", m.group(1), m.group(2), m.group(3),
                                (m.group(4) or "").strip()))
            continue

    return defs


def has_gui(code: str) -> bool:
    """Quick check — does the source contain any ``# @ui.`` annotations?"""
    return bool(re.search(r'#\s*@ui\.', code))


# ════════════════════════════════════════════════════════════════════
#  Injection helpers  (mirrors script_params but for GUI values)
# ════════════════════════════════════════════════════════════════════

def build_gui_injection(values: dict[str, Any]) -> str:
    """Build a block of Python variable assignments from the GUI values."""
    if not values:
        return ""
    lines = ["# ── Fluxus GUI Values ─────────────────────────────────"]
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
    lines.append("# ── End GUI Values ────────────────────────────────────\n")
    return "\n".join(lines) + "\n"


def create_gui_script(script_path: str, values: dict[str, Any]) -> str:
    """Write a temp copy of *script_path* with GUI values prepended."""
    code = Path(script_path).read_text(encoding="utf-8")
    injection = build_gui_injection(values)
    combined = injection + code

    tmp_dir = Path(script_path).parent
    suffix = Path(script_path).suffix  # Preserve .py or .pyj
    fd, tmp_path = tempfile.mkstemp(suffix=suffix, dir=str(tmp_dir),
                                     prefix="_fluxus_gui_")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(combined)
    return tmp_path


# ════════════════════════════════════════════════════════════════════
#  Color swatch button
# ════════════════════════════════════════════════════════════════════

class _ColorButton(QPushButton):
    """Small button that shows a colour swatch and opens a picker."""

    color_changed = Signal(str)  # hex

    def __init__(self, initial: str = "#ffffff", parent=None):
        super().__init__(parent)
        self._color = initial
        self.setFixedSize(28, 22)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        self.clicked.connect(self._pick)

    def _update_style(self):
        self.setStyleSheet(
            f"QPushButton {{ background: {self._color}; border: 1px solid"
            f" {COLORS['border']}; border-radius: 3px; }}"
            f"QPushButton:hover {{ border-color: {COLORS['accent']}; }}"
        )

    def _pick(self):
        c = QColorDialog.getColor(QColor(self._color), self, "Pick colour")
        if c.isValid():
            self._color = c.name()
            self._update_style()
            self.color_changed.emit(self._color)

    def color(self) -> str:
        return self._color


# ════════════════════════════════════════════════════════════════════
#  GUI Page widget  (one tab of controls)
# ════════════════════════════════════════════════════════════════════

class _GUIPage(QScrollArea):
    """Scrollable page containing a set of controls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._container = QWidget()
        self._form = QVBoxLayout()
        self._form.setContentsMargins(8, 8, 8, 8)
        self._form.setSpacing(5)
        self._form.setAlignment(Qt.AlignTop)
        self._container.setLayout(self._form)
        self.setWidget(self._container)

    @property
    def form(self) -> QVBoxLayout:
        return self._form

    def finalize(self):
        self._form.addStretch()


# ════════════════════════════════════════════════════════════════════
#  ScriptGUIPanel  — the main panel shown beside the editor
# ════════════════════════════════════════════════════════════════════

class ScriptGUIPanel(QFrame):
    """Right-side panel rendered from ``# @ui.*`` annotations."""

    values_changed  = Signal(dict)   # {name: value}
    run_with_gui    = Signal(str)    # temp script path
    button_clicked  = Signal(str)    # function name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ScriptGUIPanel")
        self.setFixedWidth(300)
        self.setStyleSheet(
            f"#ScriptGUIPanel {{ background: {COLORS['bg_surface']};"
            f" border-left: 1px solid {COLORS['border']}; }}"
        )

        self._script_path: str = ""
        self._defs: list[GUIDef] = []
        self._widgets: dict[str, QWidget] = {}

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # ── Header ─────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(36)
        header.setStyleSheet(
            f"background: {COLORS['bg_root']};"
            f" border-bottom: 1px solid {COLORS['border']};"
        )
        hl = QHBoxLayout()
        hl.setContentsMargins(10, 0, 6, 0)
        hl.setSpacing(6)
        header.setLayout(hl)

        self._title_lbl = QLabel("🎮 Script GUI")
        self._title_lbl.setStyleSheet(
            f"color: {COLORS['accent']}; font-weight: 700; font-size: 12px;"
            f" font-family: 'Segoe UI';"
        )
        hl.addWidget(self._title_lbl)
        hl.addStretch()

        self._run_btn = QPushButton("▶ Run")
        self._run_btn.setObjectName("AccentButton")
        self._run_btn.setCursor(Qt.PointingHandCursor)
        self._run_btn.setFixedHeight(24)
        self._run_btn.setFixedWidth(56)
        self._run_btn.clicked.connect(self._on_run)
        self._run_btn.setStyleSheet("font-size: 10px;")
        hl.addWidget(self._run_btn)

        layout.addWidget(header)

        # ── Page tabs ──────────────────────────────────────────────
        self._tab_bar = QTabBar()
        self._tab_bar.setDrawBase(False)
        self._tab_bar.setExpanding(False)
        self._tab_bar.currentChanged.connect(self._on_tab_changed)
        self._tab_bar.setStyleSheet(
            f"QTabBar {{ background: {COLORS['bg_root']}; border: none; }}"
            f"QTabBar::tab {{ background: transparent; color: {COLORS['text_muted']};"
            f"  padding: 5px 12px; font-size: 11px; font-family: 'Segoe UI';"
            f"  border-bottom: 2px solid transparent; }}"
            f"QTabBar::tab:selected {{ color: {COLORS['accent']};"
            f"  border-bottom: 2px solid {COLORS['accent']}; }}"
            f"QTabBar::tab:hover {{ color: {COLORS['text_primary']}; }}"
        )
        self._tab_bar.setVisible(False)
        layout.addWidget(self._tab_bar)

        # ── Stacked pages ──────────────────────────────────────────
        self._stack = QStackedWidget()
        layout.addWidget(self._stack, 1)

    # ── Public API ──────────────────────────────────────────────────

    def load_gui(self, script_path: str, code: str) -> bool:
        """Parse @ui annotations and build the panel.  Returns True if any found."""
        self._script_path = script_path
        self._defs = parse_gui(code)
        self._widgets.clear()

        # Clear existing pages
        while self._stack.count():
            w = self._stack.widget(0)
            self._stack.removeWidget(w)
            w.deleteLater()
        while self._tab_bar.count():
            self._tab_bar.removeTab(0)

        if not self._defs:
            return False

        # Check for any actual widgets (not just title/page/sep/label)
        widget_kinds = {"toggle", "slider", "button", "dropdown", "number", "text", "color"}
        has_widgets = any(d.kind in widget_kinds for d in self._defs)
        if not has_widgets:
            return False

        # ── Determine title ────────────────────────────────────────
        title_text = "🎮 Script GUI"
        for d in self._defs:
            if d.kind == "title":
                title_text = f"🎮 {d.label}"
                break
        self._title_lbl.setText(title_text)

        # ── Group defs by page ─────────────────────────────────────
        pages: list[tuple[str, list[GUIDef]]] = []
        current_page_name = "General"
        current_items: list[GUIDef] = []

        for d in self._defs:
            if d.kind == "title":
                continue
            if d.kind == "page":
                if current_items:
                    pages.append((current_page_name, current_items))
                current_page_name = d.label
                current_items = []
                continue
            current_items.append(d)

        if current_items:
            pages.append((current_page_name, current_items))

        # ── Show tab bar only if >1 page ───────────────────────────
        multi = len(pages) > 1
        self._tab_bar.setVisible(multi)

        # ── Build pages ────────────────────────────────────────────
        for page_name, items in pages:
            if multi:
                self._tab_bar.addTab(page_name)
            page = _GUIPage()
            self._build_page(page, items)
            page.finalize()
            self._stack.addWidget(page)

        if multi:
            self._tab_bar.setCurrentIndex(0)
        self._stack.setCurrentIndex(0)

        return True

    def get_values(self) -> dict[str, Any]:
        """Collect current values from all widgets."""
        values: dict[str, Any] = {}
        for d in self._defs:
            if d.kind in ("title", "page", "separator", "label", "button"):
                continue
            w = self._widgets.get(d.name)
            if w is None:
                continue
            if d.kind == "toggle":
                values[d.name] = w.isChecked()
            elif d.kind == "slider":
                # Slider stores int, scale back
                values[d.name] = w.value() * d.step if d.step < 1 else w.value()
            elif d.kind == "dropdown":
                values[d.name] = w.currentText()
            elif d.kind == "number":
                values[d.name] = w.value()
            elif d.kind == "text":
                values[d.name] = w.text()
            elif d.kind == "color":
                values[d.name] = w.color()
        return values

    # ── Internal ────────────────────────────────────────────────────

    _INPUT_STYLE = (
        "background: {bg}; color: {fg};"
        " border: 1px solid {bd}; border-radius: 4px;"
        " padding: 3px 6px; font-family: Consolas; font-size: 11px;"
    )

    def _css(self) -> str:
        return self._INPUT_STYLE.format(
            bg=COLORS['bg_root'], fg=COLORS['text_primary'], bd=COLORS['border']
        )

    def _build_page(self, page: _GUIPage, items: list[GUIDef]):
        form = page.form
        for d in items:
            if d.kind == "separator":
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setFixedHeight(1)
                sep.setStyleSheet(f"background: {COLORS['border']};")
                form.addWidget(sep)
                continue

            if d.kind == "label":
                lbl = QLabel(d.label)
                lbl.setWordWrap(True)
                lbl.setStyleSheet(
                    f"color: {COLORS['text_muted']}; font-size: 11px;"
                    f" padding: 4px 0; font-family: 'Segoe UI';"
                )
                form.addWidget(lbl)
                continue

            if d.kind == "button":
                btn = QPushButton(f"  {d.label}")
                btn.setObjectName("GUIButton")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setFixedHeight(30)
                btn.setStyleSheet(
                    f"QPushButton#GUIButton {{ background: {COLORS['bg_root']};"
                    f"  color: {COLORS['text_primary']}; border: 1px solid {COLORS['border']};"
                    f"  border-radius: 4px; font-size: 11px; font-family: 'Segoe UI';"
                    f"  text-align: left; padding-left: 8px; }}"
                    f"QPushButton#GUIButton:hover {{ background: {COLORS['accent']}20;"
                    f"  border-color: {COLORS['accent']}; }}"
                    f"QPushButton#GUIButton:pressed {{ background: {COLORS['accent']}40; }}"
                )
                if d.description:
                    btn.setToolTip(d.description)
                func_name = d.name
                btn.clicked.connect(lambda checked=False, fn=func_name: self.button_clicked.emit(fn))
                form.addWidget(btn)
                continue

            # ── Labelled control ───────────────────────────────────
            lbl = QLabel(d.label)
            lbl.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-size: 10px;"
                f" font-weight: 600; margin-top: 3px; font-family: 'Segoe UI';"
            )
            if d.description:
                lbl.setToolTip(d.description)
            form.addWidget(lbl)

            if d.kind == "toggle":
                row = QFrame()
                row.setStyleSheet("QFrame { border: none; }")
                rl = QHBoxLayout()
                rl.setContentsMargins(0, 0, 0, 0)
                rl.setSpacing(6)
                row.setLayout(rl)

                cb = QCheckBox("Enabled" if d.default else "Disabled")
                cb.setChecked(bool(d.default))
                cb.setStyleSheet(
                    f"QCheckBox {{ color: {COLORS['text_primary']};"
                    f" font-size: 11px; spacing: 6px; }}"
                    f"QCheckBox::indicator {{ width: 16px; height: 16px; }}"
                )
                cb.toggled.connect(
                    lambda checked, _cb=cb: _cb.setText("Enabled" if checked else "Disabled")
                )
                rl.addWidget(cb)

                if d.description:
                    desc = QLabel(d.description)
                    desc.setStyleSheet(
                        f"color: {COLORS['text_dim']}; font-size: 9px;"
                    )
                    rl.addStretch()
                    rl.addWidget(desc)

                self._widgets[d.name] = cb
                form.addWidget(row)

            elif d.kind == "slider":
                row = QFrame()
                row.setStyleSheet("QFrame { border: none; }")
                rl = QHBoxLayout()
                rl.setContentsMargins(0, 0, 0, 0)
                rl.setSpacing(6)
                row.setLayout(rl)

                slider = QSlider(Qt.Horizontal)
                # For fractional steps, scale to int range
                if d.step < 1:
                    int_min = int(d.min_val / d.step)
                    int_max = int(d.max_val / d.step)
                    int_val = int(d.default / d.step)
                    slider.setRange(int_min, int_max)
                    slider.setValue(int_val)
                else:
                    slider.setRange(int(d.min_val), int(d.max_val))
                    slider.setValue(int(d.default))
                    slider.setSingleStep(int(d.step))

                slider.setFixedHeight(20)
                slider.setStyleSheet(
                    f"QSlider::groove:horizontal {{ background: {COLORS['bg_root']};"
                    f"  height: 4px; border-radius: 2px; }}"
                    f"QSlider::handle:horizontal {{ background: {COLORS['accent']};"
                    f"  width: 12px; height: 12px; margin: -4px 0;"
                    f"  border-radius: 6px; }}"
                    f"QSlider::sub-page:horizontal {{ background: {COLORS['accent']}; border-radius: 2px; }}"
                )
                rl.addWidget(slider, 1)

                val_lbl = QLabel(self._fmt_slider_val(d, slider.value()))
                val_lbl.setFixedWidth(46)
                val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                val_lbl.setStyleSheet(
                    f"color: {COLORS['text_primary']}; font-size: 11px;"
                    f" font-family: Consolas;"
                )
                rl.addWidget(val_lbl)

                slider.valueChanged.connect(
                    lambda v, _l=val_lbl, _d=d: _l.setText(self._fmt_slider_val(_d, v))
                )

                self._widgets[d.name] = slider
                form.addWidget(row)

            elif d.kind == "dropdown":
                cb = QComboBox()
                cb.addItems(d.options)
                if str(d.default) in d.options:
                    cb.setCurrentText(str(d.default))
                cb.setStyleSheet(self._css())
                cb.setFixedHeight(26)
                self._widgets[d.name] = cb
                form.addWidget(cb)

            elif d.kind == "number":
                if d.step < 1:
                    w = QDoubleSpinBox()
                    w.setRange(d.min_val, d.max_val)
                    w.setDecimals(max(1, len(str(d.step).split('.')[-1])))
                    w.setSingleStep(d.step)
                    w.setValue(float(d.default))
                else:
                    w = QSpinBox()
                    w.setRange(int(d.min_val), int(d.max_val))
                    w.setSingleStep(int(d.step))
                    w.setValue(int(d.default))
                w.setStyleSheet(self._css())
                w.setFixedHeight(26)
                self._widgets[d.name] = w
                form.addWidget(w)

            elif d.kind == "text":
                w = QLineEdit(str(d.default or ""))
                w.setStyleSheet(self._css())
                w.setFixedHeight(26)
                self._widgets[d.name] = w
                form.addWidget(w)

            elif d.kind == "color":
                row = QFrame()
                row.setStyleSheet("QFrame { border: none; }")
                rl = QHBoxLayout()
                rl.setContentsMargins(0, 0, 0, 0)
                rl.setSpacing(6)
                row.setLayout(rl)

                hex_edit = QLineEdit(str(d.default or "#ffffff"))
                hex_edit.setStyleSheet(self._css())
                hex_edit.setFixedHeight(24)
                hex_edit.setFixedWidth(80)
                rl.addWidget(hex_edit)

                swatch = _ColorButton(str(d.default or "#ffffff"))
                swatch.color_changed.connect(hex_edit.setText)
                hex_edit.textChanged.connect(
                    lambda txt, _s=swatch: (
                        _s._update_style() if len(txt) == 7 and txt.startswith('#') else None
                    )
                )
                rl.addWidget(swatch)
                rl.addStretch()

                self._widgets[d.name] = swatch  # swatch has .color()
                form.addWidget(row)

    @staticmethod
    def _fmt_slider_val(d: GUIDef, raw_int: int) -> str:
        if d.step < 1:
            return f"{raw_int * d.step:.2f}"
        return str(raw_int)

    def _on_tab_changed(self, idx: int):
        if 0 <= idx < self._stack.count():
            self._stack.setCurrentIndex(idx)

    def _on_run(self):
        if not self._script_path:
            return
        values = self.get_values()
        self.values_changed.emit(values)
        if values:
            tmp = create_gui_script(self._script_path, values)
            self.run_with_gui.emit(tmp)
        else:
            self.run_with_gui.emit(self._script_path)
