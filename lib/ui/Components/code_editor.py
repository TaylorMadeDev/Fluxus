"""
CodeEditor — tabbed code editor with syntax highlighting, bracket matching,
minimap, autocomplete, and find/replace integration.
"""

import os
import re

from PySide6.QtCore import Qt, QRegularExpression, QSize, QRect, QStringListModel, Signal
from PySide6.QtGui import (
    QColor, QFont, QPainter, QSyntaxHighlighter, QTextCharFormat,
    QTextCursor, QTextDocument, QKeySequence, QTextBlockUserData,
)
from PySide6.QtWidgets import (
    QCompleter, QFrame, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QScrollArea, QSizePolicy, QTabWidget, QTabBar, QTextEdit,
    QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS
from .minescript_api import MINESCRIPT_API, MINESCRIPT_TYPES, get_all_completions, get_api_entry
from .plugins import get_plugin_registry
from .script_params import parse_params, ParamDef, build_injection_block, create_injected_script
from .script_gui import ScriptGUIPanel, has_gui

_AUTO_IMPORT_HEADER = "import minescript\n\n"


# ════════════════════════════════════════════════════════════════════
#  Syntax Highlighter
# ════════════════════════════════════════════════════════════════════

class PythonHighlighter(QSyntaxHighlighter):
    """Minimal Python syntax highlighter tuned for Minescript."""

    KEYWORDS = [
        "and", "as", "assert", "async", "await", "break", "class", "continue",
        "def", "del", "elif", "else", "except", "finally", "for", "from",
        "global", "if", "import", "in", "is", "lambda", "nonlocal", "not",
        "or", "pass", "raise", "return", "try", "while", "with", "yield",
        "True", "False", "None",
    ]

    BUILTINS = [
        "print", "range", "len", "int", "float", "str", "list", "dict",
        "set", "tuple", "type", "isinstance", "hasattr", "getattr", "setattr",
        "open", "input", "map", "filter", "zip", "enumerate", "sorted",
        "reversed", "abs", "min", "max", "sum", "any", "all", "super",
    ]

    PYJ_EXTRAS = [
        "echo", "player_position", "getblock", "setblock", "player",
        "execute", "job_info", "entities", "player_name", "player_health",
        "world_info", "register_chat_listener",
    ]

    # Full Minescript API names for highlighting
    MINESCRIPT_FUNCTIONS = [e.name for e in MINESCRIPT_API if "." not in e.name]

    def __init__(self, parent=None, pyj_mode: bool = False):
        super().__init__(parent)
        self._pyj = pyj_mode
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = []
        self._build_rules()

    def _fmt(self, color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFont(QFont(fmt.font().family(), -1, -1, True))
        return fmt

    def _build_rules(self) -> None:
        kw_fmt = self._fmt(COLORS["syn_keyword"], bold=True)
        for kw in self.KEYWORDS:
            self._rules.append((QRegularExpression(rf"\b{kw}\b"), kw_fmt))

        builtin_fmt = self._fmt(COLORS["syn_builtin"])
        for b in self.BUILTINS:
            self._rules.append((QRegularExpression(rf"\b{b}\b"), builtin_fmt))

        # .pyj / Minescript builtins
        if self._pyj:
            ms_fmt = self._fmt(COLORS.get("syn_function", COLORS["accent"]))
            for fn in self.PYJ_EXTRAS:
                self._rules.append((QRegularExpression(rf"\b{fn}\b"), ms_fmt))

        # Minescript API functions (always highlighted)
        ms_api_fmt = self._fmt(COLORS.get("syn_function", COLORS["accent"]))
        for fn in self.MINESCRIPT_FUNCTIONS:
            if fn not in self.PYJ_EXTRAS and fn not in self.BUILTINS:
                self._rules.append((QRegularExpression(rf"\b{fn}\b"), ms_api_fmt))

        self._rules.append((QRegularExpression(r"\bself\b"), self._fmt(COLORS["syn_self"], italic=True)))
        self._rules.append((QRegularExpression(r"\bdef\b\s+(\w+)"), self._fmt(COLORS["syn_function"])))
        self._rules.append((QRegularExpression(r"\bclass\b\s+(\w+)"), self._fmt(COLORS["syn_class"], bold=True)))
        self._rules.append((QRegularExpression(r"@\w+"), self._fmt(COLORS["syn_decorator"])))
        self._rules.append((QRegularExpression(r"\b\d+\.?\d*\b"), self._fmt(COLORS["syn_number"])))
        self._rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self._fmt(COLORS["syn_string"])))
        self._rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), self._fmt(COLORS["syn_string"])))
        self._rules.append((QRegularExpression(r"#[^\n]*"), self._fmt(COLORS["syn_comment"], italic=True)))

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                if m.lastCapturedIndex() > 0:
                    self.setFormat(m.capturedStart(1), m.capturedLength(1), fmt)
                else:
                    self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


# ════════════════════════════════════════════════════════════════════
#  Line Number Area
# ════════════════════════════════════════════════════════════════════

class LineNumberArea(QWidget):
    """Gutter showing line numbers beside the editor."""

    def __init__(self, editor: "CodeTextEdit"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return self._editor._line_number_area_width()

    def paintEvent(self, event):
        self._editor._paint_line_numbers(event)


# ════════════════════════════════════════════════════════════════════
#  Minimap
# ════════════════════════════════════════════════════════════════════

class MiniMap(QPlainTextEdit):
    """Tiny read-only overview of the document."""

    def __init__(self, source: "CodeTextEdit", parent=None):
        super().__init__(parent)
        self._source = source
        self.setObjectName("MiniMap")
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setFixedWidth(90)

        tiny = QFont("Consolas", 2)
        tiny.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(tiny)

        source.textChanged.connect(self._sync_text)
        source.verticalScrollBar().valueChanged.connect(self._sync_scroll)
        self._sync_text()

    def _sync_text(self) -> None:
        if self.toPlainText() != self._source.toPlainText():
            self.setPlainText(self._source.toPlainText())

    def _sync_scroll(self) -> None:
        src = self._source.verticalScrollBar()
        dst = self.verticalScrollBar()
        if src.maximum() > 0:
            ratio = src.value() / src.maximum()
            dst.setValue(int(ratio * dst.maximum()))

    def mousePressEvent(self, event):
        """Click to scroll the main editor."""
        if self.verticalScrollBar().maximum() > 0:
            ratio = event.pos().y() / self.height()
            src = self._source.verticalScrollBar()
            src.setValue(int(ratio * src.maximum()))


# ════════════════════════════════════════════════════════════════════
#  Text Edit with line numbers, bracket matching, autocomplete
# ════════════════════════════════════════════════════════════════════

_BRACKET_PAIRS = {"(": ")", "[": "]", "{": "}"}
_QUOTE_PAIRS = {'"': '"', "'": "'"}
_CLOSE_BRACKETS = {v: k for k, v in _BRACKET_PAIRS.items()}

_AUTOCOMPLETE_WORDS = sorted(set(
    PythonHighlighter.KEYWORDS
    + PythonHighlighter.BUILTINS
    + PythonHighlighter.PYJ_EXTRAS
    + PythonHighlighter.MINESCRIPT_FUNCTIONS
    + get_all_completions()
    + get_plugin_registry().get_all_completions()
    + [
        "minescript", "import", "from", "class", "def", "return", "self",
        # Common Python stdlib
        "os", "sys", "json", "time", "random", "math", "pathlib", "Path",
        "typing", "List", "Dict", "Optional", "Union", "Tuple", "Any",
        "dataclasses", "dataclass", "field",
        "collections", "itertools", "functools",
        "threading", "Thread", "subprocess",
        # Minescript-specific imports
        "from minescript import", "from java import",
        "EventQueue", "BlockPack", "BlockPacker", "Rotations",
        "JavaClass", "JavaObject", "AutoReleasePool",
    ]
))


class CodeTextEdit(QPlainTextEdit):
    """Editor widget with line numbers, bracket matching, autocomplete, font zoom."""

    zoom_changed = Signal(int)  # emits new font size

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CodeEditor")
        self.setTabStopDistance(32)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        self._line_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._update_line_number_width()

        # Bracket matching
        self._bracket_positions: list[int] = []
        self.cursorPositionChanged.connect(self._match_brackets)

        # Font zoom
        self._base_font_size = 11
        self._current_font_size = 11

        # Rulers
        self._ruler_columns: list[int] = []  # e.g. [80, 120]

        # Whitespace visualization
        self._show_whitespace = False

        # Indent rainbow
        self._indent_rainbow = False
        self._rainbow_colors = [
            "#2a1a3a", "#1a2a3a", "#1a3a2a", "#3a2a1a",
            "#2a2a3a", "#1a3a3a", "#3a1a2a", "#2a3a1a",
        ]

        # Autocomplete
        self._completer = QCompleter(_AUTOCOMPLETE_WORDS, self)
        self._completer.setWidget(self)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchContains)
        self._completer.activated.connect(self._insert_completion)

        # Style the popup for Minescript docs tooltip
        popup = self._completer.popup()
        popup.setStyleSheet(f"""
            QListView {{
                background: {COLORS.get('bg_surface', '#16162e')};
                color: {COLORS.get('text_primary', '#e8e6f0')};
                border: 1px solid {COLORS.get('accent', '#7c6aef')};
                border-radius: 6px;
                padding: 4px;
                font-family: 'Consolas';
                font-size: 11px;
            }}
            QListView::item:selected {{
                background: {COLORS.get('accent', '#7c6aef')};
                color: #fff;
                border-radius: 3px;
            }}
            QListView::item:hover {{
                background: {COLORS.get('bg_hover', '#1e1e3a')};
            }}
        """)

    # ── bracket matching ───────────────────────────────────────────
    def _match_brackets(self) -> None:
        extras = []
        cursor = self.textCursor()
        pos = cursor.position()
        doc = self.document()
        char_at = self._char_at(pos)
        char_before = self._char_at(pos - 1) if pos > 0 else ""

        check_pos = None
        if char_at in _BRACKET_PAIRS or char_at in _CLOSE_BRACKETS:
            check_pos = pos
        elif char_before in _BRACKET_PAIRS or char_before in _CLOSE_BRACKETS:
            check_pos = pos - 1

        if check_pos is not None:
            ch = self._char_at(check_pos)
            match_pos = self._find_matching_bracket(check_pos, ch)
            if match_pos is not None:
                for p in (check_pos, match_pos):
                    sel = QTextEdit.ExtraSelection()
                    sel.format.setBackground(QColor(COLORS.get("bracket_match", "#3a3a5c")))
                    c = self.textCursor()
                    c.setPosition(p)
                    c.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
                    sel.cursor = c
                    extras.append(sel)

        # Current line highlight
        line_sel = QTextEdit.ExtraSelection()
        line_sel.format.setBackground(QColor(COLORS.get("line_highlight", "#1e1e3a")))
        line_sel.format.setProperty(QTextCharFormat.FullWidthSelection, True)
        line_sel.cursor = self.textCursor()
        line_sel.cursor.clearSelection()
        extras.insert(0, line_sel)

        self.setExtraSelections(extras)

    def _char_at(self, pos: int) -> str:
        doc = self.document()
        if 0 <= pos < doc.characterCount():
            c = QTextCursor(doc)
            c.setPosition(pos)
            c.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            return c.selectedText()
        return ""

    def _find_matching_bracket(self, pos: int, ch: str) -> int | None:
        doc = self.document()
        if ch in _BRACKET_PAIRS:
            close = _BRACKET_PAIRS[ch]
            direction = 1
        elif ch in _CLOSE_BRACKETS:
            close = ch
            ch = _CLOSE_BRACKETS[ch]
            direction = -1
        else:
            return None

        depth = 0
        i = pos
        while 0 <= i < doc.characterCount():
            c = self._char_at(i)
            if c == ch:
                depth += 1
            elif c == close:
                depth -= 1
                if depth == 0:
                    return i
            i += direction
        return None

    # ── autocomplete ───────────────────────────────────────────────
    def keyPressEvent(self, event):
        if self._completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab, Qt.Key_Escape):
                event.ignore()
                return

        # Auto-close brackets
        ch = event.text()

        # Skip over existing closing bracket/quote
        if ch in _CLOSE_BRACKETS or ch in ('"', "'"):
            cursor = self.textCursor()
            next_char = self._char_at(cursor.position())
            if next_char == ch:
                cursor.movePosition(QTextCursor.Right)
                self.setTextCursor(cursor)
                return

        if ch in _BRACKET_PAIRS:
            super().keyPressEvent(event)
            self.insertPlainText(_BRACKET_PAIRS[ch])
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Left)
            self.setTextCursor(cursor)
            return

        # Auto-close quotes (" and ')
        if ch in _QUOTE_PAIRS:
            super().keyPressEvent(event)
            self.insertPlainText(_QUOTE_PAIRS[ch])
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Left)
            self.setTextCursor(cursor)
            return

        # Auto-indent after colon
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            cursor = self.textCursor()
            line = cursor.block().text()
            indent = len(line) - len(line.lstrip())
            super().keyPressEvent(event)
            self.insertPlainText(" " * indent)
            if line.rstrip().endswith(":"):
                self.insertPlainText("    ")
            return

        super().keyPressEvent(event)

        # Trigger completer
        tc = self.textCursor()
        tc.movePosition(QTextCursor.StartOfWord, QTextCursor.KeepAnchor)
        prefix = tc.selectedText()
        if len(prefix) >= 2:
            self._completer.setCompletionPrefix(prefix)
            if self._completer.completionCount() > 0:
                popup = self._completer.popup()
                popup.setCurrentIndex(self._completer.completionModel().index(0, 0))
                cr = self.cursorRect()
                cr.setWidth(min(
                    popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width() + 16,
                    350
                ))
                self._completer.complete(cr)

                # Show tooltip for first completion if it's a Minescript API
                first = self._completer.completionModel().data(
                    self._completer.completionModel().index(0, 0)
                )
                if first:
                    entry = get_api_entry(first)
                    if entry:
                        from PySide6.QtWidgets import QToolTip
                        global_pos = self.mapToGlobal(cr.bottomRight())
                        global_pos.setX(global_pos.x() + 220)
                        QToolTip.showText(global_pos, entry.detail_text, self)
                    else:
                        from PySide6.QtWidgets import QToolTip
                        QToolTip.hideText()
        else:
            self._completer.popup().hide()

    def _insert_completion(self, completion: str) -> None:
        tc = self.textCursor()
        tc.movePosition(QTextCursor.StartOfWord, QTextCursor.KeepAnchor)
        tc.insertText(completion)
        self.setTextCursor(tc)

    def verticalScrollBar(self):
        return super().verticalScrollBar()

    # ── Font zoom (Ctrl+Scroll) ──────────────────────────────────
    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._current_font_size = min(self._current_font_size + 1, 48)
            elif delta < 0:
                self._current_font_size = max(self._current_font_size - 1, 6)
            font = self.font()
            font.setPointSize(self._current_font_size)
            self.setFont(font)
            self.zoom_changed.emit(self._current_font_size)
            event.accept()
            return
        super().wheelEvent(event)

    def set_font_size(self, size: int) -> None:
        self._current_font_size = size
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)

    # ── Rulers ─────────────────────────────────────────────────────
    def set_rulers(self, columns: list[int]) -> None:
        self._ruler_columns = columns
        self.viewport().update()

    def set_show_whitespace(self, show: bool) -> None:
        from PySide6.QtGui import QTextOption
        self._show_whitespace = show
        opt = self.document().defaultTextOption()
        if show:
            opt.setFlags(opt.flags() | QTextOption.ShowTabsAndSpaces)
        else:
            opt.setFlags(opt.flags() & ~QTextOption.ShowTabsAndSpaces)
        self.document().setDefaultTextOption(opt)

    def set_indent_rainbow(self, enabled: bool) -> None:
        self._indent_rainbow = enabled
        self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())

        # Draw ruler lines
        if self._ruler_columns:
            for col in self._ruler_columns:
                x = self.fontMetrics().horizontalAdvance("9") * col - self.horizontalScrollBar().value()
                painter.setPen(QColor(COLORS.get("border", "#2a2a4a")))
                painter.drawLine(x, 0, x, self.viewport().height())

        # Draw indent rainbow
        if self._indent_rainbow:
            block = self.firstVisibleBlock()
            while block.isValid():
                geom = self.blockBoundingGeometry(block).translated(self.contentOffset())
                if geom.top() > self.viewport().height():
                    break
                text = block.text()
                indent = len(text) - len(text.lstrip()) if text.strip() else 0
                if indent > 0:
                    tab_size = 4
                    for level in range(0, indent, tab_size):
                        color_idx = (level // tab_size) % len(self._rainbow_colors)
                        x_start = self.fontMetrics().horizontalAdvance(" ") * level
                        x_end = self.fontMetrics().horizontalAdvance(" ") * min(level + tab_size, indent)
                        painter.fillRect(
                            int(x_start - self.horizontalScrollBar().value()),
                            int(geom.top()),
                            int(x_end - x_start),
                            int(geom.height()),
                            QColor(self._rainbow_colors[color_idx]),
                        )
                block = block.next()

        painter.end()

    # ── line numbers ───────────────────────────────────────────────
    def _line_number_area_width(self):
        digits = max(3, len(str(self.blockCount())))
        space = 12 + self.fontMetrics().horizontalAdvance("9") * digits
        return QSize(space, 0)

    def _update_line_number_width(self) -> None:
        self.setViewportMargins(self._line_number_area_width().width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self._line_area.scroll(0, dy)
        else:
            self._line_area.update(0, rect.y(), self._line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_area.setGeometry(cr.left(), cr.top(), self._line_number_area_width().width(), cr.height())

    def _paint_line_numbers(self, event):
        painter = QPainter(self._line_area)
        painter.fillRect(event.rect(), QColor(COLORS["bg_sidebar"]))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(COLORS["text_dim"]))
                painter.setFont(self.font())
                painter.drawText(
                    0, top, self._line_area.width() - 6,
                    self.fontMetrics().height(),
                    Qt.AlignRight, number
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1
        painter.end()


# ════════════════════════════════════════════════════════════════════
#  Editor Tab — one per open file
# ════════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════════
#  Inline Parameters Panel (right side of editor)
# ════════════════════════════════════════════════════════════════════

class InlineParamsPanel(QFrame):
    """Collapsible parameters panel shown to the right of the editor."""

    params_changed = Signal(dict)       # {name: value}
    run_with_params = Signal(str)       # temp script path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("InlineParamsPanel")
        self.setFixedWidth(280)
        self.setStyleSheet(
            f"QFrame#InlineParamsPanel {{"
            f"  background: {COLORS['bg_surface']};"
            f"  border-left: 1px solid {COLORS['border']};"
            f"}}"
        )
        self._widgets: dict[str, QWidget] = {}
        self._params: list[ParamDef] = []
        self._script_path: str | None = None
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Header
        header = QFrame()
        header.setFixedHeight(32)
        header.setStyleSheet(
            f"background: {COLORS['bg_root']};"
            f" border-bottom: 1px solid {COLORS['border']};"
        )
        hl = QHBoxLayout()
        hl.setContentsMargins(10, 0, 6, 0)
        hl.setSpacing(6)
        header.setLayout(hl)

        title = QLabel("⚙ Parameters")
        title.setStyleSheet(
            f"color: {COLORS['accent']}; font-weight: 700; font-size: 11px;"
            f" font-family: 'Segoe UI';"
        )
        hl.addWidget(title)
        hl.addStretch()

        self._run_btn = QPushButton("▶ Run")
        self._run_btn.setObjectName("AccentButton")
        self._run_btn.setCursor(Qt.PointingHandCursor)
        self._run_btn.setFixedHeight(22)
        self._run_btn.setFixedWidth(56)
        self._run_btn.clicked.connect(self._on_run)
        self._run_btn.setStyleSheet(f"font-size: 10px;")
        hl.addWidget(self._run_btn)

        layout.addWidget(header)

        # Scroll area for params
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._container = QWidget()
        self._form = QVBoxLayout()
        self._form.setContentsMargins(8, 8, 8, 8)
        self._form.setSpacing(5)
        self._form.setAlignment(Qt.AlignTop)
        self._container.setLayout(self._form)
        scroll.setWidget(self._container)
        layout.addWidget(scroll, 1)

    def load_params(self, script_path: str, code: str) -> bool:
        """Parse params from code. Returns True if params exist."""
        self._script_path = script_path
        self._params = parse_params(code)
        self._widgets.clear()

        # Clear form
        while self._form.count():
            item = self._form.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        has_params = any(p.kind != "header" for p in self._params)
        if not has_params:
            return False

        _INPUT_STYLE = (
            f"background: {COLORS['bg_root']}; color: {COLORS['text_primary']};"
            f" border: 1px solid {COLORS['border']}; border-radius: 3px;"
            f" padding: 3px 5px; font-family: Consolas; font-size: 11px;"
        )

        for param in self._params:
            if param.kind == "header":
                hdr = QLabel(param.name)
                hdr.setStyleSheet(
                    f"color: {COLORS['accent']}; font-size: 11px; font-weight: 700;"
                    f" padding: 6px 0 2px 0;"
                    f" border-bottom: 1px solid {COLORS['border']};"
                )
                self._form.addWidget(hdr)
                continue

            # Label
            lbl = QLabel(param.name)
            lbl.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-size: 10px;"
                f" font-weight: 600; margin-top: 2px;"
            )
            if param.description:
                lbl.setToolTip(param.description)
            self._form.addWidget(lbl)

            value = param.default

            if param.kind == "string":
                w = QLineEdit(str(value or ""))
                w.setStyleSheet(_INPUT_STYLE)
                w.setFixedHeight(24)
                self._widgets[param.name] = w
                self._form.addWidget(w)

            elif param.kind == "int":
                from PySide6.QtWidgets import QSpinBox
                w = QSpinBox()
                w.setRange(-999999, 999999)
                w.setValue(int(value) if value is not None else 0)
                w.setStyleSheet(_INPUT_STYLE)
                w.setFixedHeight(24)
                self._widgets[param.name] = w
                self._form.addWidget(w)

            elif param.kind == "float":
                from PySide6.QtWidgets import QDoubleSpinBox
                w = QDoubleSpinBox()
                w.setRange(-999999.0, 999999.0)
                w.setDecimals(3)
                w.setValue(float(value) if value is not None else 0.0)
                w.setStyleSheet(_INPUT_STYLE)
                w.setFixedHeight(24)
                self._widgets[param.name] = w
                self._form.addWidget(w)

            elif param.kind == "bool":
                from PySide6.QtWidgets import QCheckBox
                w = QCheckBox("Enabled")
                w.setChecked(bool(value))
                w.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 11px;")
                self._widgets[param.name] = w
                self._form.addWidget(w)

            elif param.kind == "dropdown":
                from PySide6.QtWidgets import QComboBox
                w = QComboBox()
                w.addItems(param.options)
                if str(value) in param.options:
                    w.setCurrentText(str(value))
                w.setStyleSheet(_INPUT_STYLE)
                w.setFixedHeight(24)
                self._widgets[param.name] = w
                self._form.addWidget(w)

        self._form.addStretch()
        return True

    def get_values(self) -> dict:
        values = {}
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

    def _on_run(self) -> None:
        if not self._script_path:
            return
        values = self.get_values()
        self.params_changed.emit(values)
        if values:
            tmp = create_injected_script(self._script_path, values)
            self.run_with_params.emit(tmp)
        else:
            self.run_with_params.emit(self._script_path)


# ════════════════════════════════════════════════════════════════════
#  Editor Tab — one per open file
# ════════════════════════════════════════════════════════════════════

class _EditorTab:
    """Lightweight container holding one file's state."""

    def __init__(self, filepath: str | None = None):
        self.filepath = filepath
        self.editor = CodeTextEdit()
        self.minimap = MiniMap(self.editor)
        self.params_panel = InlineParamsPanel()
        self.gui_panel = ScriptGUIPanel()
        self.highlighter = PythonHighlighter(
            self.editor.document(),
            pyj_mode=bool(filepath and filepath.endswith(".pyj")),
        )
        self.modified = False

        # Wrap in a QWidget with editor + minimap + params/gui side-by-side
        self.widget = QWidget()
        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(0)
        hl.addWidget(self.editor, 1)
        hl.addWidget(self.minimap)
        hl.addWidget(self.params_panel)
        hl.addWidget(self.gui_panel)
        self.widget.setLayout(hl)

        # Panels start hidden; shown when file has relevant annotations
        self.params_panel.setVisible(False)
        self.gui_panel.setVisible(False)

        self.editor.textChanged.connect(self._on_modified)

    def _on_modified(self) -> None:
        self.modified = True

    def refresh_params(self) -> None:
        """Re-parse params from current editor text and show/hide panel."""
        code = self.editor.toPlainText()
        has = self.params_panel.load_params(self.filepath or "", code)
        self.params_panel.setVisible(has)

    def refresh_gui(self) -> None:
        """Re-parse @ui annotations from current editor text and show/hide GUI panel."""
        code = self.editor.toPlainText()
        has = self.gui_panel.load_gui(self.filepath or "", code)
        self.gui_panel.setVisible(has)

    @property
    def label(self) -> str:
        name = os.path.basename(self.filepath) if self.filepath else "untitled.py"
        return f"● {name}" if self.modified else name


# ════════════════════════════════════════════════════════════════════
#  CodeEditor (main panel — toolbar + tabs + find/replace + status)
# ════════════════════════════════════════════════════════════════════

class CodeEditor(QFrame):
    """Full editor panel with tabs, toolbar, find/replace, and status bar."""

    file_opened = Signal(str)   # emitted when a file is opened (path)
    file_saved  = Signal(str)   # emitted when a file is saved  (path)
    run_requested = Signal(str) # emitted when Run is clicked (path)
    import_plugins_requested = Signal()  # emitted when Import Plugins is clicked
    zen_mode_toggled = Signal(bool)  # emitted when zen mode is toggled

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CodeEditorPanel")
        self._tabs_data: list[_EditorTab] = []
        self._recent_files: list[str] = []
        self._zen_mode = False
        self._word_wrap = False
        self._rulers_visible = False
        self._whitespace_visible = False
        self._indent_rainbow = False
        self._build()
        # Start with one empty tab pre-populated with import
        self.new_file()

    def _build(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # ── Breadcrumbs bar ────────────────────────────────────────
        self._breadcrumbs = QFrame(self)
        self._breadcrumbs.setObjectName("BreadcrumbsBar")
        self._breadcrumbs.setFixedHeight(24)
        self._bc_layout = QHBoxLayout()
        self._bc_layout.setContentsMargins(10, 0, 10, 0)
        self._bc_layout.setSpacing(4)
        self._breadcrumbs.setLayout(self._bc_layout)
        self._bc_label = QLabel("")
        self._bc_label.setObjectName("BreadcrumbsLabel")
        self._bc_label.setStyleSheet(
            f"color: {COLORS.get('text_dim', '#6a6a8a')};"
            f" font-size: 10px; font-family: 'Consolas';"
        )
        self._bc_layout.addWidget(self._bc_label)
        self._bc_layout.addStretch()
        layout.addWidget(self._breadcrumbs)

        # ── Toolbar ────────────────────────────────────────────────
        toolbar = QFrame(self)
        toolbar.setObjectName("EditorToolbar")
        toolbar.setFixedHeight(36)
        tb_layout = QHBoxLayout()
        tb_layout.setContentsMargins(10, 0, 10, 0)
        tb_layout.setSpacing(6)
        toolbar.setLayout(tb_layout)

        self._file_label = QLabel("untitled.py")
        self._file_label.setObjectName("EditorFileLabel")
        tb_layout.addWidget(self._file_label)

        self._mod_indicator = QLabel("")
        self._mod_indicator.setObjectName("EditorModIndicator")
        self._mod_indicator.setFixedWidth(14)
        tb_layout.addWidget(self._mod_indicator)

        tb_layout.addStretch()

        for text, slot in [
            ("New", self.new_file),
            ("Open", self.open_file),
            ("Save", self.save_file),
            ("Save As", self.save_file_as),
        ]:
            btn = QPushButton(text)
            btn.setObjectName("EditorToolButton")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(slot)
            tb_layout.addWidget(btn)

        # Save All button
        save_all_btn = QPushButton("Save All")
        save_all_btn.setObjectName("EditorToolButton")
        save_all_btn.setCursor(Qt.PointingHandCursor)
        save_all_btn.setToolTip("Save all open files (Ctrl+Shift+S)")
        save_all_btn.clicked.connect(self.save_all)
        tb_layout.addWidget(save_all_btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background: {COLORS.get('border', '#2a2a4a')};")
        tb_layout.addWidget(sep)

        # Word wrap toggle
        self._wrap_btn = QPushButton("↔")
        self._wrap_btn.setObjectName("EditorToolButton")
        self._wrap_btn.setCursor(Qt.PointingHandCursor)
        self._wrap_btn.setToolTip("Toggle word wrap")
        self._wrap_btn.setCheckable(True)
        self._wrap_btn.setFixedWidth(28)
        self._wrap_btn.clicked.connect(self._toggle_word_wrap)
        tb_layout.addWidget(self._wrap_btn)

        # Rulers toggle
        self._ruler_btn = QPushButton("│")
        self._ruler_btn.setObjectName("EditorToolButton")
        self._ruler_btn.setCursor(Qt.PointingHandCursor)
        self._ruler_btn.setToolTip("Toggle ruler lines (80, 120)")
        self._ruler_btn.setCheckable(True)
        self._ruler_btn.setFixedWidth(28)
        self._ruler_btn.clicked.connect(self._toggle_rulers)
        tb_layout.addWidget(self._ruler_btn)

        # Whitespace toggle
        self._ws_btn = QPushButton("·")
        self._ws_btn.setObjectName("EditorToolButton")
        self._ws_btn.setCursor(Qt.PointingHandCursor)
        self._ws_btn.setToolTip("Toggle whitespace visualization")
        self._ws_btn.setCheckable(True)
        self._ws_btn.setFixedWidth(28)
        self._ws_btn.clicked.connect(self._toggle_whitespace)
        tb_layout.addWidget(self._ws_btn)

        # Indent rainbow toggle
        self._rainbow_btn = QPushButton("🌈")
        self._rainbow_btn.setObjectName("EditorToolButton")
        self._rainbow_btn.setCursor(Qt.PointingHandCursor)
        self._rainbow_btn.setToolTip("Toggle indent rainbow")
        self._rainbow_btn.setCheckable(True)
        self._rainbow_btn.setFixedWidth(28)
        self._rainbow_btn.clicked.connect(self._toggle_indent_rainbow)
        tb_layout.addWidget(self._rainbow_btn)

        # Zen mode
        self._zen_btn = QPushButton("🧘")
        self._zen_btn.setObjectName("EditorToolButton")
        self._zen_btn.setCursor(Qt.PointingHandCursor)
        self._zen_btn.setToolTip("Zen mode — distraction-free editing")
        self._zen_btn.setCheckable(True)
        self._zen_btn.setFixedWidth(28)
        self._zen_btn.clicked.connect(self._toggle_zen)
        tb_layout.addWidget(self._zen_btn)

        # Separator 2
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setFixedWidth(1)
        sep2.setStyleSheet(f"background: {COLORS.get('border', '#2a2a4a')};")
        tb_layout.addWidget(sep2)

        # Import Plugins button
        import_btn = QPushButton("📦 Plugins")
        import_btn.setObjectName("EditorToolButton")
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.setToolTip("Insert import lines for enabled plugins")
        import_btn.clicked.connect(self._insert_plugin_imports)
        tb_layout.addWidget(import_btn)

        # Run button
        run_btn = QPushButton("▶ Run")
        run_btn.setObjectName("AccentButton")
        run_btn.setCursor(Qt.PointingHandCursor)
        run_btn.setToolTip("Run current script (F5)")
        run_btn.clicked.connect(self._on_run_clicked)
        tb_layout.addWidget(run_btn)

        self._toolbar = toolbar
        layout.addWidget(toolbar)

        # ── Tab Bar ────────────────────────────────────────────────
        self._tab_widget = QTabWidget()
        self._tab_widget.setObjectName("EditorTabs")
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.setMovable(True)
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.currentChanged.connect(self._on_tab_changed)
        self._tab_widget.tabCloseRequested.connect(self.close_tab)
        layout.addWidget(self._tab_widget, 1)

        # ── Find/Replace bar placeholder (injected from outside) ──
        self._find_replace_slot = QVBoxLayout()
        self._find_replace_slot.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self._find_replace_slot)

        # ── Status line ────────────────────────────────────────────
        status = QFrame(self)
        status.setObjectName("EditorStatus")
        status.setFixedHeight(24)
        st_layout = QHBoxLayout()
        st_layout.setContentsMargins(12, 0, 12, 0)
        st_layout.setSpacing(16)
        status.setLayout(st_layout)

        self._cursor_label = QLabel("Ln 1, Col 1")
        self._cursor_label.setObjectName("EditorStatusText")
        st_layout.addWidget(self._cursor_label)
        st_layout.addStretch()

        self._lang_label = QLabel("Python")
        self._lang_label.setObjectName("EditorStatusText")
        st_layout.addWidget(self._lang_label)

        self._encoding_label = QLabel("UTF-8")
        self._encoding_label.setObjectName("EditorStatusText")
        st_layout.addWidget(self._encoding_label)

        layout.addWidget(status)

    # ── Tab management ─────────────────────────────────────────────
    def _add_tab(self, filepath: str | None) -> _EditorTab:
        tab = _EditorTab(filepath)
        self._tabs_data.append(tab)
        idx = self._tab_widget.addTab(tab.widget, tab.label)
        self._tab_widget.setCurrentIndex(idx)
        tab.editor.textChanged.connect(lambda: self._update_tab_label(tab))
        tab.editor.cursorPositionChanged.connect(self._update_cursor_pos)
        return tab

    def _update_tab_label(self, tab: _EditorTab) -> None:
        idx = self._index_of(tab)
        if idx >= 0:
            self._tab_widget.setTabText(idx, tab.label)
        self._update_title()

    def _index_of(self, tab: _EditorTab) -> int:
        for i in range(self._tab_widget.count()):
            if self._tab_widget.widget(i) is tab.widget:
                return i
        return -1

    def _current_tab(self) -> _EditorTab | None:
        idx = self._tab_widget.currentIndex()
        if 0 <= idx < len(self._tabs_data):
            # find by widget
            w = self._tab_widget.widget(idx)
            for t in self._tabs_data:
                if t.widget is w:
                    return t
        return None

    def close_tab(self, index: int) -> None:
        if self._tab_widget.count() <= 1:
            return  # keep at least one tab
        w = self._tab_widget.widget(index)
        for t in self._tabs_data:
            if t.widget is w:
                self._tabs_data.remove(t)
                break
        self._tab_widget.removeTab(index)

    def _on_tab_changed(self, index: int) -> None:
        self._update_title()
        self._update_cursor_pos()
        self._update_breadcrumbs()

    # ── Toggle helpers ─────────────────────────────────────────────
    def _toggle_word_wrap(self) -> None:
        self._word_wrap = self._wrap_btn.isChecked()
        mode = QTextEdit.WidgetWidth if self._word_wrap else QTextEdit.NoWrap
        for td in self._tabs_data:
            td.editor.setLineWrapMode(mode)

    def _toggle_rulers(self) -> None:
        self._rulers_visible = self._ruler_btn.isChecked()
        cols = [80, 120] if self._rulers_visible else []
        for td in self._tabs_data:
            td.editor.set_rulers(cols)

    def _toggle_whitespace(self) -> None:
        self._whitespace_visible = self._ws_btn.isChecked()
        for td in self._tabs_data:
            td.editor.set_show_whitespace(self._whitespace_visible)

    def _toggle_indent_rainbow(self) -> None:
        self._indent_rainbow = self._rainbow_btn.isChecked()
        for td in self._tabs_data:
            td.editor.set_indent_rainbow(self._indent_rainbow)

    def _toggle_zen(self) -> None:
        self._zen_mode = self._zen_btn.isChecked()
        self.zen_mode_toggled.emit(self._zen_mode)

    def _update_breadcrumbs(self) -> None:
        t = self._current_tab()
        if t and t.filepath:
            parts = t.filepath.replace("\\", "/").split("/")
            # Show last 3 parts
            display = " › ".join(parts[-3:]) if len(parts) > 3 else " › ".join(parts)
            self._bc_label.setText(display)
        else:
            self._bc_label.setText("untitled.py")

    def save_all(self) -> None:
        """Save all open files that have unsaved changes."""
        for td in self._tabs_data:
            if td.modified and td.filepath:
                self._write_file(td, td.filepath)

    # ── Public API ─────────────────────────────────────────────────
    def set_content(self, text: str, filepath: str | None = None) -> None:
        """Open text in a new tab (or reuse if same path is open)."""
        # Check if already open
        for t in self._tabs_data:
            if t.filepath and filepath and os.path.normpath(t.filepath) == os.path.normpath(filepath):
                idx = self._index_of(t)
                if idx >= 0:
                    self._tab_widget.setCurrentIndex(idx)
                return

        tab = self._add_tab(filepath)
        tab.editor.setPlainText(text)
        tab.modified = False
        tab.highlighter = PythonHighlighter(
            tab.editor.document(),
            pyj_mode=bool(filepath and filepath.endswith(".pyj")),
        )
        self._update_tab_label(tab)

        if filepath:
            self._push_recent(filepath)
            self.file_opened.emit(filepath)

        # Set font
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        tab.editor.setFont(font)
        tab.minimap.setFont(QFont("Consolas", 2))

        # Language label
        if filepath and filepath.endswith(".pyj"):
            self._lang_label.setText("Python (Minescript .pyj)")
        else:
            self._lang_label.setText("Python")

        # Refresh inline parameters panel and GUI panel
        tab.refresh_params()
        tab.refresh_gui()

    def get_content(self) -> str:
        t = self._current_tab()
        return t.editor.toPlainText() if t else ""

    def get_current_file(self) -> str | None:
        t = self._current_tab()
        return t.filepath if t else None

    def get_editor(self) -> CodeTextEdit | None:
        """Return the currently focused CodeTextEdit for find/replace."""
        t = self._current_tab()
        return t.editor if t else None

    def insert_text(self, text: str) -> None:
        """Insert text at cursor in the active tab."""
        t = self._current_tab()
        if t:
            t.editor.insertPlainText(text)

    def _on_run_clicked(self) -> None:
        """Save (if needed) and emit run_requested with the current file path."""
        t = self._current_tab()
        if not t:
            return
        # Auto-save before running
        if t.filepath and t.modified:
            self._write_file(t, t.filepath)
        if t.filepath:
            self.run_requested.emit(t.filepath)

    def _insert_plugin_imports(self) -> None:
        """Show a popup with checkboxes for all plugins to import."""
        from .plugins_panel import PluginImportDialog
        t = self._current_tab()
        if not t:
            return

        dlg = PluginImportDialog(self)

        def _do_insert(import_lines: list[str]):
            if not import_lines:
                return
            content = t.editor.toPlainText()
            to_insert = [line for line in import_lines if line not in content]
            if not to_insert:
                return
            lines = content.split("\n")
            insert_idx = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("from "):
                    insert_idx = i + 1
                elif stripped and not stripped.startswith("#"):
                    break
            for j, imp in enumerate(to_insert):
                lines.insert(insert_idx + j, imp)
            t.editor.setPlainText("\n".join(lines))
            cursor = t.editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            for _ in range(insert_idx + len(to_insert)):
                cursor.movePosition(QTextCursor.Down)
            t.editor.setTextCursor(cursor)

        dlg.import_selected.connect(_do_insert)
        dlg.exec()

    def get_recent_files(self) -> list[str]:
        return list(self._recent_files)

    def _push_recent(self, path: str) -> None:
        norm = os.path.normpath(path)
        if norm in self._recent_files:
            self._recent_files.remove(norm)
        self._recent_files.insert(0, norm)
        self._recent_files = self._recent_files[:15]

    # ── Slots ──────────────────────────────────────────────────────
    def new_file(self) -> None:
        tab = self._add_tab(None)
        # Auto-insert import minescript for new files
        tab.editor.setPlainText(_AUTO_IMPORT_HEADER)
        # Place cursor after the import
        cursor = tab.editor.textCursor()
        cursor.movePosition(QTextCursor.End)
        tab.editor.setTextCursor(cursor)
        tab.modified = False
        self._update_tab_label(tab)

    def open_file(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Script", "", "Python Files (*.py *.pyj);;All Files (*)"
        )
        if path:
            self.open_path(path)

    def open_path(self, path: str) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.set_content(f.read(), path)
        except Exception:
            pass

    def save_file(self) -> None:
        t = self._current_tab()
        if not t:
            return
        if t.filepath:
            self._write_file(t, t.filepath)
        else:
            self.save_file_as()

    def save_file_as(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Script", "", "Python Files (*.py);;All Files (*)"
        )
        if path:
            t = self._current_tab()
            if t:
                self._write_file(t, path)

    def _write_file(self, tab: _EditorTab, path: str) -> None:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(tab.editor.toPlainText())
            tab.filepath = path
            tab.modified = False
            self._update_tab_label(tab)
            self._push_recent(path)
            self.file_saved.emit(path)
        except Exception:
            pass

    def _update_title(self) -> None:
        t = self._current_tab()
        if t:
            name = os.path.basename(t.filepath) if t.filepath else "untitled.py"
            self._file_label.setText(name)
            self._mod_indicator.setText("●" if t.modified else "")
        else:
            self._file_label.setText("untitled.py")
            self._mod_indicator.setText("")

    def _update_cursor_pos(self) -> None:
        t = self._current_tab()
        if t:
            cursor = t.editor.textCursor()
            line = cursor.blockNumber() + 1
            col = cursor.columnNumber() + 1
            self._cursor_label.setText(f"Ln {line}, Col {col}")
