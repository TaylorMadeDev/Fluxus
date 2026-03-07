"""Sidebar and sub-nav styles."""

from ...Colors.palette import COLORS


def get_sidebar_styles() -> str:
    C = COLORS
    return f"""

/* ===== SIDEBAR ===== */
QFrame#Sidebar {{
    background-color: {C['bg_sidebar']};
    border-right: 1px solid {C['border']};
}}

QLabel#SidebarSection {{
    color: {C['text_dim']};
    font-family: 'Segoe UI';
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding-left: 16px;
}}

QLabel#SidebarCategory {{
    color: {C['text_dim']};
    font-family: 'Segoe UI';
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}}

QPushButton#SidebarButton {{
    background-color: transparent;
    border: none;
    border-radius: 8px;
    margin-left: 6px;
    margin-right: 6px;
    text-align: left;
    padding: 6px 10px;
}}

QPushButton#SidebarButton:hover {{
    background-color: {C['bg_hover']};
    border-left: 2px solid {C['accent_dim']};
    border-radius: 0px 8px 8px 0px;
    margin-left: 4px;
}}

QPushButton#SidebarButton:pressed {{
    background-color: {C['bg_pressed']};
    border-left: 2px solid {C['accent']};
    border-radius: 0px 8px 8px 0px;
    margin-left: 4px;
}}

QPushButton#SidebarButton:checked {{
    background-color: {C['bg_selected']};
    border-left: 3px solid {C['accent']};
    border-radius: 0px 8px 8px 0px;
    margin-left: 0px;
}}

QLabel#SidebarIcon {{
    color: {C['text_muted']};
    font-size: 15px;
}}

QLabel#SidebarLabel {{
    color: {C['text_secondary']};
    font-family: 'Segoe UI';
    font-size: 13px;
    font-weight: 500;
}}

QLabel#SidebarVersion {{
    color: {C['text_dim']};
    font-family: 'Segoe UI';
    font-size: 10px;
}}

QPushButton#SidebarCollapseBtn {{
    background-color: transparent;
    color: {C['text_muted']};
    border: none;
    border-radius: 4px;
    font-size: 16px;
}}

QPushButton#SidebarCollapseBtn:hover {{
    background-color: {C['bg_hover']};
    color: {C['text_primary']};
}}

QPushButton#SidebarCollapseBtn:pressed {{
    background-color: {C['bg_pressed']};
    color: {C['accent']};
}}

/* ===== SUB-NAV BAR ===== */
QFrame#SubNavBar {{
    background-color: {C['bg_topbar']};
    border-bottom: 1px solid {C['border']};
}}

QFrame#SubNavPage {{
    background-color: {C['bg_root']};
}}

QPushButton#SubNavButton {{
    background-color: transparent;
    color: {C['text_secondary']};
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 0;
    font-family: 'Segoe UI';
    font-size: 12px;
    font-weight: 600;
    padding: 6px 14px;
    margin: 0 2px;
}}

QPushButton#SubNavButton:hover {{
    color: {C['text_primary']};
    background-color: {C['bg_hover']};
    border-bottom: 2px solid {C['accent_dim']};
}}

QPushButton#SubNavButton:checked {{
    color: {C['accent']};
    border-bottom: 2px solid {C['accent']};
    background-color: transparent;
}}

QPushButton#SubNavButton:pressed {{
    color: {C['accent']};
    background-color: {C['bg_pressed']};
}}

/* ===== SIDEBAR SEARCH ===== */
QFrame#SidebarSearchBar {{
    background-color: transparent;
}}

QLineEdit#SidebarSearchInput {{
    background-color: {C['bg_surface']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 12px;
    padding: 4px 8px;
}}

QLineEdit#SidebarSearchInput:focus {{
    border-color: {C['accent']};
}}

QListWidget#SidebarSearchResults {{
    background-color: {C['bg_surface']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 12px;
    padding: 2px;
    outline: none;
}}

QListWidget#SidebarSearchResults::item {{
    padding: 4px 8px;
    border-radius: 4px;
}}

QListWidget#SidebarSearchResults::item:hover {{
    background-color: {C['bg_hover']};
}}

QListWidget#SidebarSearchResults::item:selected {{
    background-color: {C['accent']};
    color: {C['text_primary']};
}}
"""
