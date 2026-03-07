"""Base styles — root window, scrollbars, splitters, page stack."""

from ...Colors.palette import COLORS


def get_base_styles() -> str:
    C = COLORS
    return f"""

/* ===== ROOT / WINDOW ===== */
QWidget#FluxusWindow {{
    background-color: {C['bg_root']};
}}

QWidget#MainBody {{
    background-color: {C['bg_root']};
}}

/* ===== PAGE STACK ===== */
QStackedWidget#PageStack, QStackedWidget#SubNavStack {{
    background-color: {C['bg_root']};
    border: none;
}}

/* ===== SPLITTER HANDLE ===== */
QSplitter#EditorSplitter::handle {{
    background-color: {C['border']};
    height: 3px;
}}

QSplitter#EditorSplitter::handle:hover {{
    background-color: {C['accent']};
}}

/* ===== SCROLLBAR ===== */
QScrollBar:vertical {{
    background-color: {C['bg_root']};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {C['bg_hover']};
    min-height: 30px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {C['border_light']};
}}

QScrollBar::handle:vertical:pressed {{
    background-color: {C['accent_dim']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {C['bg_root']};
    height: 10px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {C['bg_hover']};
    min-width: 30px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {C['border_light']};
}}

QScrollBar::handle:horizontal:pressed {{
    background-color: {C['accent_dim']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
"""
