"""
StatusBar — bottom bar with page indicator, script name, live player
HUD (position / health / biome / dimension) via Minescript, and version.
"""

import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

from ..Colors.palette import COLORS


def _fetch_player_info() -> dict | None:
    """Return player info dict or None if unavailable."""
    try:
        import minescript
        pos = minescript.player_position()
        info: dict = {
            "x": int(pos[0]),
            "y": int(pos[1]),
            "z": int(pos[2]),
        }
        # Try to get health
        try:
            health = minescript.player_health()
            info["health"] = f"{health:.0f}" if isinstance(health, float) else str(health)
        except Exception:
            info["health"] = "?"
        # Try to get biome / dimension through player()
        try:
            p = minescript.player()
            if hasattr(p, "dimension"):
                info["dimension"] = str(p.dimension)
            if hasattr(p, "biome"):
                info["biome"] = str(p.biome)
        except Exception:
            pass
        return info
    except Exception:
        return None


class StatusBar(QFrame):
    """Bottom status bar with live player HUD."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatusBar")
        self.setFixedHeight(26)
        self._build()
        # Auto-refresh HUD every 2 seconds
        self._hud_timer = QTimer(self)
        self._hud_timer.timeout.connect(self._refresh_hud)
        self._hud_timer.start(2000)
        self._refresh_hud()

    def _build(self) -> None:
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(16)
        self.setLayout(layout)

        self._page_label = QLabel("Editor")
        self._page_label.setObjectName("StatusText")
        layout.addWidget(self._page_label)

        sep1 = QLabel("│")
        sep1.setObjectName("StatusSep")
        layout.addWidget(sep1)

        self._script_label = QLabel("No script loaded")
        self._script_label.setObjectName("StatusText")
        layout.addWidget(self._script_label)

        layout.addStretch()

        # ── Player HUD labels ──────────────────────────────────────
        self._pos_label = QLabel("")
        self._pos_label.setObjectName("HudText")
        layout.addWidget(self._pos_label)

        self._health_label = QLabel("")
        self._health_label.setObjectName("HudText")
        layout.addWidget(self._health_label)

        self._dim_label = QLabel("")
        self._dim_label.setObjectName("HudText")
        layout.addWidget(self._dim_label)

        # ── Separator ──────────────────────────────────────────────
        self._hud_sep = QLabel("│")
        self._hud_sep.setObjectName("StatusSep")
        self._hud_sep.hide()
        layout.addWidget(self._hud_sep)

        self._status_label = QLabel("Ready")
        self._status_label.setObjectName("StatusText")
        layout.addWidget(self._status_label)

        sep2 = QLabel("│")
        sep2.setObjectName("StatusSep")
        layout.addWidget(sep2)

        self._version_label = QLabel("Fluxus V0.1")
        self._version_label.setObjectName("StatusText")
        layout.addWidget(self._version_label)

    # ── HUD refresh ────────────────────────────────────────────────
    def _refresh_hud(self) -> None:
        info = _fetch_player_info()
        if info is None:
            self._pos_label.hide()
            self._health_label.hide()
            self._dim_label.hide()
            self._hud_sep.hide()
            return
        self._hud_sep.show()
        self._pos_label.show()
        self._pos_label.setText(f"📍 {info['x']}, {info['y']}, {info['z']}")

        health = info.get("health", "")
        if health:
            self._health_label.show()
            self._health_label.setText(f"❤ {health}")
        else:
            self._health_label.hide()

        dim = info.get("dimension", "")
        if dim:
            self._dim_label.show()
            # Shorten dimension name
            short = dim.replace("minecraft:", "").replace("_", " ").title()
            self._dim_label.setText(f"🌍 {short}")
        else:
            self._dim_label.hide()

    def set_page(self, name: str) -> None:
        self._page_label.setText(name)

    def set_script(self, name: str) -> None:
        self._script_label.setText(name)

    def set_status(self, text: str) -> None:
        self._status_label.setText(text)
