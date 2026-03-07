"""
Git Panel — basic Git integration for viewing status, staging, committing.
Uses subprocess to call git commands (no external libraries needed).
"""

import subprocess
import threading
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPlainTextEdit, QPushButton, QVBoxLayout, QMessageBox,
)

from ..Colors.palette import COLORS


class _GitSignals(QObject):
    output = Signal(str)
    status_ready = Signal(list)  # list of (status, file) tuples
    error = Signal(str)


class GitPanel(QFrame):
    """Basic git integration: status, diff, stage, commit, log."""

    def __init__(self, working_dir: str, parent=None):
        super().__init__(parent)
        self.setObjectName("GitPanel")
        self._cwd = working_dir
        self._signals = _GitSignals()
        self._signals.output.connect(self._append_output)
        self._signals.status_ready.connect(self._show_status)
        self._signals.error.connect(self._show_error)
        self._build()

    def _build(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Header
        header = QFrame()
        header.setObjectName("BrowserHeader")
        header.setFixedHeight(36)
        hl = QHBoxLayout()
        hl.setContentsMargins(10, 0, 10, 0)
        hl.setSpacing(6)
        header.setLayout(hl)

        title = QLabel("🔀 Git")
        title.setObjectName("PanelTitle")
        hl.addWidget(title)
        hl.addStretch()

        refresh_btn = QPushButton("↻")
        refresh_btn.setObjectName("SmallButton")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh)
        hl.addWidget(refresh_btn)

        init_btn = QPushButton("Init")
        init_btn.setObjectName("SmallButton")
        init_btn.setCursor(Qt.PointingHandCursor)
        init_btn.setToolTip("Initialize git repository")
        init_btn.clicked.connect(self._git_init)
        hl.addWidget(init_btn)

        layout.addWidget(header)

        # Status label
        self._status_label = QLabel("Not initialized")
        self._status_label.setStyleSheet(
            f"color: {COLORS.get('text_secondary', '#a0a0c0')};"
            f" padding: 6px 10px; font-size: 11px;"
        )
        layout.addWidget(self._status_label)

        # File status list
        self._file_list = QListWidget()
        self._file_list.setObjectName("GitFileList")
        self._file_list.setAlternatingRowColors(True)
        self._file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self._file_list.setStyleSheet(f"""
            QListWidget {{
                background: {COLORS.get('bg_surface', '#16162e')};
                color: {COLORS.get('text_primary', '#e8e6f0')};
                border: 1px solid {COLORS.get('border', '#2a2a4a')};
                border-radius: 4px;
                font-family: 'Consolas'; font-size: 11px;
            }}
            QListWidget::item {{ padding: 3px 6px; }}
            QListWidget::item:selected {{
                background: {COLORS.get('accent', '#7c6aef')};
            }}
        """)
        layout.addWidget(self._file_list, 1)

        # Action buttons
        action_bar = QHBoxLayout()
        action_bar.setContentsMargins(8, 6, 8, 4)
        action_bar.setSpacing(6)

        stage_btn = QPushButton("+ Stage Selected")
        stage_btn.setObjectName("SmallButton")
        stage_btn.setCursor(Qt.PointingHandCursor)
        stage_btn.clicked.connect(self._stage_selected)
        action_bar.addWidget(stage_btn)

        stage_all = QPushButton("++ Stage All")
        stage_all.setObjectName("SmallButton")
        stage_all.setCursor(Qt.PointingHandCursor)
        stage_all.clicked.connect(self._stage_all)
        action_bar.addWidget(stage_all)

        unstage_btn = QPushButton("- Unstage")
        unstage_btn.setObjectName("SmallButton")
        unstage_btn.setCursor(Qt.PointingHandCursor)
        unstage_btn.clicked.connect(self._unstage_selected)
        action_bar.addWidget(unstage_btn)

        layout.addLayout(action_bar)

        # Commit area
        commit_area = QFrame()
        commit_area.setStyleSheet(
            f"background: {COLORS.get('bg_root', '#0e0e1e')};"
            f" border-top: 1px solid {COLORS.get('border', '#2a2a4a')};"
        )
        cl = QVBoxLayout()
        cl.setContentsMargins(8, 6, 8, 6)
        cl.setSpacing(4)
        commit_area.setLayout(cl)

        self._commit_msg = QLineEdit()
        self._commit_msg.setObjectName("SearchInput")
        self._commit_msg.setPlaceholderText("Commit message…")
        self._commit_msg.returnPressed.connect(self._commit)
        cl.addWidget(self._commit_msg)

        commit_row = QHBoxLayout()
        commit_btn = QPushButton("✓ Commit")
        commit_btn.setObjectName("AccentButton")
        commit_btn.setCursor(Qt.PointingHandCursor)
        commit_btn.clicked.connect(self._commit)
        commit_row.addWidget(commit_btn)
        commit_row.addStretch()
        cl.addLayout(commit_row)

        layout.addWidget(commit_area)

        # Output area
        self._output = QPlainTextEdit()
        self._output.setObjectName("ConsoleOutput")
        self._output.setReadOnly(True)
        self._output.setMaximumHeight(120)
        self._output.setStyleSheet(
            f"background: {COLORS.get('bg_root', '#0e0e1e')};"
            f" color: {COLORS.get('text_secondary', '#a0a0c0')};"
            f" font-family: Consolas; font-size: 10px;"
            f" border: none;"
        )
        layout.addWidget(self._output)

    def _git_cmd(self, args: list[str], callback=None):
        """Run a git command in a background thread."""
        def _run():
            try:
                result = subprocess.run(
                    ["git"] + args,
                    cwd=self._cwd,
                    capture_output=True,
                    text=True,
                    timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
                )
                out = result.stdout.strip()
                err = result.stderr.strip()
                if result.returncode != 0 and err:
                    self._signals.error.emit(err)
                elif out:
                    self._signals.output.emit(out)
                if callback:
                    callback(result)
            except FileNotFoundError:
                self._signals.error.emit("Git is not installed or not in PATH")
            except Exception as e:
                self._signals.error.emit(str(e))

        threading.Thread(target=_run, daemon=True).start()

    def refresh(self):
        """Refresh git status."""
        def _on_status(result):
            if result.returncode != 0:
                return
            lines = result.stdout.strip().splitlines()
            statuses = []
            for line in lines:
                if len(line) >= 4:
                    status_code = line[:2].strip()
                    filename = line[3:].strip()
                    statuses.append((status_code, filename))
            self._signals.status_ready.emit(statuses)

        self._git_cmd(["status", "--porcelain"], callback=_on_status)

        # Get branch
        def _on_branch(result):
            if result.returncode == 0:
                branch = result.stdout.strip()
                self._signals.output.emit(f"Branch: {branch}")

        self._git_cmd(["branch", "--show-current"], callback=_on_branch)

    def _show_status(self, statuses: list):
        self._file_list.clear()
        if not statuses:
            self._status_label.setText("✓ Working tree clean")
            return

        _STATUS_ICONS = {
            "M": "🟡 Modified",
            "A": "🟢 Added",
            "D": "🔴 Deleted",
            "R": "🔵 Renamed",
            "??": "⚪ Untracked",
            "UU": "⚠️ Conflict",
        }

        self._status_label.setText(f"{len(statuses)} changed files")

        for status, filename in statuses:
            display = f"{_STATUS_ICONS.get(status, status)}  {filename}"
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, filename)
            self._file_list.addItem(item)

    def _stage_selected(self):
        items = self._file_list.selectedItems()
        files = [item.data(Qt.UserRole) for item in items if item.data(Qt.UserRole)]
        if files:
            self._git_cmd(["add"] + files, callback=lambda _: self.refresh())

    def _stage_all(self):
        self._git_cmd(["add", "-A"], callback=lambda _: self.refresh())

    def _unstage_selected(self):
        items = self._file_list.selectedItems()
        files = [item.data(Qt.UserRole) for item in items if item.data(Qt.UserRole)]
        if files:
            self._git_cmd(["reset", "HEAD"] + files, callback=lambda _: self.refresh())

    def _commit(self):
        msg = self._commit_msg.text().strip()
        if not msg:
            self._show_error("Commit message cannot be empty")
            return
        self._commit_msg.clear()
        self._git_cmd(["commit", "-m", msg], callback=lambda _: self.refresh())

    def _git_init(self):
        self._git_cmd(["init"], callback=lambda _: self.refresh())

    def _append_output(self, text: str):
        self._output.appendPlainText(text)

    def _show_error(self, text: str):
        self._output.appendPlainText(f"ERROR: {text}")
