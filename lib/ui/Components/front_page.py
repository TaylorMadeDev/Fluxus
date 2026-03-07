"""
FrontPage — the home / dashboard page showing pinned scripts as large
one-click-run cards, recent activity, and a quick-create button.
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QPointF
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS
from .script_card import ScriptCard
from . import script_manifest as manifest


def _get_player_name() -> str | None:
    """Try to get the Minecraft player name via Minescript. Returns None outside MC."""
    try:
        import minescript  # only available when launched by the Minescript mod
        return minescript.player_name()
    except Exception:
        return None


class FrontPage(QFrame):
    """Dashboard page with pinned script cards for 1-click execution."""

    run_requested = Signal(str)       # script path
    edit_requested = Signal(str)      # script path
    configure_requested = Signal(str) # script path
    create_requested = Signal()       # open script creator

    def __init__(self, scripts_root: str, parent=None):
        super().__init__(parent)
        self.setObjectName("FrontPage")
        self._root = scripts_root
        self._cards: list[ScriptCard] = []
        self._player_name = _get_player_name()
        self._build()
        self.refresh()

    def _build(self) -> None:
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.setLayout(outer)

        # Header
        header = QFrame(self)
        header.setObjectName("FrontPageHeader")
        header.setFixedHeight(56)
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(20, 0, 20, 0)
        h_layout.setSpacing(12)
        header.setLayout(h_layout)

        logo = QLabel("◈")
        logo.setObjectName("FrontPageLogo")
        h_layout.addWidget(logo)

        # Greeting — personalised when running inside Minecraft
        if self._player_name:
            greeting = f"Welcome back, {self._player_name}"
        else:
            greeting = "Welcome to Fluxus"
        self._title_label = QLabel(greeting)
        self._title_label.setObjectName("FrontPageTitle")
        h_layout.addWidget(self._title_label)

        # Player badge (only when inside Minescript)
        if self._player_name:
            badge = QLabel(f"🎮 {self._player_name}")
            badge.setObjectName("PlayerBadge")
            h_layout.addWidget(badge)

        h_layout.addStretch()

        create_btn = QPushButton("+ Create Script")
        create_btn.setObjectName("AccentButton")
        create_btn.setCursor(Qt.PointingHandCursor)
        create_btn.clicked.connect(self.create_requested.emit)
        h_layout.addWidget(create_btn)

        refresh_btn = QPushButton("↻")
        refresh_btn.setObjectName("SmallButton")
        refresh_btn.setToolTip("Refresh")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh)
        h_layout.addWidget(refresh_btn)

        outer.addWidget(header)

        # Scrollable card area
        scroll = QScrollArea(self)
        scroll.setObjectName("FrontPageScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._container.setObjectName("FrontPageContainer")
        self._card_layout = QVBoxLayout()
        self._card_layout.setContentsMargins(20, 16, 20, 20)
        self._card_layout.setSpacing(12)
        self._container.setLayout(self._card_layout)

        scroll.setWidget(self._container)
        outer.addWidget(scroll, 1)

    def refresh(self) -> None:
        """Reload all pinned scripts and rebuild cards."""
        # Clear existing cards
        self._cards.clear()
        while self._card_layout.count():
            child = self._card_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # ── Section: Favorite Scripts ───────────────────────────
        favorites = manifest.list_favorites()
        if favorites:
            fav_label = QLabel("★  FAVORITES")
            fav_label.setObjectName("SectionLabel")
            self._card_layout.addWidget(fav_label)

            for path, meta in favorites:
                card = ScriptCard(path, meta)
                card.run_clicked.connect(self.run_requested.emit)
                card.edit_clicked.connect(self.edit_requested.emit)
                card.configure_clicked.connect(self.configure_requested.emit)
                card.toggle_clicked.connect(self._toggle_script)
                self._cards.append(card)
                self._card_layout.addWidget(card)

            self._card_layout.addSpacing(8)

        # ── Section: Pinned Scripts ─────────────────────────────
        pinned_label = QLabel("📌  PINNED SCRIPTS")
        pinned_label.setObjectName("SectionLabel")
        self._card_layout.addWidget(pinned_label)

        pinned = manifest.list_pinned(self._root)

        # Also scan the filesystem for any scripts that have manifests
        if not pinned:
            # If no pinned scripts, scan Scripts/ for .py files and suggest them
            root = Path(self._root)
            for f in sorted(root.rglob("*")):
                if f.suffix in (".py", ".pyj") and f.is_file():
                    meta = manifest.ensure_defaults(str(f))
                    pinned.append((str(f), meta))

        if not pinned:
            empty = QLabel("No pinned scripts yet.\nUse the Scripts page to pin scripts to your dashboard.")
            empty.setObjectName("FrontPageEmpty")
            empty.setAlignment(Qt.AlignCenter)
            empty.setWordWrap(True)
            empty.setMinimumHeight(120)
            self._card_layout.addWidget(empty)
        else:
            for path, meta in pinned:
                card = ScriptCard(path, meta)
                card.run_clicked.connect(self.run_requested.emit)
                card.edit_clicked.connect(self.edit_requested.emit)
                card.configure_clicked.connect(self.configure_requested.emit)
                card.toggle_clicked.connect(self._toggle_script)
                self._cards.append(card)
                self._card_layout.addWidget(card)

        # ── Section: Most Used ──────────────────────────────────
        most_used = manifest.list_most_used(5)
        if most_used:
            self._card_layout.addSpacing(12)
            mu_label = QLabel("🔥  MOST USED")
            mu_label.setObjectName("SectionLabel")
            self._card_layout.addWidget(mu_label)

            mu_row = QHBoxLayout()
            mu_row.setSpacing(8)
            for path, meta in most_used:
                chip = QFrame()
                chip.setObjectName("StatCard")
                chip.setFixedHeight(50)
                cl = QHBoxLayout()
                cl.setContentsMargins(10, 4, 10, 4)
                cl.setSpacing(6)
                chip.setLayout(cl)

                ic = QLabel(meta.get("icon", "📜"))
                ic.setFixedWidth(20)
                cl.addWidget(ic)

                nm = QLabel(meta.get("name", Path(path).stem))
                nm.setObjectName("CardName")
                nm.setStyleSheet("font-size: 11px;")
                cl.addWidget(nm)

                rc = QLabel(f"▶ {meta.get('run_count', 0)}")
                rc.setObjectName("CardVersion")
                rc.setStyleSheet(f"color: {COLORS.get('accent', '#7c6ff7')}; font-size: 10px;")
                cl.addWidget(rc)

                mu_row.addWidget(chip)
            mu_row.addStretch()
            self._card_layout.addLayout(mu_row)

        # ── Section: Quick Stats ────────────────────────────────
        self._card_layout.addSpacing(12)
        stats_label = QLabel("📊  QUICK STATS")
        stats_label.setObjectName("SectionLabel")
        self._card_layout.addWidget(stats_label)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        all_meta = manifest.list_all()
        total = len(all_meta)
        enabled = sum(1 for m in all_meta.values() if m.get("enabled", True))
        pinned_count = sum(1 for m in all_meta.values() if m.get("pinned", False))
        fav_count = sum(1 for m in all_meta.values() if m.get("favorite", False))
        total_runs = sum(m.get("run_count", 0) for m in all_meta.values())

        for value, label in [
            (str(total), "Total Scripts"),
            (str(enabled), "Active"),
            (str(pinned_count), "Pinned"),
            (str(fav_count), "Favorites"),
            (str(total_runs), "Total Runs"),
        ]:
            stat = QFrame()
            stat.setObjectName("StatCard")
            stat.setFixedHeight(70)
            sl = QVBoxLayout()
            sl.setContentsMargins(16, 8, 16, 8)
            sl.setSpacing(2)
            stat.setLayout(sl)

            val_lbl = QLabel(value)
            val_lbl.setObjectName("StatValue")
            val_lbl.setAlignment(Qt.AlignCenter)
            sl.addWidget(val_lbl)

            desc_lbl = QLabel(label)
            desc_lbl.setObjectName("StatLabel")
            desc_lbl.setAlignment(Qt.AlignCenter)
            sl.addWidget(desc_lbl)

            stats_row.addWidget(stat)

            # Hover shadow animation for stat cards
            shadow = QGraphicsDropShadowEffect(stat)
            shadow.setBlurRadius(4)
            shadow.setColor(QColor(0, 0, 0, 30))
            shadow.setOffset(0, 1)
            stat.setGraphicsEffect(shadow)
            stat._shadow = shadow

        self._card_layout.addLayout(stats_row)
        self._card_layout.addStretch()

    def _toggle_script(self, path: str) -> None:
        meta = manifest.get_meta(path)
        meta["enabled"] = not meta.get("enabled", True)
        manifest.set_meta(path, meta)
        self.refresh()
