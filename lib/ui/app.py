"""
Fluxus — Minecraft scripting IDE.
Main application window with all panels wired together.
"""

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QSplitter,
    QStackedWidget, QVBoxLayout, QWidget,
)

from .Components.animations import (
    AnimatedStackedWidget, window_open_animation, window_close_animation,
    fade_in, DURATION_SMOOTH,
)

from .Components.top_bar import TopBar
from .Components.sidebar import Sidebar
from .Components.sub_nav import SubNavPage
from .Components.front_page import FrontPage
from .Components.code_editor import CodeEditor
from .Components.script_browser import ScriptBrowser
from .Components.script_creator import ScriptCreatorDialog
from .Components.script_runner import ScriptRunner
from .Components.console import ConsolePanel
from .Components.jobs_panel import JobsPanel
from .Components.packages_panel import PackagesPanel
from .Components.settings_panel import SettingsPanel, load_settings, save_settings
from .Components.status_bar import StatusBar
from .Components.theme_creator import ThemeCreator
from .Components.toast import ToastManager
from .Components.shortcuts import ShortcutManager
from .Components.command_palette import CommandPalette
from .Components.find_replace import FindReplaceBar
from .Components.snippet_library import SnippetLibrary
from .Components.world_inspector import WorldInspector
from .Components.session import save_session, load_session
from .Components.script_templates import list_templates, get_template
from .Components.docs_panel import DocsPanel
from .Components.discord_webhook import DiscordWebhookPanel, get_webhook_sender
from .Components.splash_screen import SplashScreen
from .Components.plugins_panel import PluginsPanel
from .Components.script_store import PluginStorePanel
from .Components.script_params import ScriptParametersDialog, parse_params, create_injected_script
from .Components.script_gui import has_gui, parse_gui, create_gui_script
from .Components import script_io, script_manifest as manifest
from .Components.mc_reference import MCReferencePanel
from .Components.file_tree import FileTreePanel
from .Components.todo_panel import TodoPanel
from .Components.git_panel import GitPanel
from .Components.keybinding_editor import KeybindingEditor
from .Components.backup_manager import BackupManager
from .Colors.palette import COLORS, apply_theme
from .Styling.stylesheet import get_app_stylesheet
from .Styling.theme import WINDOW_GEOMETRY, WINDOW_MIN_SIZE, WINDOW_TITLE

_MINESCRIPT_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR = _MINESCRIPT_ROOT / "Scripts"
_SCRIPTS_DIR.mkdir(exist_ok=True)


class FluxusWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("FluxusWindow")
        self.setAcceptDrops(True)  # drag-and-drop support
        self._configure_window()
        self._build_layout()
        self._setup_toast()
        self._setup_shortcuts()
        self._connect_signals()
        self._restore_session()

    # ── Window setup ───────────────────────────────────────────────
    def _configure_window(self) -> None:
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setMinimumSize(*WINDOW_MIN_SIZE)
        self._apply_geometry()
        self.setWindowIcon(QIcon())
        self.setStyleSheet(get_app_stylesheet())

    def _apply_geometry(self) -> None:
        size_part, pos_part = WINDOW_GEOMETRY.split("+", 1)
        width, height = size_part.split("x")
        x_pos, y_pos = pos_part.split("+")
        self.setGeometry(int(x_pos), int(y_pos), int(width), int(height))

    # ── Build UI ───────────────────────────────────────────────────
    def _build_layout(self) -> None:
        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setLayout(root_layout)

        # Top bar
        self.top_bar = TopBar(self)
        root_layout.addWidget(self.top_bar)

        # Main body: sidebar + content area
        body = QWidget(self)
        body.setObjectName("MainBody")
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body.setLayout(body_layout)

        self.sidebar = Sidebar(body)
        body_layout.addWidget(self.sidebar)

        # ── Stacked pages ──────────────────────────────────────────
        self._pages = AnimatedStackedWidget(body)
        self._pages.setObjectName("PageStack")

        # [0] Front Page / Home (standalone)
        self.front_page = FrontPage(str(_SCRIPTS_DIR))
        self._pages.addWidget(self.front_page)

        # ── Develop sub-nav [1] ────────────────────────────────────
        self.develop_page = SubNavPage()

        # Editor pane (splitter: editor + console)
        editor_page = QWidget()
        editor_page.setObjectName("EditorPage")
        ep_layout = QVBoxLayout()
        ep_layout.setContentsMargins(0, 0, 0, 0)
        ep_layout.setSpacing(0)
        editor_page.setLayout(ep_layout)

        editor_splitter = QSplitter(Qt.Vertical)
        editor_splitter.setObjectName("EditorSplitter")

        self.code_editor = CodeEditor()
        editor_splitter.addWidget(self.code_editor)

        self.console = ConsolePanel(minescript_root=str(_MINESCRIPT_ROOT))
        editor_splitter.addWidget(self.console)

        editor_splitter.setSizes([500, 200])
        editor_splitter.setStretchFactor(0, 3)
        editor_splitter.setStretchFactor(1, 1)
        ep_layout.addWidget(editor_splitter)

        # Find/Replace bar (below splitter)
        self.find_replace = FindReplaceBar()
        self.find_replace.hide()
        ep_layout.addWidget(self.find_replace)

        self.develop_page.add_sub_page("📝", "Editor", "editor", editor_page)

        # Scripts browser
        self.script_browser = ScriptBrowser(str(_SCRIPTS_DIR))
        self.develop_page.add_sub_page("📁", "Scripts", "scripts", self.script_browser)

        # Snippet Library
        self.snippet_library = SnippetLibrary()
        self.develop_page.add_sub_page("📎", "Snippets", "snippets", self.snippet_library)

        # Docs panel
        self.docs_panel = DocsPanel()
        self.develop_page.add_sub_page("📖", "Docs", "docs", self.docs_panel)

        # File explorer
        self.file_tree = FileTreePanel(str(_SCRIPTS_DIR))
        self.develop_page.add_sub_page("📂", "Files", "files", self.file_tree)

        self.develop_page.finalize()
        self._pages.addWidget(self.develop_page)  # index 1

        # ── Execute sub-nav [2] ────────────────────────────────────
        self.execute_page = SubNavPage()

        self.script_runner = ScriptRunner(str(_SCRIPTS_DIR))
        self.execute_page.add_sub_page("▶", "Runner", "runner", self.script_runner)

        self.console_standalone = ConsolePanel(minescript_root=str(_MINESCRIPT_ROOT))
        self.execute_page.add_sub_page("📋", "Console", "console", self.console_standalone)

        self.jobs_panel = JobsPanel()
        self.execute_page.add_sub_page("⚡", "Jobs", "jobs", self.jobs_panel)

        self.execute_page.finalize()
        self._pages.addWidget(self.execute_page)  # index 2

        # ── Tools sub-nav [3] ─────────────────────────────────────
        self.tools_page = SubNavPage()

        self.world_inspector = WorldInspector()
        self.tools_page.add_sub_page("🔍", "Inspector", "inspector", self.world_inspector)

        self.packages_panel = PackagesPanel(str(_MINESCRIPT_ROOT))
        self.tools_page.add_sub_page("📦", "Packages", "packages", self.packages_panel)

        self.plugins_panel = PluginsPanel()
        self.tools_page.add_sub_page("🔌", "Plugins", "plugins", self.plugins_panel)

        # MC Reference
        self.mc_reference = MCReferencePanel()
        self.tools_page.add_sub_page("📚", "Reference", "reference", self.mc_reference)

        # TODO scanner
        self.todo_panel = TodoPanel(str(_SCRIPTS_DIR))
        self.tools_page.add_sub_page("📌", "TODOs", "todos", self.todo_panel)

        # Git panel
        self.git_panel = GitPanel(str(_MINESCRIPT_ROOT))
        self.tools_page.add_sub_page("🔀", "Git", "git", self.git_panel)

        self.tools_page.finalize()
        self._pages.addWidget(self.tools_page)  # index 3

        # ── Store sub-nav [4] ──────────────────────────────────────────
        self.store_page = SubNavPage()

        self.plugin_store = PluginStorePanel()
        self.store_page.add_sub_page("🏪", "Plugin Store", "plugin_store", self.plugin_store)

        self.script_store = PluginStorePanel(
            plugins_dir=str(_SCRIPTS_DIR),
            title="Script Store",
            search_hint="Search scripts…",
        )
        self.store_page.add_sub_page("📥", "Script Store", "script_store", self.script_store)

        self.store_page.finalize()
        self._pages.addWidget(self.store_page)  # index 4

        # ── Configure sub-nav [5] ───────────────────────────────────────
        self.configure_page = SubNavPage()

        self.theme_creator = ThemeCreator()
        self.configure_page.add_sub_page("🎨", "Themes", "themes", self.theme_creator)

        self.webhook_panel = DiscordWebhookPanel()
        self.configure_page.add_sub_page("🔔", "Webhook", "webhook", self.webhook_panel)

        self.settings_panel = SettingsPanel()
        self.configure_page.add_sub_page("⚙", "Settings", "settings", self.settings_panel)

        # Keybinding editor
        self.keybinding_editor = KeybindingEditor()
        self.configure_page.add_sub_page("⌨", "Shortcuts", "shortcuts_editor", self.keybinding_editor)

        # Backup manager
        self.backup_manager = BackupManager(str(_MINESCRIPT_ROOT))
        self.configure_page.add_sub_page("💾", "Backups", "backups", self.backup_manager)

        self.configure_page.finalize()
        self._pages.addWidget(self.configure_page)  # index 5

        body_layout.addWidget(self._pages, 1)
        root_layout.addWidget(body, 1)

        # Status bar
        self.status_bar = StatusBar(self)
        root_layout.addWidget(self.status_bar)

    # ── Toast manager ─────────────────────────────────────────────
    def _setup_toast(self) -> None:
        self.toast = ToastManager(self)

    # ── Keyboard shortcuts ─────────────────────────────────────────
    def _setup_shortcuts(self) -> None:
        self.shortcut_mgr = ShortcutManager(self)

        actions = {
            "new_file":       lambda: self.code_editor.new_file(),
            "open_file":      lambda: self.code_editor.open_file(),
            "save_file":      lambda: self.code_editor.save_file(),
            "save_file_as":   lambda: self.code_editor.save_file_as(),
            "close_tab":      lambda: self._close_current_tab(),
            "next_tab":       lambda: self._cycle_tab(1),
            "prev_tab":       lambda: self._cycle_tab(-1),
            "find":           lambda: self._toggle_find(),
            "replace":        lambda: self._toggle_replace(),
            "run_script":     lambda: self._run_current(),
            "command_palette": lambda: self._show_palette(),
            "toggle_sidebar":  lambda: self.sidebar.toggle_collapse(),
            "goto_home":      lambda: self._goto_page("home"),
            "goto_editor":    lambda: self._goto_page("editor"),
            "goto_scripts":   lambda: self._goto_page("scripts"),
            "goto_runner":    lambda: self._goto_page("runner"),
            "goto_console":   lambda: self._goto_page("console"),
            "goto_jobs":      lambda: self._goto_page("jobs"),
            "goto_inspector": lambda: self._goto_page("inspector"),
            "goto_snippets":  lambda: self._goto_page("snippets"),
            "goto_settings":  lambda: self._goto_page("settings"),
            "import_scripts": lambda: self._import_scripts(),
            "export_script":  lambda: self._export_script(),
        }
        for action, callback in actions.items():
            self.shortcut_mgr.register(action, callback)

        # Install as QShortcuts
        for action, key in self.shortcut_mgr.get_bindings().items():
            try:
                sc = QShortcut(QKeySequence(key), self)
                cb = actions.get(action)
                if cb:
                    sc.activated.connect(cb)
            except Exception:
                pass

    # ── Signal wiring ──────────────────────────────────────────────
    def _connect_signals(self) -> None:
        # Sidebar → main page stack.  Sub-nav tabs handled by SubNavPage.
        page_map = {
            "home": 0, "develop": 1, "execute": 2, "tools": 3, "store": 4, "configure": 5,
        }
        # Sub-page routing: sidebar tag → (main index, sub-nav tag or None)
        sub_page_route = {
            "home":       (0, None),
            "develop":    (1, None),
            "execute":    (2, None),
            "tools":      (3, None),
            "store":      (4, None),
            "configure":  (5, None),
            # Direct deep links from shortcuts / command palette
            "editor":     (1, "editor"),
            "scripts":    (1, "scripts"),
            "snippets":   (1, "snippets"),
            "docs":       (1, "docs"),
            "files":      (1, "files"),
            "runner":     (2, "runner"),
            "console":    (2, "console"),
            "jobs":       (2, "jobs"),
            "inspector":  (3, "inspector"),
            "packages":   (3, "packages"),
            "plugins":    (3, "plugins"),
            "reference":  (3, "reference"),
            "todos":      (3, "todos"),
            "git":        (3, "git"),
            "plugin_store": (4, "plugin_store"),
            "script_store": (4, "script_store"),
            "themes":     (5, "themes"),
            "webhook":    (5, "webhook"),
            "settings":   (5, "settings"),
            "shortcuts_editor": (5, "shortcuts_editor"),
            "backups":    (5, "backups"),
        }
        page_labels = {
            "home": "Home", "develop": "Develop", "execute": "Execute",
            "tools": "Tools", "store": "Store", "configure": "Configure",
            "editor": "Editor", "scripts": "Scripts", "snippets": "Snippets",
            "docs": "Docs", "files": "Files", "runner": "Runner",
            "console": "Console", "jobs": "Jobs", "inspector": "Inspector",
            "packages": "Packages", "plugins": "Plugins", "reference": "Reference",
            "todos": "TODOs", "git": "Git",
            "plugin_store": "Plugin Store", "script_store": "Script Store",
            "themes": "Themes", "webhook": "Webhook", "settings": "Settings",
            "shortcuts_editor": "Shortcuts", "backups": "Backups",
        }

        def switch_page(tag: str):
            route = sub_page_route.get(tag)
            if not route:
                return
            main_idx, sub_tag = route
            self._pages.setCurrentIndex(main_idx)
            self.status_bar.set_page(page_labels.get(sub_tag or tag, tag))
            # Switch sub-tab if applicable
            if sub_tag:
                sub_nav = self._pages.widget(main_idx)
                if hasattr(sub_nav, "select_sub_page"):
                    sub_nav.select_sub_page(sub_tag)
            # Refresh hooks
            if tag == "home":
                self.front_page.refresh()
            elif tag in ("scripts", "develop"):
                self.script_browser.refresh()
            elif tag in ("jobs", "execute"):
                self.jobs_panel.refresh()
            elif tag in ("inspector", "tools"):
                self.world_inspector.refresh()
            elif tag == "plugins":
                self.plugins_panel.refresh()
            elif tag == "reference":
                pass  # static data
            elif tag == "todos":
                self.todo_panel.scan()
            elif tag == "git":
                self.git_panel.refresh()
            elif tag == "files":
                self.file_tree.refresh()
            elif tag == "backups":
                self.backup_manager.refresh()
            elif tag == "plugin_store":
                if not self.plugin_store._all_scripts:
                    self.plugin_store.fetch_scripts()
            elif tag == "script_store":
                if not self.script_store._all_scripts:
                    self.script_store.fetch_scripts()

        self.sidebar.page_changed.connect(switch_page)

        # ── Open in editor ─────────────────────────────────────────
        def open_in_editor(path: str):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.code_editor.set_content(f.read(), path)
                self._goto_page("editor")
                self.status_bar.set_script(os.path.basename(path))
            except Exception:
                self.toast.error(f"Failed to open {os.path.basename(path)}")

        # ── Run helper ─────────────────────────────────────────────
        def run_script(path: str):
            actual_path = path
            # If the script has @ui.* or @param annotations and isn't
            # already an injected temp file, prepend saved/default values.
            if not os.path.basename(path).startswith("_fluxus_"):
                try:
                    code = Path(path).read_text(encoding="utf-8")
                    meta = manifest.get_meta(path)
                    saved = meta.get("params", {})

                    if has_gui(code):
                        # @ui.* style annotations
                        gui_defs = parse_gui(code)
                        values = {}
                        for d in gui_defs:
                            if d.name and d.kind not in ("title", "page", "label",
                                                          "separator", "button"):
                                values[d.name] = d.default
                        values.update(saved)
                        if values:
                            actual_path = create_gui_script(path, values)
                    else:
                        # @param style annotations
                        param_defs = parse_params(code)
                        if param_defs:
                            values = {}
                            for p in param_defs:
                                if p.kind != "header" and p.name:
                                    values[p.name] = p.default
                            values.update(saved)
                            if values:
                                actual_path = create_injected_script(path, values)
                except Exception:
                    pass  # fall through and run the original script
            method = load_settings().get("execution_method", "minescript")
            self.console.run_script(actual_path, execution_method=method)
            self._goto_page("editor")
            self.status_bar.set_status("Running…")
            self.toast.info(f"Running {os.path.basename(path)}")
            get_webhook_sender().on_script_run(os.path.basename(path))

        # ── Configure helper (now opens Parameters dialog) ──────────────
        def configure_script(path: str):
            meta = manifest.get_meta(path)
            saved_params = meta.get("params", {})
            dlg = ScriptParametersDialog(path, saved_values=saved_params, parent=self)
            dlg.params_saved.connect(lambda vals: _save_script_params(path, vals))
            dlg.run_with_params.connect(run_script)
            dlg.exec()

        def _save_script_params(path: str, values: dict):
            meta = manifest.get_meta(path)
            meta["params"] = values
            manifest.set_meta(path, meta)
            self.toast.success("Parameters saved")

        # Front Page
        self.front_page.run_requested.connect(run_script)
        self.front_page.edit_requested.connect(open_in_editor)
        self.front_page.configure_requested.connect(configure_script)
        self.front_page.create_requested.connect(lambda: self._open_creator())

        # Script Browser
        self.script_browser.script_selected.connect(open_in_editor)
        self.script_browser.run_requested.connect(run_script)
        self.script_browser.configure_requested.connect(configure_script)
        self.script_browser.delete_requested.connect(
            lambda p: (
                self.front_page.refresh(),
                self.toast.info(f"Script deleted"),
            )
        )

        # Script Runner
        self.script_runner.run_requested.connect(run_script)
        self.script_runner.open_requested.connect(open_in_editor)

        # Inline params from editor tabs
        def connect_tab_params(tab):
            tab.params_panel.params_changed.connect(lambda vals: _save_script_params(tab.filepath or "", vals))
            tab.params_panel.run_with_params.connect(run_script)
            # GUI panel signals
            tab.gui_panel.values_changed.connect(lambda vals: _save_script_params(tab.filepath or "", vals))
            tab.gui_panel.run_with_gui.connect(run_script)
            tab.gui_panel.button_clicked.connect(
                lambda fn_name: self.toast.info(f"Button '{fn_name}' — run the script to execute")
            )

        # Hook into editor tab creation
        orig_add_tab = self.code_editor._add_tab
        def patched_add_tab(filepath):
            tab = orig_add_tab(filepath)
            connect_tab_params(tab)
            return tab
        self.code_editor._add_tab = patched_add_tab

        # Connect existing tabs
        for t in self.code_editor._tabs_data:
            connect_tab_params(t)

        # Console finished
        def on_console_finished(code):
            self.status_bar.set_status("Ready")
            path = self.code_editor.get_current_file()
            script_name = os.path.basename(path) if path else "unknown"
            if path:
                self.script_runner.add_history_entry(path, code)
            if code == 0:
                self.toast.success("Script finished successfully")
            else:
                self.toast.warning(f"Script exited with code {code}")
            get_webhook_sender().on_script_finish(script_name, code)

        self.console._signals.process_finished.connect(on_console_finished)

        # Theme changes from settings
        self.settings_panel.theme_changed.connect(self._apply_theme)
        self.settings_panel.settings_changed.connect(lambda _: self.toast.success("Settings saved"))

        # Theme creator live apply
        self.theme_creator.theme_applied.connect(lambda name: (
            self.setStyleSheet(get_app_stylesheet()),
            self.toast.info(f"Theme '{name}' applied"),
        ))

        # Snippet insert → editor
        self.snippet_library.insert_requested.connect(self.code_editor.insert_text)

        # Docs insert → editor
        self.docs_panel.insert_requested.connect(self.code_editor.insert_text)

        # Webhook settings changed
        self.webhook_panel.settings_changed.connect(
            lambda _: self.toast.success("Webhook settings saved")
        )

        # Find/Replace → editor
        self.find_replace.close_requested.connect(self.find_replace.hide)

        # Editor file events
        self.code_editor.file_saved.connect(
            lambda p: (
                self.toast.success(f"Saved {os.path.basename(p)}"),
                get_webhook_sender().on_save(p),
            )
        )

        # Editor Run button → run_script helper
        self.code_editor.run_requested.connect(run_script)

        # Plugin Store → refresh on install / delete
        self.plugin_store.plugin_installed.connect(
            lambda title: (
                self.plugins_panel.refresh(),
                self.toast.success(f"Installed '{title}' from Plugin Store"),
            )
        )
        self.plugin_store.plugin_deleted.connect(
            lambda title: (
                self.plugins_panel.refresh(),
                self.toast.info(f"Plugin '{title}' deleted"),
            )
        )

        # Script Store → refresh on install / delete
        self.script_store.plugin_installed.connect(
            lambda title: (
                self.script_browser.refresh(),
                self.front_page.refresh(),
                self.toast.success(f"Installed script '{title}'"),
            )
        )
        self.script_store.plugin_deleted.connect(
            lambda title: (
                self.script_browser.refresh(),
                self.front_page.refresh(),
                self.toast.info(f"Script '{title}' deleted"),
            )
        )

        # Plugins panel → notify
        self.plugins_panel.plugins_changed.connect(
            lambda: self.toast.info("Plugin settings updated")
        )

        # ── New component signal wiring ────────────────────────────

        # File tree → open in editor
        self.file_tree.file_selected.connect(open_in_editor)
        self.file_tree.file_renamed.connect(
            lambda old, new: self.toast.info(f"Renamed → {os.path.basename(new)}")
        )
        self.file_tree.file_deleted.connect(
            lambda p: (
                self.script_browser.refresh(),
                self.front_page.refresh(),
                self.toast.info(f"Deleted {os.path.basename(p)}"),
            )
        )
        self.file_tree.file_created.connect(
            lambda p: (
                self.script_browser.refresh(),
                self.toast.success(f"Created {os.path.basename(p)}"),
            )
        )

        # TODO panel → navigate to file + line
        def on_todo_navigate(filepath, line):
            open_in_editor(filepath)
            # Jump to line
            editor = self.code_editor.get_editor()
            if editor:
                cursor = editor.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                for _ in range(line - 1):
                    cursor.movePosition(cursor.MoveOperation.Down)
                editor.setTextCursor(cursor)
                editor.centerCursor()

        self.todo_panel.navigate_requested.connect(on_todo_navigate)

        # MC Reference → copy to clipboard
        self.mc_reference.copy_requested.connect(
            lambda text: (
                QApplication.clipboard().setText(text),
                self.toast.info(f"Copied: {text[:40]}"),
            )
        )

        # Keybinding editor → update bindings
        self.keybinding_editor.bindings_changed.connect(
            lambda bindings: self.toast.success("Keyboard shortcuts updated")
        )

        # Backup manager → restore notification
        self.backup_manager.backup_restored.connect(
            lambda: (
                self.script_browser.refresh(),
                self.front_page.refresh(),
                self.toast.success("Backup restored successfully"),
            )
        )

        # Editor zen mode → hide/show sidebar + top_bar + status_bar
        self.code_editor.zen_mode_toggled.connect(self._toggle_zen_mode)

    # ── Zen mode ───────────────────────────────────────────────────
    def _toggle_zen_mode(self, enabled: bool) -> None:
        """Hide/show sidebar, top bar, and status bar for distraction-free editing."""
        self.sidebar.setVisible(not enabled)
        self.top_bar.setVisible(not enabled)
        self.status_bar.setVisible(not enabled)

    # ── Page navigation helpers ────────────────────────────────────
    def _goto_page(self, tag: str) -> None:
        """Navigate to a page, including deep sub-page tags like 'editor', 'settings'."""
        # Map sub-pages to their parent sidebar tag for the highlight
        sidebar_map = {
            "editor": "develop", "scripts": "develop", "snippets": "develop",
            "docs": "develop", "files": "develop",
            "runner": "execute", "console": "execute", "jobs": "execute",
            "inspector": "tools", "packages": "tools",
            "plugins": "tools", "reference": "tools", "todos": "tools", "git": "tools",
            "plugin_store": "store", "script_store": "store",
            "themes": "configure", "webhook": "configure", "settings": "configure",
            "shortcuts_editor": "configure", "backups": "configure",
        }
        sidebar_tag = sidebar_map.get(tag, tag)
        self.sidebar.select(sidebar_tag)
        self.sidebar.page_changed.emit(tag)

    # ── Tab helpers ────────────────────────────────────────────────
    def _close_current_tab(self) -> None:
        tw = self.code_editor._tab_widget
        if tw.count() > 1:
            tw.removeTab(tw.currentIndex())

    def _cycle_tab(self, direction: int) -> None:
        tw = self.code_editor._tab_widget
        new_idx = (tw.currentIndex() + direction) % max(tw.count(), 1)
        tw.setCurrentIndex(new_idx)

    # ── Find/Replace ──────────────────────────────────────────────
    def _toggle_find(self) -> None:
        editor = self.code_editor.get_editor()
        if editor:
            self.find_replace.set_editor(editor)
        if self.find_replace.isVisible():
            self.find_replace.hide()
        else:
            self.find_replace.show()
            self.find_replace.open_find()

    def _toggle_replace(self) -> None:
        editor = self.code_editor.get_editor()
        if editor:
            self.find_replace.set_editor(editor)
        self.find_replace.show()
        self.find_replace.open_replace()

    # ── Run current script ─────────────────────────────────────────
    def _run_current(self) -> None:
        path = self.code_editor.get_current_file()
        if path:
            method = load_settings().get("execution_method", "minescript")
            self.console.run_script(path, execution_method=method)
            self.status_bar.set_status("Running…")
            self.toast.info(f"Running {os.path.basename(path)}")
        else:
            self.toast.warning("No file loaded — save first")

    # ── Command Palette ────────────────────────────────────────────
    def _show_palette(self) -> None:
        actions = {
            "new_file": "New File",
            "open_file": "Open File…",
            "save_file": "Save File",
            "save_file_as": "Save File As…",
            "save_all": "Save All Open Files",
            "run_script": "Run Current Script",
            "find": "Find",
            "replace": "Find & Replace",
            "goto_home": "Go to Home",
            "goto_editor": "Go to Editor",
            "goto_scripts": "Go to Scripts",
            "goto_files": "Go to File Explorer",
            "goto_runner": "Go to Runner",
            "goto_console": "Go to Console",
            "goto_jobs": "Go to Jobs",
            "goto_inspector": "Go to World Inspector",
            "goto_snippets": "Go to Snippets",
            "goto_docs": "Go to Docs",
            "goto_reference": "Go to MC Reference",
            "goto_todos": "Go to TODO Scanner",
            "goto_git": "Go to Git",
            "goto_themes": "Go to Theme Creator",
            "goto_packages": "Go to Packages",
            "goto_plugins": "Go to Plugins",
            "goto_plugin_store": "Go to Plugin Store",
            "goto_script_store": "Go to Script Store",
            "goto_webhook": "Go to Discord Webhook",
            "goto_settings": "Go to Settings",
            "goto_shortcuts_editor": "Go to Keyboard Shortcuts",
            "goto_backups": "Go to Backup Manager",
            "toggle_sidebar": "Toggle Sidebar",
            "toggle_zen": "Toggle Zen Mode",
            "import_scripts": "Import Scripts…",
            "export_script": "Export Script…",
            "new_from_template": "New from Template…",
        }
        palette = CommandPalette(actions, parent=self)
        palette.action_selected.connect(self._on_palette_action)
        palette.exec()

    def _on_palette_action(self, key: str) -> None:
        dispatch = {
            "new_file": self.code_editor.new_file,
            "open_file": self.code_editor.open_file,
            "save_file": self.code_editor.save_file,
            "save_file_as": self.code_editor.save_file_as,
            "save_all": self.code_editor.save_all,
            "run_script": self._run_current,
            "find": self._toggle_find,
            "replace": self._toggle_replace,
            "toggle_sidebar": self.sidebar.toggle_collapse,
            "toggle_zen": lambda: self.code_editor._zen_btn.click(),
            "import_scripts": self._import_scripts,
            "export_script": self._export_script,
            "new_from_template": self._new_from_template,
        }
        if key.startswith("goto_"):
            tag = key[5:]
            self._goto_page(tag)
        elif key in dispatch:
            dispatch[key]()

    # ── Templates ──────────────────────────────────────────────────
    def _new_from_template(self) -> None:
        templates = list_templates()
        actions = {name: f"{name} — {info['description']}" for name, info in templates.items()}
        palette = CommandPalette(actions, parent=self)
        palette.setWindowTitle("Select Template")
        def apply_template(name: str):
            code = get_template(name)
            if code:
                self.code_editor.set_content(code, None)
                self._goto_page("editor")
                self.toast.info(f"Template '{name}' loaded")
        palette.action_selected.connect(apply_template)
        palette.exec()

    # ── Import / Export ────────────────────────────────────────────
    def _import_scripts(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Scripts", "", "Zip Archives (*.zip)"
        )
        if path:
            imported = script_io.import_scripts(path, str(_SCRIPTS_DIR))
            if imported:
                self.script_browser.refresh()
                self.front_page.refresh()
                self.toast.success(f"Imported {len(imported)} script(s)")
            else:
                self.toast.warning("No scripts found in archive")

    def _export_script(self) -> None:
        src = self.code_editor.get_current_file()
        if not src:
            self.toast.warning("No file loaded to export")
            return
        dest, _ = QFileDialog.getSaveFileName(
            self, "Export Script", os.path.basename(src).replace(".py", ".zip"), "Zip Archives (*.zip)"
        )
        if dest:
            if script_io.export_script(src, dest):
                self.toast.success("Script exported")
            else:
                self.toast.error("Export failed")

    # ── Theme application ──────────────────────────────────────────
    def _apply_theme(self, name: str) -> None:
        try:
            apply_theme(name)
            self.setStyleSheet(get_app_stylesheet())
            settings = load_settings()
            settings["theme"] = name
            save_settings(settings)
            self.toast.info(f"Theme changed to '{name}'")
        except Exception as e:
            self.toast.error(f"Theme error: {e}")

    # ── Drag and drop ──────────────────────────────────────────────
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith((".py", ".pyj", ".zip")):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.endswith(".zip"):
                imported = script_io.import_scripts(path, str(_SCRIPTS_DIR))
                if imported:
                    self.toast.success(f"Imported {len(imported)} script(s)")
                    self.script_browser.refresh()
            elif path.endswith((".py", ".pyj")):
                self.code_editor.open_path(path)
                self._goto_page("editor")
                self.toast.info(f"Opened {os.path.basename(path)}")

    # ── Script creator ─────────────────────────────────────────────
    def _open_creator(self) -> None:
        dlg = ScriptCreatorDialog(str(_SCRIPTS_DIR), parent=self)
        dlg.script_created.connect(lambda path: (
            self.front_page.refresh(),
            self.script_browser.refresh(),
            self.toast.success("Script created"),
        ))
        dlg.exec()

    # ── Session save / restore ─────────────────────────────────────
    def _restore_session(self) -> None:
        settings = load_settings()
        if not settings.get("session_restore", True):
            return
        session = load_session()
        if not session:
            return
        # Restore sidebar collapse
        if session.get("sidebar_collapsed"):
            self.sidebar.set_collapsed(True)
        # Restore open files
        for fp in session.get("open_files", []):
            if os.path.isfile(fp):
                self.code_editor.open_path(fp)
        # Restore page (clamp to valid range)
        page_idx = session.get("page_index", 0)
        if page_idx > self._pages.count() - 1:
            page_idx = 0
        self._pages.setCurrentIndex(page_idx)

    def _save_session(self) -> None:
        open_files = []
        for t in self.code_editor._tabs_data:
            if t.filepath:
                open_files.append(t.filepath)
        save_session(
            open_files=open_files,
            active_file=self.code_editor.get_current_file(),
            page_index=self._pages.currentIndex(),
            sidebar_collapsed=self.sidebar.collapsed,
        )

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_opened'):
            self._opened = True
            window_open_animation(self, DURATION_SMOOTH)

    def closeEvent(self, event):
        self._save_session()
        if not getattr(self, '_closing_done', False):
            event.ignore()
            if not getattr(self, '_closing', False):
                self._closing = True
                window_close_animation(self, 200, callback=self._real_close)
            return
        super().closeEvent(event)

    def _real_close(self):
        self._closing_done = True
        self.close()


class FluxusApp:
    def __init__(self):
        self.qt_app = QApplication.instance() or QApplication(sys.argv)
        self._window = None
        self._splash = None

    def run(self) -> None:
        # Show splash screen first
        self._splash = SplashScreen()
        self._splash.init_complete.connect(self._on_splash_done)
        self._splash.start()
        self.qt_app.exec()

    def _on_splash_done(self):
        """Called when splash finishes — create and show main window."""
        self._window = FluxusWindow()
        self._window.show()
        if self._splash:
            self._splash.deleteLater()
            self._splash = None

