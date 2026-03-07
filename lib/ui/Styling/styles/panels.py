"""Panel styles — console, script browser, runner, settings, jobs, inspector,
docs, webhook, snippets, packages, theme creator, world inspector."""

from ...Colors.palette import COLORS


def get_panel_styles() -> str:
    C = COLORS
    return f"""

/* ===== PANEL TITLES ===== */
QLabel#PanelTitle {{
    color: {C['text_primary']};
    font-family: 'Segoe UI';
    font-size: 13px;
    font-weight: 700;
}}

QLabel#SectionLabel {{
    color: {C['text_muted']};
    font-family: 'Segoe UI';
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
}}

QLabel#FieldLabel {{
    color: {C['text_secondary']};
    font-family: 'Segoe UI';
    font-size: 12px;
}}

/* ===== SCRIPT BROWSER ===== */
QFrame#ScriptBrowser {{
    background-color: {C['bg_root']};
    border: none;
}}

QFrame#BrowserHeader, QFrame#RunnerHeader, QFrame#ConsoleHeader,
QFrame#SettingsHeader, QFrame#PackagesHeader {{
    background-color: {C['bg_topbar']};
    border-bottom: 1px solid {C['border']};
}}

QFrame#FilterBar {{
    background-color: {C['bg_surface']};
    border-bottom: 1px solid {C['border']};
}}

QLineEdit#SearchInput {{
    background-color: {C['bg_input']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 12px;
    padding: 4px 10px;
    selection-background-color: {C['accent_dim']};
}}

QLineEdit#SearchInput:focus {{
    border-color: {C['accent']};
}}

QComboBox#SortCombo, QComboBox#ScriptCombo {{
    background-color: {C['bg_input']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 12px;
    padding: 4px 10px;
    min-width: 120px;
}}

QComboBox#SortCombo:hover, QComboBox#ScriptCombo:hover {{
    border-color: {C['accent_dim']};
}}

QComboBox#SortCombo::drop-down, QComboBox#ScriptCombo::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {C['bg_surface']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    selection-background-color: {C['bg_selected']};
    outline: none;
}}

QListWidget#ScriptList, QListWidget#HistoryList, QListWidget#PackageList {{
    background-color: {C['bg_root']};
    color: {C['text_secondary']};
    border: none;
    font-family: 'Segoe UI';
    font-size: 12px;
    outline: none;
    padding: 2px;
}}

QListWidget#ScriptList::item, QListWidget#HistoryList::item, QListWidget#PackageList::item {{
    padding: 6px 8px;
    border-radius: 4px;
    margin: 1px 4px;
}}

QListWidget#ScriptList::item:hover, QListWidget#HistoryList::item:hover {{
    background-color: {C['bg_hover']};
    color: {C['text_primary']};
}}

QListWidget#ScriptList::item:selected, QListWidget#HistoryList::item:selected {{
    background-color: {C['bg_selected']};
    color: {C['accent']};
    border-left: 2px solid {C['accent']};
}}

QLabel#BrowserInfo {{
    color: {C['text_dim']};
    font-family: 'Segoe UI';
    font-size: 11px;
}}

/* ===== CONSOLE ===== */
QFrame#ConsolePanel {{
    background-color: {C['bg_console']};
    border: none;
}}

QLabel#ConsoleStatus {{
    color: {C['text_muted']};
    font-family: 'Segoe UI';
    font-size: 11px;
}}

QPlainTextEdit#ConsoleOutput {{
    background-color: {C['bg_console']};
    color: {C['text_secondary']};
    border: none;
    font-family: 'Consolas';
    font-size: 12px;
    selection-background-color: {C['bg_selected']};
}}

QFrame#ConsoleInputBar {{
    background-color: {C['bg_surface']};
    border-top: 1px solid {C['border']};
}}

QLabel#ConsolePrompt {{
    color: {C['accent']};
    font-family: 'Consolas';
    font-size: 13px;
    font-weight: 700;
}}

QLineEdit#ConsoleInput {{
    background-color: {C['bg_input']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 5px;
    font-family: 'Consolas';
    font-size: 12px;
    padding: 3px 8px;
}}

QLineEdit#ConsoleInput:focus {{
    border-color: {C['accent']};
}}

/* ===== SCRIPT RUNNER ===== */
QFrame#ScriptRunner {{
    background-color: {C['bg_root']};
    border: none;
}}

QFrame#RunnerSelector {{
    background-color: {C['bg_surface']};
    border-bottom: 1px solid {C['border']};
}}

QFrame#QuickActions {{
    background-color: {C['bg_surface']};
    border-top: 1px solid {C['border']};
}}

/* ===== SETTINGS PANEL ===== */
QFrame#SettingsPanel {{
    background-color: {C['bg_root']};
    border: none;
}}

QScrollArea#SettingsScroll {{
    background-color: {C['bg_root']};
    border: none;
}}

QWidget#SettingsBody {{
    background-color: {C['bg_root']};
}}

QLabel#SettingsSection {{
    color: {C['accent']};
    font-family: 'Segoe UI';
    font-size: 13px;
    font-weight: 700;
    padding-top: 4px;
    padding-bottom: 4px;
    border-bottom: 1px solid {C['border']};
}}

QLabel#SettingsLabel {{
    color: {C['text_secondary']};
    font-family: 'Segoe UI';
    font-size: 12px;
}}

QLineEdit#SettingsInput {{
    background-color: {C['bg_input']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 12px;
    padding: 4px 10px;
}}

QLineEdit#SettingsInput:focus {{
    border-color: {C['accent']};
}}

QSpinBox#SettingsSpinBox {{
    background-color: {C['bg_input']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 12px;
    padding: 3px 8px;
    min-width: 80px;
}}

QSpinBox#SettingsSpinBox:hover {{
    border-color: {C['accent_dim']};
}}

QSpinBox#SettingsSpinBox:focus {{
    border-color: {C['accent']};
}}

QCheckBox#SettingsCheck {{
    color: {C['text_secondary']};
    font-family: 'Segoe UI';
    font-size: 12px;
    spacing: 8px;
    padding: 4px 0;
}}

QCheckBox#SettingsCheck::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {C['border']};
    border-radius: 4px;
    background-color: {C['bg_input']};
}}

QCheckBox#SettingsCheck::indicator:hover {{
    border-color: {C['accent_dim']};
}}

QCheckBox#SettingsCheck::indicator:checked {{
    background-color: {C['accent']};
    border-color: {C['accent']};
}}

QCheckBox#SettingsCheck::indicator:checked:hover {{
    background-color: {C['accent_hover']};
    border-color: {C['accent_hover']};
}}

/* ===== PACKAGES PANEL ===== */
QFrame#PackagesPanel {{
    background-color: {C['bg_root']};
    border: none;
}}

/* ===== JOBS PANEL ===== */
QFrame#JobsPanel {{
    background-color: {C['bg_panel']};
}}

QLabel#JobsTitle {{
    color: {C['text_primary']};
    font-family: 'Segoe UI';
    font-size: 20px;
    font-weight: 700;
}}

QLabel#JobsSubtitle {{
    color: {C['text_muted']};
    font-family: 'Segoe UI';
    font-size: 12px;
}}

QPushButton#JobsHeaderBtn {{
    background-color: {C['bg_surface']};
    color: {C['text_secondary']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    font-family: 'Segoe UI';
    font-size: 12px;
    font-weight: 600;
    padding: 5px 14px;
}}

QPushButton#JobsHeaderBtn:hover {{
    background-color: {C['bg_hover']};
    color: {C['text_primary']};
}}

QPushButton#JobsHeaderBtn:pressed {{
    background-color: {C['bg_pressed']};
}}

QTableWidget#JobsTable {{
    background-color: {C['bg_surface']};
    alternate-background-color: {C['bg_card']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px;
    gridline-color: transparent;
    selection-background-color: {C['bg_selected']};
    selection-color: {C['text_primary']};
}}

QTableWidget#JobsTable QHeaderView::section {{
    background-color: {C['bg_topbar']};
    color: {C['text_muted']};
    border: none;
    border-bottom: 1px solid {C['border']};
    font-family: 'Segoe UI';
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    padding: 8px 6px;
}}

QTableWidget#JobsTable::item {{
    padding: 6px 8px;
}}

QLabel#JobsFallback {{
    color: {C['text_dim']};
    font-family: 'Segoe UI';
    font-size: 14px;
    padding: 40px;
}}

QLabel#JobsLegend {{
    color: {C['text_dim']};
    font-family: 'Segoe UI';
    font-size: 11px;
    padding-top: 6px;
}}

/* ===== THEME CREATOR ===== */
QFrame#ThemeCreator {{
    background-color: {C['bg_root']};
}}

QPushButton#ColorSwatch {{
    border: 2px solid {C['border']};
    border-radius: 6px;
    min-width: 40px;
    min-height: 28px;
}}

QPushButton#ColorSwatch:hover {{
    border-color: {C['accent']};
}}

/* ===== SNIPPET LIBRARY ===== */
QFrame#SnippetLibrary {{
    background-color: {C['bg_root']};
}}

/* ===== WORLD INSPECTOR ===== */
QFrame#WorldInspector {{
    background-color: {C['bg_root']};
}}

QTabWidget#InspectorTabs::pane {{
    border: 1px solid {C['border']};
    border-radius: 0 0 8px 8px;
    background-color: {C['bg_root']};
}}

QTabWidget#InspectorTabs > QTabBar::tab {{
    background-color: {C['bg_sidebar']};
    color: {C['text_secondary']};
    border: none;
    font-family: 'Segoe UI';
    font-size: 12px;
    padding: 6px 16px;
}}

QTabWidget#InspectorTabs > QTabBar::tab:hover:!selected {{
    background-color: {C['bg_hover']};
    color: {C['text_primary']};
}}

QTabWidget#InspectorTabs > QTabBar::tab:selected {{
    background-color: {C['bg_root']};
    color: {C['text_primary']};
    border-bottom: 2px solid {C['accent']};
}}

QLabel#InspectorResult {{
    color: {C['accent']};
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 13px;
    padding: 8px;
    background-color: {C['bg_surface']};
    border: 1px solid {C['border']};
    border-radius: 6px;
}}

/* ===== DOCS PANEL ===== */
QFrame#DocsPanel {{
    background-color: {C['bg_root']};
}}

QFrame#DocsHeader {{
    background-color: {C['bg_surface']};
    border-bottom: 1px solid {C['border']};
}}

QFrame#DocsSearchBar {{
    background-color: {C['bg_surface']};
    border-bottom: 1px solid {C['border']};
}}

QLineEdit#DocsSearch {{
    background-color: {C['bg_root']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
}}

QLineEdit#DocsSearch:focus {{
    border: 1px solid {C['accent']};
}}

QListWidget#DocsCategoryList, QListWidget#DocsFuncList {{
    background-color: {C['bg_root']};
    color: {C['text_primary']};
    border: none;
    font-size: 12px;
    padding: 2px;
}}

QListWidget#DocsCategoryList::item, QListWidget#DocsFuncList::item {{
    padding: 4px 8px;
    border-radius: 4px;
}}

QListWidget#DocsCategoryList::item:selected, QListWidget#DocsFuncList::item:selected {{
    background-color: {C['accent']};
    color: #fff;
}}

QListWidget#DocsCategoryList::item:hover, QListWidget#DocsFuncList::item:hover {{
    background-color: {C['bg_hover']};
}}

QTextEdit#DocsDetail {{
    background-color: {C['bg_root']};
    color: {C['text_primary']};
    border: none;
    border-left: 1px solid {C['border']};
    padding: 8px;
}}

/* ===== WEBHOOK PANEL ===== */
QFrame#WebhookPanel {{
    background-color: {C['bg_root']};
}}

QFrame#WebhookHeader {{
    background-color: {C['bg_surface']};
    border-bottom: 1px solid {C['border']};
}}

QPlainTextEdit#WebhookCustomMsg {{
    background-color: {C['bg_root']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    padding: 6px;
    font-size: 12px;
}}

QPlainTextEdit#WebhookCustomMsg:focus {{
    border: 1px solid {C['accent']};
}}
"""
