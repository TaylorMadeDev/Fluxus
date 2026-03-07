"""Component styles — buttons, inputs, cards, toasts, dialogs, command palette, status bar."""

from ...Colors.palette import COLORS


def get_component_styles() -> str:
    C = COLORS
    return f"""

/* ===== SMALL BUTTONS ===== */
QPushButton#SmallButton {{
    background-color: {C['bg_surface']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    min-width: 28px;
}}

QPushButton#SmallButton:hover {{
    background-color: {C['bg_hover']};
    border-color: {C['border_light']};
}}

QPushButton#SmallButton:pressed {{
    background-color: {C['bg_pressed']};
}}

QPushButton#DangerSmallButton {{
    background-color: {C['danger']};
    color: {C['text_primary']};
    border: none;
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
}}

QPushButton#DangerSmallButton:hover {{
    background-color: {C['danger_hover']};
}}

QPushButton#DangerSmallButton:disabled {{
    background-color: {C['bg_surface']};
    color: {C['text_dim']};
}}

QPushButton#DangerSmallButton:pressed {{
    background-color: {C['danger']};
    padding: 2px 5px;
}}

QPushButton#AccentButton {{
    background-color: {C['accent']};
    color: {C['bg_root']};
    border: none;
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 12px;
    font-weight: 700;
    padding: 6px 14px;
}}

QPushButton#AccentButton:hover {{
    background-color: {C['accent_hover']};
    padding: 6px 16px;
}}

QPushButton#AccentButton:pressed {{
    background-color: {C['accent_dim']};
    padding: 6px 13px;
}}

/* ===== STATUS BAR ===== */
QFrame#StatusBar {{
    background-color: {C['bg_topbar']};
    border-top: 1px solid {C['border']};
}}

QLabel#StatusText {{
    color: {C['text_dim']};
    font-family: 'Segoe UI';
    font-size: 11px;
}}

QLabel#StatusSep {{
    color: {C['border']};
    font-size: 11px;
}}

QLabel#HudText {{
    color: {C['accent']};
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 11px;
}}

/* ===== TOAST NOTIFICATIONS ===== */
QFrame#Toast {{
    background-color: {C['bg_card']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    padding: 8px 14px;
}}

QFrame#Toast QLabel {{
    color: {C['text_primary']};
    font-family: 'Segoe UI';
    font-size: 12px;
}}

/* ===== COMMAND PALETTE ===== */
QDialog#CommandPalette {{
    background-color: {C['bg_root']};
    border: 1px solid {C['border']};
    border-radius: 10px;
}}

QDialog#CommandPalette QLineEdit {{
    background-color: {C['bg_surface']};
    color: {C['text_primary']};
    border: none;
    border-bottom: 1px solid {C['border']};
    font-family: 'Segoe UI';
    font-size: 14px;
    padding: 10px 14px;
}}

QDialog#CommandPalette QListWidget {{
    background-color: {C['bg_root']};
    color: {C['text_secondary']};
    border: none;
    font-family: 'Segoe UI';
    font-size: 13px;
    outline: none;
}}

QDialog#CommandPalette QListWidget::item {{
    padding: 6px 14px;
    border: none;
}}

QDialog#CommandPalette QListWidget::item:selected {{
    background-color: {C['bg_selected']};
    color: {C['text_primary']};
}}

QDialog#CommandPalette QListWidget::item:hover:!selected {{
    background-color: {C['bg_hover']};
}}

/* ===== FRONT PAGE ===== */
QFrame#FrontPage {{
    background-color: {C['bg_root']};
    border: none;
}}

QFrame#FrontPageHeader {{
    background-color: {C['bg_topbar']};
    border-bottom: 1px solid {C['border']};
}}

QLabel#FrontPageLogo {{
    color: {C['accent']};
    font-family: 'Segoe UI';
    font-size: 24px;
    font-weight: 700;
}}

QLabel#FrontPageTitle {{
    color: {C['text_primary']};
    font-family: 'Segoe UI';
    font-size: 16px;
    font-weight: 700;
}}

QLabel#PlayerBadge {{
    color: {C['accent']};
    background-color: {C['bg_badge']};
    font-family: 'Segoe UI';
    font-size: 11px;
    font-weight: 700;
    border-radius: 6px;
    padding: 4px 10px;
}}

QLabel#FrontPageEmpty {{
    color: {C['text_dim']};
    font-family: 'Segoe UI';
    font-size: 13px;
    padding: 24px;
}}

QScrollArea#FrontPageScroll, QScrollArea#BrowserScroll {{
    background-color: {C['bg_root']};
    border: none;
}}

QWidget#FrontPageContainer {{
    background-color: {C['bg_root']};
}}

/* ===== SCRIPT CARD ===== */
QFrame#ScriptCard {{
    background-color: {C['bg_card']};
    border: 1px solid {C['border_card']};
    border-radius: 10px;
}}

QFrame#ScriptCard:hover {{
    background-color: {C['bg_card_hover']};
    border-color: {C['accent_dim']};
}}

QLabel#CardIcon {{
    font-size: 28px;
    background-color: {C['bg_badge']};
    border-radius: 10px;
}}

QLabel#CardName {{
    color: {C['text_primary']};
    font-family: 'Segoe UI';
    font-size: 14px;
    font-weight: 700;
}}

QLabel#CardVersion {{
    color: {C['text_dim']};
    font-family: 'Segoe UI';
    font-size: 11px;
}}

QLabel#CardDescription {{
    color: {C['text_muted']};
    font-family: 'Segoe UI';
    font-size: 12px;
}}

QLabel#CardAuthor {{
    color: {C['text_dim']};
    font-family: 'Segoe UI';
    font-size: 11px;
}}

QLabel#CardTag {{
    color: {C['accent']};
    background-color: {C['bg_badge']};
    font-family: 'Segoe UI';
    font-size: 10px;
    font-weight: 600;
    border-radius: 4px;
    padding: 2px 8px;
}}

QLabel#CardBadgeActive {{
    color: {C['success']};
    background-color: {C['success_dim']};
    font-family: 'Segoe UI';
    font-size: 10px;
    font-weight: 700;
    border-radius: 4px;
    padding: 2px 10px;
}}

QLabel#CardBadgeDisabled {{
    color: {C['text_dim']};
    background-color: {C['bg_surface']};
    font-family: 'Segoe UI';
    font-size: 10px;
    font-weight: 700;
    border-radius: 4px;
    padding: 2px 10px;
}}

QPushButton#CardRunButton {{
    background-color: {C['accent']};
    color: {C['bg_root']};
    border: none;
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 11px;
    font-weight: 700;
    padding: 5px 0;
}}

QPushButton#CardRunButton:hover {{
    background-color: {C['accent_hover']};
    padding: 5px 2px;
}}

QPushButton#CardRunButton:pressed {{
    background-color: {C['accent_dim']};
    padding: 5px 0;
}}

QPushButton#CardConfigButton {{
    background-color: {C['bg_surface']};
    color: {C['text_secondary']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 11px;
    font-weight: 600;
    padding: 5px 0;
}}

QPushButton#CardConfigButton:hover {{
    background-color: {C['bg_hover']};
    border-color: {C['border_light']};
}}

QPushButton#CardToggleButton {{
    background-color: transparent;
    color: {C['text_dim']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 10px;
    padding: 4px 0;
}}

QPushButton#CardToggleButton:hover {{
    background-color: {C['bg_hover']};
    color: {C['text_secondary']};
}}

/* ===== STAT CARDS ===== */
QFrame#StatCard {{
    background-color: {C['bg_card']};
    border: 1px solid {C['border_card']};
    border-radius: 10px;
}}

QLabel#StatValue {{
    color: {C['accent']};
    font-family: 'Segoe UI';
    font-size: 22px;
    font-weight: 700;
}}

QLabel#StatLabel {{
    color: {C['text_dim']};
    font-family: 'Segoe UI';
    font-size: 11px;
    font-weight: 600;
}}

/* ===== SCRIPT CREATOR / DIALOG ===== */
QDialog#ScriptCreatorDialog {{
    background-color: {C['bg_dialog']};
}}

QLabel#DialogTitle {{
    color: {C['text_primary']};
    font-family: 'Segoe UI';
    font-size: 16px;
    font-weight: 700;
}}

QFrame#IconPicker {{
    background-color: {C['bg_surface']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    padding: 4px;
}}

QPushButton#IconPickerButton {{
    background-color: transparent;
    border: 2px solid transparent;
    border-radius: 6px;
    font-size: 18px;
}}

QPushButton#IconPickerButton:hover {{
    background-color: {C['bg_hover']};
}}

QPushButton#IconPickerButton:checked {{
    background-color: {C['bg_selected']};
    border-color: {C['accent']};
}}

QTextEdit#DescriptionInput {{
    background-color: {C['bg_input']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 12px;
    padding: 6px 10px;
}}

QTextEdit#DescriptionInput:focus {{
    border-color: {C['accent']};
}}
"""
