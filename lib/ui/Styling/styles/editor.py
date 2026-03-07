"""Editor, code area, tabs, minimap, find/replace styles."""

from pathlib import Path

from ...Colors.palette import COLORS

_ICONS_DIR = Path(__file__).resolve().parents[2] / "Icons"


def get_editor_styles() -> str:
    C = COLORS
    # Qt stylesheet url() needs forward slashes
    _icon_close = (_ICONS_DIR / "tab-close.svg").as_posix()
    _icon_close_hover = (_ICONS_DIR / "tab-close-hover.svg").as_posix()
    return f"""

/* ===== EDITOR ===== */
QFrame#CodeEditorPanel {{
    background-color: {C['bg_editor']};
    border: none;
}}

QFrame#EditorToolbar {{
    background-color: {C['bg_topbar']};
    border-bottom: 1px solid {C['border']};
}}

QLabel#EditorFileLabel {{
    color: {C['text_primary']};
    font-family: 'Segoe UI';
    font-size: 12px;
    font-weight: 600;
}}

QLabel#EditorModIndicator {{
    color: {C['warning']};
    font-size: 14px;
    font-weight: 700;
}}

QPushButton#EditorToolButton {{
    background-color: {C['bg_surface']};
    color: {C['text_secondary']};
    border: 1px solid {C['border']};
    border-radius: 5px;
    font-family: 'Segoe UI';
    font-size: 11px;
    font-weight: 600;
    padding: 4px 12px;
}}

QPushButton#EditorToolButton:hover {{
    background-color: {C['bg_hover']};
    color: {C['text_primary']};
    border-color: {C['border_light']};
}}

QPushButton#EditorToolButton:pressed {{
    background-color: {C['bg_pressed']};
}}

QPlainTextEdit#CodeEditor {{
    background-color: {C['bg_editor']};
    color: {C['text_primary']};
    border: none;
    selection-background-color: {C['bg_selected']};
    selection-color: {C['text_primary']};
    font-family: 'Consolas';
    font-size: 13px;
}}

QFrame#EditorStatus {{
    background-color: {C['bg_topbar']};
    border-top: 1px solid {C['border']};
}}

QLabel#EditorStatusText {{
    color: {C['text_dim']};
    font-family: 'Segoe UI';
    font-size: 11px;
}}

/* ===== TAB BAR (Editor Tabs) ===== */
QTabWidget#EditorTabs::pane {{
    border: none;
    background-color: {C['bg_root']};
}}

QTabWidget#EditorTabs > QTabBar::tab {{
    background-color: {C['bg_sidebar']};
    color: {C['text_secondary']};
    border: none;
    border-right: 1px solid {C['border']};
    font-family: 'Segoe UI';
    font-size: 12px;
    font-weight: 500;
    padding: 6px 16px;
    min-width: 100px;
}}

QTabWidget#EditorTabs > QTabBar::tab:selected {{
    background-color: {C['bg_root']};
    color: {C['text_primary']};
    border-bottom: 2px solid {C['accent']};
}}

QTabWidget#EditorTabs > QTabBar::tab:hover:!selected {{
    background-color: {C['bg_hover']};
    color: {C['text_primary']};
    border-bottom: 2px solid {C['accent_dim']};
}}

QTabWidget#EditorTabs > QTabBar::close-button {{
    image: url({_icon_close});
    subcontrol-position: right;
    border: none;
    background: transparent;
    padding: 4px;
    margin-right: 4px;
    width: 12px;
    height: 12px;
}}

QTabWidget#EditorTabs > QTabBar::close-button:hover {{
    image: url({_icon_close_hover});
    background-color: {C['bg_hover']};
    border-radius: 3px;
}}

/* ===== MINIMAP ===== */
QPlainTextEdit#MiniMap {{
    background-color: {C['bg_sidebar']};
    color: {C['text_dim']};
    border: none;
    border-left: 1px solid {C['border']};
    selection-background-color: transparent;
}}

/* ===== FIND / REPLACE BAR ===== */
QFrame#FindReplaceBar {{
    background-color: {C['bg_topbar']};
    border-top: 1px solid {C['border']};
    padding: 4px 8px;
}}

QFrame#FindReplaceBar QLineEdit {{
    background-color: {C['bg_surface']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 4px;
    font-family: 'Segoe UI';
    font-size: 12px;
    padding: 3px 8px;
    min-width: 180px;
}}

QFrame#FindReplaceBar QLineEdit:focus {{
    border-color: {C['accent']};
}}

QFrame#FindReplaceBar QPushButton {{
    background-color: {C['bg_surface']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 4px;
    font-size: 12px;
    padding: 3px 8px;
}}

QFrame#FindReplaceBar QPushButton:hover {{
    background-color: {C['bg_hover']};
}}

QFrame#FindReplaceBar QLabel {{
    color: {C['text_muted']};
    font-family: 'Segoe UI';
    font-size: 11px;
}}

QFrame#FindReplaceBar QCheckBox {{
    color: {C['text_secondary']};
    font-size: 11px;
    spacing: 4px;
}}
"""
