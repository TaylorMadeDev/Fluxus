import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QVBoxLayout,
)

from ..Colors.palette import COLORS


class ScriptRunner(QFrame):
    """Panel for selecting, running, and managing script execution."""

    run_requested = Signal(str)  # full script path
    open_requested = Signal(str)

    def __init__(self, scripts_root: str | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("ScriptRunner")
        self._root = scripts_root or str(Path(__file__).resolve().parents[3])
        self._history: list[dict] = []
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Header
        header = QFrame(self)
        header.setObjectName("RunnerHeader")
        header.setFixedHeight(40)
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(12, 0, 12, 0)
        h_layout.setSpacing(8)
        header.setLayout(h_layout)

        title = QLabel("▶  Script Runner")
        title.setObjectName("PanelTitle")
        h_layout.addWidget(title)
        h_layout.addStretch()
        layout.addWidget(header)

        # Script selector
        sel_frame = QFrame(self)
        sel_frame.setObjectName("RunnerSelector")
        sf_layout = QVBoxLayout()
        sf_layout.setContentsMargins(12, 10, 12, 10)
        sf_layout.setSpacing(8)
        sel_frame.setLayout(sf_layout)

        lbl = QLabel("Select Script:")
        lbl.setObjectName("FieldLabel")
        sf_layout.addWidget(lbl)

        self._script_combo = QComboBox()
        self._script_combo.setObjectName("ScriptCombo")
        sf_layout.addWidget(self._script_combo)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._run_btn = QPushButton("▶  Run Script")
        self._run_btn.setObjectName("AccentButton")
        self._run_btn.setCursor(Qt.PointingHandCursor)
        self._run_btn.clicked.connect(self._on_run)
        btn_row.addWidget(self._run_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("EditorToolButton")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.clicked.connect(self._on_edit)
        btn_row.addWidget(edit_btn)

        refresh_btn = QPushButton("↻")
        refresh_btn.setObjectName("SmallButton")
        refresh_btn.setToolTip("Refresh scripts")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_scripts)
        btn_row.addWidget(refresh_btn)

        sf_layout.addLayout(btn_row)
        layout.addWidget(sel_frame)

        # Execution history
        hist_header = QLabel("  Recent Executions")
        hist_header.setObjectName("SectionLabel")
        hist_header.setContentsMargins(12, 10, 0, 4)
        layout.addWidget(hist_header)

        self._history_list = QListWidget()
        self._history_list.setObjectName("HistoryList")
        layout.addWidget(self._history_list, 1)

        # Quick actions
        actions = QFrame(self)
        actions.setObjectName("QuickActions")
        a_layout = QVBoxLayout()
        a_layout.setContentsMargins(12, 8, 12, 10)
        a_layout.setSpacing(6)
        actions.setLayout(a_layout)

        qa_label = QLabel("Quick Actions")
        qa_label.setObjectName("SectionLabel")
        a_layout.addWidget(qa_label)

        for text, tip in [
            ("Run Last Script", "Re-run the most recently executed script"),
            ("Run All Tests", "Execute all test_* scripts"),
            ("Open Scripts Folder", "Open the scripts directory in Explorer"),
        ]:
            btn = QPushButton(text)
            btn.setObjectName("EditorToolButton")
            btn.setToolTip(tip)
            btn.setCursor(Qt.PointingHandCursor)
            if "Last" in text:
                btn.clicked.connect(self._run_last)
            elif "Tests" in text:
                btn.clicked.connect(self._run_tests)
            elif "Folder" in text:
                btn.clicked.connect(self._open_folder)
            a_layout.addWidget(btn)

        layout.addWidget(actions)

        self.refresh_scripts()

    def refresh_scripts(self) -> None:
        self._script_combo.clear()
        root = Path(self._root)
        if root.is_dir():
            scripts = sorted(
                [f for f in root.rglob("*.[p][y]*") if f.is_file() and f.suffix in (".py", ".pyj")],
                key=lambda p: p.name.lower()
            )
            for s in scripts:
                try:
                    rel = str(s.relative_to(self._root))
                except ValueError:
                    rel = str(s)
                self._script_combo.addItem(rel, str(s))

    def add_history_entry(self, script: str, exit_code: int) -> None:
        import datetime
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        icon = "✓" if exit_code == 0 else "✗"
        name = Path(script).name
        entry = f"{icon}  [{ts}]  {name}  →  exit {exit_code}"
        self._history.insert(0, {"script": script, "code": exit_code, "text": entry})
        self._history_list.insertItem(0, entry)
        if self._history_list.count() > 50:
            self._history_list.takeItem(50)

    def _on_run(self) -> None:
        path = self._script_combo.currentData()
        if path:
            self.run_requested.emit(path)

    def _on_edit(self) -> None:
        path = self._script_combo.currentData()
        if path:
            self.open_requested.emit(path)

    def _run_last(self) -> None:
        if self._history:
            self.run_requested.emit(self._history[0]["script"])

    def _run_tests(self) -> None:
        root = Path(self._root)
        test_files = [f for f in root.rglob("test_*") if f.suffix in (".py", ".pyj")]
        for s in sorted(test_files):
            self.run_requested.emit(str(s))

    def _open_folder(self) -> None:
        if sys.platform == "win32":
            os.startfile(self._root)
