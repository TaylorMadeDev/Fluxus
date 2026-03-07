import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout,
)

from ..Colors.palette import COLORS


class PackagesPanel(QFrame):
    """Panel showing installed Minescript packages and blockpacks."""

    def __init__(self, root_dir: str | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("PackagesPanel")
        self._root = root_dir or str(Path(__file__).resolve().parents[3])
        self._build()
        self.refresh()

    def _build(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Header
        header = QFrame(self)
        header.setObjectName("PackagesHeader")
        header.setFixedHeight(40)
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(12, 0, 12, 0)
        h_layout.setSpacing(8)
        header.setLayout(h_layout)

        title = QLabel("📦  Packages & BlockPacks")
        title.setObjectName("PanelTitle")
        h_layout.addWidget(title)
        h_layout.addStretch()

        refresh_btn = QPushButton("↻")
        refresh_btn.setObjectName("SmallButton")
        refresh_btn.setToolTip("Refresh")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh)
        h_layout.addWidget(refresh_btn)

        layout.addWidget(header)

        # Blockpacks section
        bp_label = QLabel("  Block Packs")
        bp_label.setObjectName("SectionLabel")
        bp_label.setContentsMargins(12, 10, 0, 4)
        layout.addWidget(bp_label)

        self._bp_list = QListWidget()
        self._bp_list.setObjectName("PackageList")
        layout.addWidget(self._bp_list)

        # System modules section
        mod_label = QLabel("  System Modules")
        mod_label.setObjectName("SectionLabel")
        mod_label.setContentsMargins(12, 10, 0, 4)
        layout.addWidget(mod_label)

        self._mod_list = QListWidget()
        self._mod_list.setObjectName("PackageList")
        layout.addWidget(self._mod_list)

        # Mappings section
        map_label = QLabel("  Mappings")
        map_label.setObjectName("SectionLabel")
        map_label.setContentsMargins(12, 10, 0, 4)
        layout.addWidget(map_label)

        self._map_list = QListWidget()
        self._map_list.setObjectName("PackageList")
        layout.addWidget(self._map_list)

        layout.addStretch()

        # Open folder button
        open_btn = QPushButton("Open Minescript Folder")
        open_btn.setObjectName("EditorToolButton")
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setContentsMargins(12, 6, 12, 10)
        open_btn.clicked.connect(self._open_root)
        layout.addWidget(open_btn)

    def refresh(self) -> None:
        root = Path(self._root)

        # Blockpacks
        self._bp_list.clear()
        bp_dir = root / "blockpacks"
        if bp_dir.is_dir():
            items = sorted(bp_dir.iterdir())
            for item in items:
                self._bp_list.addItem(f"  {item.name}")
        if self._bp_list.count() == 0:
            self._bp_list.addItem("  (none)")

        # System modules
        self._mod_list.clear()
        lib_dir = root / "system" / "lib"
        if lib_dir.is_dir():
            for f in sorted(lib_dir.glob("*.py")):
                self._mod_list.addItem(f"  {f.name}")

        exec_dir = root / "system" / "exec"
        if exec_dir.is_dir():
            for f in sorted(exec_dir.iterdir()):
                if f.suffix in (".py", ".pyj"):
                    self._mod_list.addItem(f"  exec/{f.name}")

        # Mappings
        self._map_list.clear()
        map_dir = root / "system" / "mappings"
        if map_dir.is_dir():
            for d in sorted(map_dir.iterdir()):
                if d.is_dir():
                    count = sum(1 for _ in d.iterdir())
                    self._map_list.addItem(f"  {d.name}  ({count} files)")
        if self._map_list.count() == 0:
            self._map_list.addItem("  (none)")

    def _open_root(self) -> None:
        if sys.platform == "win32":
            os.startfile(self._root)
