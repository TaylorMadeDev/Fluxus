"""
Backup Manager — create and restore backups of scripts, settings, and config.
"""

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QVBoxLayout,
)

from ..Colors.palette import COLORS

_BACKUP_DIR = Path(__file__).resolve().parents[3] / "backups"


class BackupManager(QFrame):
    """Panel for creating and restoring backups."""

    backup_restored = Signal()

    def __init__(self, scripts_root: str, parent=None):
        super().__init__(parent)
        self.setObjectName("BackupManager")
        self._root = scripts_root
        self._config_root = str(Path(__file__).resolve().parents[3])
        _BACKUP_DIR.mkdir(exist_ok=True)
        self._build()
        self.refresh()

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

        title = QLabel("💾 Backups")
        title.setObjectName("PanelTitle")
        hl.addWidget(title)
        hl.addStretch()

        create_btn = QPushButton("+ Create Backup")
        create_btn.setObjectName("AccentButton")
        create_btn.setCursor(Qt.PointingHandCursor)
        create_btn.clicked.connect(self._create_backup)
        hl.addWidget(create_btn)

        layout.addWidget(header)

        # Backup list
        self._list = QListWidget()
        self._list.setObjectName("BackupList")
        self._list.setAlternatingRowColors(True)
        self._list.setStyleSheet(f"""
            QListWidget {{
                background: {COLORS.get('bg_surface', '#16162e')};
                color: {COLORS.get('text_primary', '#e8e6f0')};
                border: 1px solid {COLORS.get('border', '#2a2a4a')};
                border-radius: 4px;
                font-family: 'Consolas'; font-size: 11px;
            }}
            QListWidget::item {{ padding: 6px 8px; }}
            QListWidget::item:selected {{
                background: {COLORS.get('accent', '#7c6aef')};
            }}
            QListWidget::item:alternate {{
                background: {COLORS.get('bg_root', '#0e0e1e')};
            }}
        """)
        layout.addWidget(self._list, 1)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(8, 6, 8, 6)
        btn_row.setSpacing(6)

        restore_btn = QPushButton("♻ Restore Selected")
        restore_btn.setObjectName("SmallButton")
        restore_btn.setCursor(Qt.PointingHandCursor)
        restore_btn.clicked.connect(self._restore_selected)
        btn_row.addWidget(restore_btn)

        export_btn = QPushButton("📤 Export")
        export_btn.setObjectName("SmallButton")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export_backup)
        btn_row.addWidget(export_btn)

        import_btn = QPushButton("📥 Import")
        import_btn.setObjectName("SmallButton")
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.clicked.connect(self._import_backup)
        btn_row.addWidget(import_btn)

        btn_row.addStretch()

        delete_btn = QPushButton("🗑 Delete")
        delete_btn.setObjectName("DangerSmallButton")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(delete_btn)

        layout.addLayout(btn_row)

        # Info
        self._info = QLabel("")
        self._info.setObjectName("BrowserInfo")
        self._info.setContentsMargins(10, 4, 10, 4)
        layout.addWidget(self._info)

    def refresh(self):
        self._list.clear()
        backups = sorted(_BACKUP_DIR.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
        for bp in backups:
            size_mb = bp.stat().st_size / (1024 * 1024)
            ts = datetime.fromtimestamp(bp.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            display = f"💾 {bp.stem}  ({size_mb:.1f} MB)  —  {ts}"
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, str(bp))
            self._list.addItem(item)
        self._info.setText(f"{len(backups)} backup(s)")

    def _create_backup(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"fluxus_backup_{ts}.zip"
        backup_path = _BACKUP_DIR / name

        try:
            with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # Backup scripts
                scripts = Path(self._root)
                if scripts.is_dir():
                    for f in scripts.rglob("*"):
                        if f.is_file() and "__pycache__" not in str(f):
                            zf.write(f, f"Scripts/{f.relative_to(scripts)}")

                # Backup config files
                config_root = Path(self._config_root)
                for cfg_name in [
                    "fluxus_settings.json",
                    "fluxus_session.json",
                    "fluxus_shortcuts.json",
                    "fluxus_scripts.json",
                    "config.txt",
                ]:
                    cfg = config_root / cfg_name
                    if cfg.exists():
                        zf.write(cfg, f"config/{cfg_name}")

            self.refresh()
            self._info.setText(f"Backup created: {name}")
        except Exception as e:
            QMessageBox.warning(self, "Backup Error", str(e))

    def _restore_selected(self):
        item = self._list.currentItem()
        if not item:
            return
        path = item.data(Qt.UserRole)
        if not path:
            return

        reply = QMessageBox.question(
            self, "Restore Backup",
            "This will overwrite current scripts and settings.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            with zipfile.ZipFile(path, "r") as zf:
                for member in zf.namelist():
                    if member.startswith("Scripts/"):
                        target = Path(self._root) / member[len("Scripts/"):]
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as src, open(target, "wb") as dst:
                            dst.write(src.read())
                    elif member.startswith("config/"):
                        target = Path(self._config_root) / member[len("config/"):]
                        with zf.open(member) as src, open(target, "wb") as dst:
                            dst.write(src.read())

            self._info.setText("Backup restored!")
            self.backup_restored.emit()
        except Exception as e:
            QMessageBox.warning(self, "Restore Error", str(e))

    def _export_backup(self):
        item = self._list.currentItem()
        if not item:
            return
        src = item.data(Qt.UserRole)
        if not src:
            return
        dest, _ = QFileDialog.getSaveFileName(
            self, "Export Backup", Path(src).name, "Zip Archives (*.zip)"
        )
        if dest:
            try:
                shutil.copy2(src, dest)
                self._info.setText(f"Exported to {Path(dest).name}")
            except Exception as e:
                QMessageBox.warning(self, "Export Error", str(e))

    def _import_backup(self):
        src, _ = QFileDialog.getOpenFileName(
            self, "Import Backup", "", "Zip Archives (*.zip)"
        )
        if src:
            try:
                dest = _BACKUP_DIR / Path(src).name
                shutil.copy2(src, dest)
                self.refresh()
                self._info.setText(f"Imported {Path(src).name}")
            except Exception as e:
                QMessageBox.warning(self, "Import Error", str(e))

    def _delete_selected(self):
        item = self._list.currentItem()
        if not item:
            return
        path = item.data(Qt.UserRole)
        if not path:
            return
        reply = QMessageBox.question(
            self, "Delete Backup",
            f"Delete '{Path(path).name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                Path(path).unlink(missing_ok=True)
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Delete Error", str(e))
