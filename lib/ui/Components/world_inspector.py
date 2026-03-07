"""
WorldInspector — browse blocks and entities around the player.
Uses ``minescript.getblock()`` and ``minescript.entities()``; shows
a friendly placeholder when the Minescript API is not available.
"""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSpinBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS


def _minescript_available() -> bool:
    try:
        import minescript
        return True
    except Exception:
        return False


def _player_pos():
    """Return (x, y, z) as ints or None."""
    try:
        import minescript
        pos = minescript.player_position()
        return (int(pos[0]), int(pos[1]), int(pos[2]))
    except Exception:
        return None


def _get_block(x: int, y: int, z: int) -> str:
    try:
        import minescript
        return str(minescript.getblock(x, y, z))
    except Exception:
        return "unavailable"


def _get_entities():
    """Return list of entity dicts or empty list."""
    try:
        import minescript
        return minescript.entities()
    except Exception:
        return []


class WorldInspector(QFrame):
    """Minescript world inspector — blocks + entities + scan."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WorldInspector")
        self._build()
        self.refresh()

    # ── build ───────────────────────────────────────────────────────
    def _build(self) -> None:
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.setLayout(outer)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll)

        container = QWidget()
        self._vlayout = QVBoxLayout()
        self._vlayout.setContentsMargins(28, 22, 28, 22)
        self._vlayout.setSpacing(16)
        container.setLayout(self._vlayout)
        scroll.setWidget(container)

        # Header
        h = QHBoxLayout()
        h.setSpacing(10)
        title = QLabel("🔍  World Inspector")
        title.setObjectName("JobsTitle")
        h.addWidget(title)
        h.addStretch()
        refresh_btn = QPushButton("⟳  Refresh")
        refresh_btn.setObjectName("JobsHeaderBtn")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh)
        h.addWidget(refresh_btn)
        self._vlayout.addLayout(h)

        self._subtitle = QLabel("")
        self._subtitle.setObjectName("JobsSubtitle")
        self._vlayout.addWidget(self._subtitle)

        # Tabs: Block Probe / Entity List / Block Scan
        self._tabs = QTabWidget()
        self._tabs.setObjectName("InspectorTabs")
        self._vlayout.addWidget(self._tabs, 1)

        # — Tab 1: Block Probe ———————————————————————————————————————
        block_page = QWidget()
        bl = QVBoxLayout()
        bl.setContentsMargins(12, 12, 12, 12)
        bl.setSpacing(10)
        block_page.setLayout(bl)

        coords_row = QHBoxLayout()
        coords_row.setSpacing(6)
        self._xspin = self._spin("X")
        self._yspin = self._spin("Y")
        self._zspin = self._spin("Z")
        coords_row.addWidget(QLabel("X")); coords_row.addWidget(self._xspin)
        coords_row.addWidget(QLabel("Y")); coords_row.addWidget(self._yspin)
        coords_row.addWidget(QLabel("Z")); coords_row.addWidget(self._zspin)

        probe_btn = QPushButton("🔎 Probe")
        probe_btn.setObjectName("AccentButton")
        probe_btn.setCursor(Qt.PointingHandCursor)
        probe_btn.clicked.connect(self._probe_block)
        coords_row.addWidget(probe_btn)

        here_btn = QPushButton("📍 At Player")
        here_btn.setObjectName("SmallButton")
        here_btn.setCursor(Qt.PointingHandCursor)
        here_btn.clicked.connect(self._set_player_coords)
        coords_row.addWidget(here_btn)
        coords_row.addStretch()
        bl.addLayout(coords_row)

        self._block_result = QLabel("—")
        self._block_result.setObjectName("InspectorResult")
        self._block_result.setWordWrap(True)
        bl.addWidget(self._block_result)

        # Block scan table (small 3x3x3 around coords)
        self._block_table = QTableWidget()
        self._block_table.setObjectName("JobsTable")
        self._block_table.setColumnCount(4)
        self._block_table.setHorizontalHeaderLabels(["X", "Y", "Z", "Block"])
        self._block_table.horizontalHeader().setStretchLastSection(True)
        self._block_table.verticalHeader().setVisible(False)
        self._block_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._block_table.setAlternatingRowColors(True)
        self._block_table.setShowGrid(False)
        bl.addWidget(self._block_table, 1)

        scan_btn = QPushButton("🧱 Scan 3×3×3")
        scan_btn.setObjectName("SmallButton")
        scan_btn.setCursor(Qt.PointingHandCursor)
        scan_btn.clicked.connect(self._scan_blocks)
        bl.addWidget(scan_btn)

        self._tabs.addTab(block_page, "🧱 Blocks")

        # — Tab 2: Entities ——————————————————————————————————————————
        entity_page = QWidget()
        el = QVBoxLayout()
        el.setContentsMargins(12, 12, 12, 12)
        el.setSpacing(10)
        entity_page.setLayout(el)

        self._entity_table = QTableWidget()
        self._entity_table.setObjectName("JobsTable")
        self._entity_table.setColumnCount(4)
        self._entity_table.setHorizontalHeaderLabels(["Type", "Name", "Position", "Health"])
        self._entity_table.horizontalHeader().setStretchLastSection(True)
        self._entity_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._entity_table.verticalHeader().setVisible(False)
        self._entity_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._entity_table.setAlternatingRowColors(True)
        self._entity_table.setShowGrid(False)
        el.addWidget(self._entity_table, 1)

        refresh_ent = QPushButton("⟳ Refresh Entities")
        refresh_ent.setObjectName("SmallButton")
        refresh_ent.setCursor(Qt.PointingHandCursor)
        refresh_ent.clicked.connect(self._load_entities)
        el.addWidget(refresh_ent)

        self._tabs.addTab(entity_page, "🐄 Entities")

        # — Fallback message ————————————————————————————————————————
        self._fallback = QLabel(
            "🎮  World Inspector is only available when Fluxus\n"
            "is running inside Minecraft via Minescript.\n\n"
            "Features available when connected:\n"
            "  · Probe any block by coordinates\n"
            "  · Scan 3×3×3 block regions\n"
            "  · List nearby entities with types and health\n"
            "  · Use 📍 At Player to jump to your current position"
        )
        self._fallback.setObjectName("JobsFallback")
        self._fallback.setAlignment(Qt.AlignCenter)
        self._fallback.setWordWrap(True)
        self._fallback.hide()
        self._vlayout.addWidget(self._fallback, 1)

    def _spin(self, label: str) -> QSpinBox:
        s = QSpinBox()
        s.setRange(-30000000, 30000000)
        s.setObjectName("SettingsInput")
        s.setFixedWidth(90)
        return s

    # ── actions ─────────────────────────────────────────────────────
    def refresh(self) -> None:
        if not _minescript_available():
            self._tabs.hide()
            self._fallback.show()
            self._subtitle.setText("Minescript API not available")
            return
        self._fallback.hide()
        self._tabs.show()
        pos = _player_pos()
        if pos:
            self._subtitle.setText(f"Player at  X={pos[0]}  Y={pos[1]}  Z={pos[2]}")
            self._xspin.setValue(pos[0])
            self._yspin.setValue(pos[1])
            self._zspin.setValue(pos[2])
        else:
            self._subtitle.setText("Connected — position unknown")
        self._load_entities()

    def _set_player_coords(self) -> None:
        pos = _player_pos()
        if pos:
            self._xspin.setValue(pos[0])
            self._yspin.setValue(pos[1])
            self._zspin.setValue(pos[2])

    def _probe_block(self) -> None:
        x, y, z = self._xspin.value(), self._yspin.value(), self._zspin.value()
        block = _get_block(x, y, z)
        self._block_result.setText(f"Block at ({x}, {y}, {z}):  {block}")

    def _scan_blocks(self) -> None:
        cx, cy, cz = self._xspin.value(), self._yspin.value(), self._zspin.value()
        rows = []
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                for dz in range(-1, 2):
                    x, y, z = cx + dx, cy + dy, cz + dz
                    b = _get_block(x, y, z)
                    if b != "minecraft:air":
                        rows.append((x, y, z, b))
        self._block_table.setRowCount(len(rows))
        for r, (x, y, z, b) in enumerate(rows):
            for c, v in enumerate([str(x), str(y), str(z), b]):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                self._block_table.setItem(r, c, item)

    def _load_entities(self) -> None:
        ents = _get_entities()
        self._entity_table.setRowCount(len(ents))
        for r, ent in enumerate(ents):
            etype = str(getattr(ent, "type", "?") if not isinstance(ent, dict) else ent.get("type", "?"))
            ename = str(getattr(ent, "name", "") if not isinstance(ent, dict) else ent.get("name", ""))
            epos = ""
            try:
                p = getattr(ent, "position", None) if not isinstance(ent, dict) else ent.get("position")
                if p:
                    epos = f"{p[0]:.0f}, {p[1]:.0f}, {p[2]:.0f}"
            except Exception:
                pass
            ehealth = ""
            try:
                h = getattr(ent, "health", None) if not isinstance(ent, dict) else ent.get("health")
                if h is not None:
                    ehealth = f"{h}"
            except Exception:
                pass
            for c, v in enumerate([etype, ename, epos, ehealth]):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                self._entity_table.setItem(r, c, item)
