"""Top bar styles."""

from ...Colors.palette import COLORS


def get_topbar_styles() -> str:
    C = COLORS
    return f"""

/* ===== TOP BAR ===== */
QFrame#TopBar {{
    background-color: {C['bg_topbar']};
}}

QLabel#TopBarLogo {{
    color: {C['accent']};
    font-family: 'Segoe UI';
    font-size: 18px;
    font-weight: 700;
    padding-left: 8px;
    padding-right: 8px;
}}

QLabel#TopBarTitle {{
    color: {C['text_primary']};
    font-family: 'Segoe UI';
    font-size: 14px;
    font-weight: 700;
}}

QPushButton#TopBarButton {{
    background-color: {C['bg_surface']};
    color: {C['text_primary']};
    border: none;
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 12px;
    font-weight: 700;
    padding: 4px 6px;
}}

QPushButton#TopBarButton:hover {{
    background-color: {C['bg_hover']};
    color: {C['accent']};
}}

QPushButton#TopBarButton:pressed {{
    background-color: {C['bg_pressed']};
    color: {C['text_primary']};
}}

QPushButton#CloseButton {{
    background-color: {C['danger']};
    color: {C['text_primary']};
    border: none;
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 12px;
    font-weight: 700;
    padding: 4px 6px;
}}

QPushButton#CloseButton:hover {{
    background-color: {C['danger_hover']};
}}

QPushButton#CloseButton:pressed {{
    background-color: {C['danger_hover']};
}}

QPushButton#PinButton[pinned="false"] {{
    background-color: {C['bg_surface']};
    color: {C['text_primary']};
    border: none;
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 12px;
    font-weight: 700;
    padding: 4px 6px;
}}

QPushButton#PinButton[pinned="false"]:hover {{
    background-color: {C['bg_hover']};
}}

QPushButton#PinButton[pinned="false"]:pressed {{
    background-color: {C['bg_pressed']};
}}

QPushButton#PinButton[pinned="true"] {{
    background-color: {C['accent']};
    color: {C['bg_root']};
    border: none;
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 12px;
    font-weight: 700;
    padding: 4px 6px;
}}
"""
