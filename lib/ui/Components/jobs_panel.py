"""
JobsPanel — displays active Minescript jobs when running inside Minecraft.
Calls ``minescript.job_info()`` and presents the results in a styled table.
When run outside Minecraft the panel shows a friendly fallback message.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QSizePolicy, QScrollArea, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS

# ── Column definitions ──────────────────────────────────────────────
_COLUMNS = [
    ("Job ID",    "job_id"),
    ("Command",   "command"),
    ("Source",    "source"),
    ("Status",    "status"),
    ("Parent ID", "parent_job_id"),
    ("Self",      "self"),
    ("Actions",   "_actions"),
]


def _fetch_jobs():
    """Return a list of JobInfo objects, or *None* if Minescript is unavailable."""
    try:
        import minescript          # only present when launched by the mod
        return minescript.job_info()
    except Exception:
        return None


class JobsPanel(QFrame):
    """Full-page panel that lists every active Minescript job."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("JobsPanel")
        self._auto_timer: QTimer | None = None
        self._build()
        self.refresh()

    # ── UI construction ─────────────────────────────────────────────
    def _build(self) -> None:
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.setLayout(outer)

        # Scrollable wrapper
        scroll = QScrollArea()
        scroll.setObjectName("JobsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll)

        container = QWidget()
        container.setObjectName("JobsContainer")
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(28, 22, 28, 22)
        self._layout.setSpacing(16)
        container.setLayout(self._layout)
        scroll.setWidget(container)

        # ── Header row ──────────────────────────────────────────────
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        title = QLabel("⚡  Minescript Jobs")
        title.setObjectName("JobsTitle")
        header_row.addWidget(title)

        header_row.addStretch()

        # Auto-refresh toggle
        self._auto_btn = QPushButton("Auto ⏸")
        self._auto_btn.setObjectName("JobsHeaderBtn")
        self._auto_btn.setCursor(Qt.PointingHandCursor)
        self._auto_btn.setToolTip("Toggle 3-second auto-refresh")
        self._auto_btn.clicked.connect(self._toggle_auto)
        header_row.addWidget(self._auto_btn)

        refresh_btn = QPushButton("⟳  Refresh")
        refresh_btn.setObjectName("JobsHeaderBtn")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh)
        header_row.addWidget(refresh_btn)

        self._layout.addLayout(header_row)

        # ── Subtitle / count ────────────────────────────────────────
        self._subtitle = QLabel("")
        self._subtitle.setObjectName("JobsSubtitle")
        self._layout.addWidget(self._subtitle)

        # ── Table ───────────────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setObjectName("JobsTable")
        self._table.setColumnCount(len(_COLUMNS))
        self._table.setHorizontalHeaderLabels([c[0] for c in _COLUMNS])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._layout.addWidget(self._table, 1)

        # ── Fallback message (hidden by default) ────────────────────
        self._fallback = QLabel(
            "🎮  Jobs are only visible when Fluxus is\n"
            "launched from inside Minecraft via Minescript."
        )
        self._fallback.setObjectName("JobsFallback")
        self._fallback.setAlignment(Qt.AlignCenter)
        self._fallback.setWordWrap(True)
        self._fallback.hide()
        self._layout.addWidget(self._fallback, 1)

        # ── Legend ──────────────────────────────────────────────────
        legend = QLabel(
            "JobInfo fields: job_id · command · source · status · parent_job_id · self"
        )
        legend.setObjectName("JobsLegend")
        self._layout.addWidget(legend)

    # ── Data refresh ────────────────────────────────────────────────
    def refresh(self) -> None:
        jobs = _fetch_jobs()

        if jobs is None:
            self._table.hide()
            self._fallback.show()
            self._subtitle.setText("Minescript API not available")
            return

        self._fallback.hide()
        self._table.show()

        self._table.setRowCount(len(jobs))
        self_job_id = None

        for row, job in enumerate(jobs):
            job_id = getattr(job, "job_id", "?")
            command = getattr(job, "command", [])
            source = getattr(job, "source", "")
            status = getattr(job, "status", "")
            parent = getattr(job, "parent_job_id", None)
            is_self = getattr(job, "self", False)

            if is_self:
                self_job_id = job_id

            cmd_text = " ".join(str(c) for c in command) if isinstance(command, list) else str(command)
            parent_text = str(parent) if parent is not None else "—"

            values = [
                str(job_id),
                cmd_text,
                str(source),
                str(status),
                parent_text,
                "✓" if is_self else "",
            ]

            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)

                # Highlight the current job row
                if is_self:
                    item.setForeground(QColor(COLORS["accent"]))

                # Color-code status
                if col == 3:  # status column
                    lower = val.lower()
                    if "run" in lower:
                        item.setForeground(QColor(COLORS["success"]))
                    elif "stop" in lower or "kill" in lower:
                        item.setForeground(QColor(COLORS["danger"]))
                    elif "suspend" in lower or "paus" in lower:
                        item.setForeground(QColor(COLORS["warning"]))

                self._table.setItem(row, col, item)

            # Actions column — kill / suspend / resume buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(2, 1, 2, 1)
            actions_layout.setSpacing(3)
            actions_widget.setLayout(actions_layout)

            if not is_self:  # don't allow killing Fluxus itself
                kill_btn = QPushButton("✕")
                kill_btn.setObjectName("DangerSmallButton")
                kill_btn.setToolTip("Kill job")
                kill_btn.setFixedSize(24, 20)
                kill_btn.setCursor(Qt.PointingHandCursor)
                kill_btn.clicked.connect(lambda _, jid=job_id: self._kill_job(jid))
                actions_layout.addWidget(kill_btn)

                susp_btn = QPushButton("⏸")
                susp_btn.setObjectName("SmallButton")
                susp_btn.setToolTip("Suspend job")
                susp_btn.setFixedSize(24, 20)
                susp_btn.setCursor(Qt.PointingHandCursor)
                susp_btn.clicked.connect(lambda _, jid=job_id: self._suspend_job(jid))
                actions_layout.addWidget(susp_btn)

                res_btn = QPushButton("▶")
                res_btn.setObjectName("SmallButton")
                res_btn.setToolTip("Resume job")
                res_btn.setFixedSize(24, 20)
                res_btn.setCursor(Qt.PointingHandCursor)
                res_btn.clicked.connect(lambda _, jid=job_id: self._resume_job(jid))
                actions_layout.addWidget(res_btn)

            self._table.setCellWidget(row, 6, actions_widget)

        count = len(jobs)
        self_text = f"  ·  This job → #{self_job_id}" if self_job_id is not None else ""
        self._subtitle.setText(f"{count} active job{'s' if count != 1 else ''}{self_text}")

    # ── Job actions ───────────────────────────────────────────────
    def _kill_job(self, job_id) -> None:
        try:
            import minescript
            minescript.execute(f"\\job_kill {job_id}")
        except Exception:
            pass
        self.refresh()

    def _suspend_job(self, job_id) -> None:
        try:
            import minescript
            minescript.execute(f"\\job_suspend {job_id}")
        except Exception:
            pass
        self.refresh()

    def _resume_job(self, job_id) -> None:
        try:
            import minescript
            minescript.execute(f"\\job_resume {job_id}")
        except Exception:
            pass
        self.refresh()

    # ── Auto-refresh ────────────────────────────────────────────────
    def _toggle_auto(self) -> None:
        if self._auto_timer and self._auto_timer.isActive():
            self._auto_timer.stop()
            self._auto_btn.setText("Auto ⏸")
        else:
            if self._auto_timer is None:
                self._auto_timer = QTimer(self)
                self._auto_timer.timeout.connect(self.refresh)
            self._auto_timer.start(3000)
            self._auto_btn.setText("Auto ▶")
