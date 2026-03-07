"""
Plugin Store — browse and install community Minescript plugins from JSONBin API.

Fetches plugin metadata from a remote JSON endpoint, displays cards with
title, author, description, downloads count, and a one-click install button
that downloads the zip/py and extracts it into the plugins/ directory.
"""

import io
import json
import os
import threading
import zipfile
from pathlib import Path
from urllib import request as urllib_request
from urllib.error import URLError

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS

_API_URL = "https://api.jsonbin.io/v3/b/69ab06c5ae596e708f6664cd"
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "Scripts"
_SCRIPTS_DIR.mkdir(exist_ok=True)
_PLUGINS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "plugins"
_PLUGINS_DIR.mkdir(exist_ok=True)


class _StoreSignals(QObject):
    """Thread-safe signals for async fetching."""
    data_ready = Signal(list)     # list of script dicts
    fetch_error = Signal(str)     # error message
    download_done = Signal(str)   # script title
    download_error = Signal(str)  # error


class PluginStoreCard(QFrame):
    """Visual card for a single community plugin."""

    install_requested = Signal(dict)  # full plugin data dict
    delete_requested = Signal(dict)   # full plugin data dict

    def __init__(self, data: dict, installed: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("StoreCard")
        self._data = data
        self.setMinimumHeight(120)
        self.setMaximumHeight(160)
        self.setStyleSheet(
            f"QFrame#StoreCard {{"
            f"  background: {COLORS['bg_surface']};"
            f"  border: 1px solid {COLORS['border']};"
            f"  border-radius: 10px;"
            f"  margin: 2px 4px;"
            f"}}"
            f"QFrame#StoreCard:hover {{"
            f"  border-color: {COLORS['accent_dim']};"
            f"}}"
        )

        layout = QHBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)
        self.setLayout(layout)

        # Left: info
        info = QVBoxLayout()
        info.setSpacing(3)

        # Title + version
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_lbl = QLabel(data.get("title", "Unknown"))
        title_lbl.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-weight: 700; font-size: 14px;"
            f" font-family: 'Segoe UI';"
        )
        title_row.addWidget(title_lbl)

        ver = QLabel(data.get("version", ""))
        ver.setStyleSheet(
            f"color: {COLORS['accent']}; font-size: 10px; font-family: 'Segoe UI';"
            f" font-weight: 600;"
        )
        title_row.addWidget(ver)
        title_row.addStretch()
        info.addLayout(title_row)

        # Author
        author = QLabel(f"by {data.get('author', 'Unknown')}")
        author.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; font-family: 'Segoe UI';"
        )
        info.addWidget(author)

        # Description
        desc = QLabel(data.get("description", ""))
        desc.setWordWrap(True)
        desc.setMaximumHeight(40)
        desc.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px; font-family: 'Segoe UI';"
        )
        info.addWidget(desc)

        # Requirements + downloads
        reqs = data.get("requirements", [])
        req_text = ", ".join(reqs) if reqs else "None"
        downloads = data.get("downloads", 0)
        meta = QLabel(f"📥 {downloads:,}  •  Requires: {req_text}")
        meta.setStyleSheet(
            f"color: {COLORS['text_dim']}; font-size: 10px; font-family: 'Segoe UI';"
        )
        info.addWidget(meta)

        layout.addLayout(info, 1)

        # Right: install button
        right = QVBoxLayout()
        right.setAlignment(Qt.AlignCenter)

        if installed:
            installed_row = QHBoxLayout()
            installed_row.setSpacing(6)
            installed_lbl = QLabel("✓ Installed")
            installed_lbl.setStyleSheet(
                f"color: {COLORS['success']}; font-weight: 700; font-size: 11px;"
                f" font-family: 'Segoe UI';"
            )
            installed_row.addWidget(installed_lbl)

            del_btn = QPushButton("🗑")
            del_btn.setObjectName("DangerSmallButton")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setFixedWidth(32)
            del_btn.setToolTip("Delete installed plugin")
            del_btn.clicked.connect(lambda: self.delete_requested.emit(self._data))
            installed_row.addWidget(del_btn)

            right.addLayout(installed_row)
        else:
            install_btn = QPushButton("Install")
            install_btn.setObjectName("AccentButton")
            install_btn.setCursor(Qt.PointingHandCursor)
            install_btn.setFixedWidth(80)
            install_btn.clicked.connect(lambda: self.install_requested.emit(self._data))
            right.addWidget(install_btn)

        layout.addLayout(right)


class PluginStorePanel(QFrame):
    """Browse and install community plugins/scripts from the online store."""

    plugin_installed = Signal(str)  # plugin title
    plugin_deleted = Signal(str)    # plugin title

    def __init__(self, plugins_dir: str | None = None, title: str = "Plugin Store",
                 search_hint: str = "Search plugins\u2026", parent=None):
        super().__init__(parent)
        self.setObjectName("PluginStorePanel")
        self._plugins_dir = Path(plugins_dir) if plugins_dir else _PLUGINS_DIR
        self._plugins_dir.mkdir(exist_ok=True)
        self._store_title = title
        self._search_hint = search_hint
        self._all_scripts: list[dict] = []
        self._signals = _StoreSignals()
        self._signals.data_ready.connect(self._on_data)
        self._signals.fetch_error.connect(self._on_error)
        self._signals.download_done.connect(self._on_download_done)
        self._signals.download_error.connect(self._on_download_error)
        self._build()

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

        title = QLabel(f"🏪  {self._store_title}")
        title.setObjectName("PanelTitle")
        h_layout.addWidget(title)
        h_layout.addStretch()

        self._status_label = QLabel("")
        self._status_label.setStyleSheet(
            f"color: {COLORS['text_dim']}; font-size: 10px; font-family: 'Segoe UI';"
        )
        h_layout.addWidget(self._status_label)

        refresh_btn = QPushButton("↻ Refresh")
        refresh_btn.setObjectName("SmallButton")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.fetch_scripts)
        h_layout.addWidget(refresh_btn)

        layout.addWidget(header)

        # Search / filter bar
        filter_bar = QFrame()
        filter_bar.setObjectName("FilterBar")
        filter_bar.setFixedHeight(38)
        fb_layout = QHBoxLayout()
        fb_layout.setContentsMargins(12, 4, 12, 4)
        fb_layout.setSpacing(8)
        filter_bar.setLayout(fb_layout)

        self._search_input = QLineEdit()
        self._search_input.setObjectName("SearchInput")
        self._search_input.setPlaceholderText(f"🔍  {self._search_hint}")
        self._search_input.textChanged.connect(self._filter_cards)
        fb_layout.addWidget(self._search_input)

        layout.addWidget(filter_bar)

        # Scrollable card area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._cards_widget = QWidget()
        self._cards_layout = QVBoxLayout()
        self._cards_layout.setContentsMargins(8, 8, 8, 8)
        self._cards_layout.setSpacing(8)
        self._cards_layout.setAlignment(Qt.AlignTop)
        self._cards_widget.setLayout(self._cards_layout)
        scroll.setWidget(self._cards_widget)
        layout.addWidget(scroll, 1)

        # Loading message
        self._loading_label = QLabel("Click  ↻ Refresh  to load the plugin store…")
        self._loading_label.setAlignment(Qt.AlignCenter)
        self._loading_label.setStyleSheet(
            f"color: {COLORS['text_dim']}; font-size: 12px; padding: 40px;"
        )
        self._cards_layout.addWidget(self._loading_label)

    def fetch_scripts(self) -> None:
        """Fetch the plugin list from JSONBin API in a background thread."""
        self._status_label.setText("Fetching…")
        self._loading_label.setText("Loading plugins…")
        self._loading_label.setVisible(True)

        def _do_fetch():
            try:
                req = urllib_request.Request(_API_URL)
                req.add_header("User-Agent", "FluxusIDE/1.0")
                with urllib_request.urlopen(req, timeout=15) as resp:
                    raw = json.loads(resp.read().decode("utf-8"))
                # JSONBin wraps data in {"record": {...}}
                record = raw.get("record", raw)
                scripts = record.get("minescript_scripts", [])
                self._signals.data_ready.emit(scripts)
            except Exception as e:
                self._signals.fetch_error.emit(str(e))

        threading.Thread(target=_do_fetch, daemon=True).start()

    def _on_data(self, scripts: list) -> None:
        self._all_scripts = scripts
        self._status_label.setText(f"{len(scripts)} plugins")
        self._loading_label.setVisible(False)
        self._rebuild_cards(scripts)

    def _on_error(self, error: str) -> None:
        self._status_label.setText("Error")
        self._loading_label.setText(f"Failed to load: {error}")
        self._loading_label.setVisible(True)

    def _rebuild_cards(self, scripts: list) -> None:
        # Clear old cards (keep loading label if shown)
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        installed_names = set()
        if self._plugins_dir.exists():
            for f in self._plugins_dir.iterdir():
                if f.suffix in (".py", ".pyj"):
                    installed_names.add(f.stem.lower())

        for script in scripts:
            title = script.get("title", "").lower()
            is_installed = title in installed_names
            card = PluginStoreCard(script, installed=is_installed)
            card.install_requested.connect(self._install_script)
            card.delete_requested.connect(self._delete_plugin)
            self._cards_layout.addWidget(card)

        if not scripts:
            empty = QLabel("No plugins available.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(
                f"color: {COLORS['text_dim']}; font-size: 12px; padding: 40px;"
            )
            self._cards_layout.addWidget(empty)

    def _filter_cards(self, text: str) -> None:
        text = text.strip().lower()
        if not text:
            self._rebuild_cards(self._all_scripts)
            return
        filtered = [
            s for s in self._all_scripts
            if text in s.get("title", "").lower()
            or text in s.get("description", "").lower()
            or text in s.get("author", "").lower()
        ]
        self._rebuild_cards(filtered)

    def _install_script(self, data: dict) -> None:
        """Download and install a plugin (zip → extract to plugins/)."""
        url = data.get("download_url", "")
        title = data.get("title", "unknown")
        if not url:
            self._signals.download_error.emit(f"No download URL for '{title}'")
            return

        self._status_label.setText(f"Downloading {title}…")

        def _do_download():
            try:
                req = urllib_request.Request(url)
                req.add_header("User-Agent", "FluxusIDE/1.0")
                with urllib_request.urlopen(req, timeout=30) as resp:
                    content = resp.read()
                    content_type = resp.headers.get("Content-Type", "")

                # Try to extract as zip
                if self._try_extract_zip(content, title):
                    self._signals.download_done.emit(title)
                    return

                # If not a zip, save as .py directly
                dest = self._plugins_dir / f"{title}.py"
                dest.write_bytes(content)
                self._signals.download_done.emit(title)

            except Exception as e:
                self._signals.download_error.emit(f"{title}: {e}")

        threading.Thread(target=_do_download, daemon=True).start()

    def _try_extract_zip(self, content: bytes, title: str) -> bool:
        """Try to extract zip content. Returns True if successful."""
        try:
            bio = io.BytesIO(content)
            if not zipfile.is_zipfile(bio):
                return False
            bio.seek(0)
            with zipfile.ZipFile(bio, "r") as zf:
                # Extract .py and .pyj files to Scripts dir
                extracted = False
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    name = os.path.basename(info.filename)
                    if name.endswith((".py", ".pyj")):
                        dest = self._plugins_dir / name
                        dest.write_bytes(zf.read(info.filename))
                        extracted = True
                return extracted
        except Exception:
            return False

    def _on_download_done(self, title: str) -> None:
        self._status_label.setText(f"✓ Installed {title}")
        self.plugin_installed.emit(title)
        # Refresh cards to show "Installed" status
        if self._all_scripts:
            self._rebuild_cards(self._all_scripts)

    def _on_download_error(self, error: str) -> None:
        self._status_label.setText(f"✗ {error}")

    def _delete_plugin(self, data: dict) -> None:
        """Delete an installed plugin after confirmation."""
        title = data.get("title", "unknown")
        reply = QMessageBox.question(
            self, "Delete Plugin",
            f"Delete installed plugin '{title}'?\n\nThis removes the .py file from the plugins folder.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        # Remove matching .py / .pyj files
        for ext in (".py", ".pyj"):
            candidate = self._plugins_dir / f"{title}{ext}"
            if candidate.exists():
                candidate.unlink()
        self.plugin_deleted.emit(title)
        self._status_label.setText(f"Deleted {title}")
        if self._all_scripts:
            self._rebuild_cards(self._all_scripts)
