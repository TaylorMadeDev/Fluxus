"""
Discord Webhook system — send notifications, script outputs, errors, and
custom messages to Discord channels via webhook URLs.
"""

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QScrollArea,
    QSpinBox, QTextEdit, QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS

_CONFIG_PATH = Path(__file__).resolve().parents[3] / "fluxus_webhook.json"

# ── Defaults ───────────────────────────────────────────────────────

_DEFAULTS = {
    "webhook_url": "",
    "username": "Fluxus IDE",
    "avatar_url": "",
    "notify_script_run": True,
    "notify_script_finish": True,
    "notify_script_error": True,
    "notify_save": False,
    "auto_send_console": False,
    "embed_color": 8154863,  # #7c6aef as int
    "enabled": False,
}


def load_webhook_config() -> dict:
    try:
        if _CONFIG_PATH.exists():
            data = json.loads(_CONFIG_PATH.read_text("utf-8"))
            return {**_DEFAULTS, **data}
    except Exception:
        pass
    return dict(_DEFAULTS)


def save_webhook_config(cfg: dict) -> None:
    try:
        _CONFIG_PATH.write_text(json.dumps(cfg, indent=2), "utf-8")
    except Exception:
        pass


# ── Sender (threaded to avoid blocking UI) ─────────────────────────

class WebhookSender:
    """Thread-safe Discord webhook dispatcher."""

    def __init__(self):
        self._config = load_webhook_config()

    def reload(self):
        self._config = load_webhook_config()

    @property
    def enabled(self) -> bool:
        return bool(self._config.get("enabled")) and bool(self._config.get("webhook_url"))

    def send_embed(self, title: str, description: str, color: int = None,
                   fields: list[dict] = None, footer: str = None):
        """Send a Discord embed in a background thread."""
        if not self.enabled:
            return
        cfg = self._config
        embed = {
            "title": title,
            "description": description[:4000],
            "color": color or cfg.get("embed_color", 8154863),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if fields:
            embed["fields"] = fields[:25]
        if footer:
            embed["footer"] = {"text": footer}

        payload = {
            "username": cfg.get("username", "Fluxus IDE"),
            "embeds": [embed],
        }
        if cfg.get("avatar_url"):
            payload["avatar_url"] = cfg["avatar_url"]

        threading.Thread(target=self._post, args=(cfg["webhook_url"], payload), daemon=True).start()

    def send_message(self, content: str):
        """Send a plain text message."""
        if not self.enabled:
            return
        cfg = self._config
        payload = {
            "username": cfg.get("username", "Fluxus IDE"),
            "content": content[:2000],
        }
        if cfg.get("avatar_url"):
            payload["avatar_url"] = cfg["avatar_url"]

        threading.Thread(target=self._post, args=(cfg["webhook_url"], payload), daemon=True).start()

    # ── Event helpers ──────────────────────────────────────────────

    def on_script_run(self, script_name: str):
        if self._config.get("notify_script_run"):
            self.send_embed(
                "▶ Script Started",
                f"Running **{script_name}**",
                color=3447003,  # blue
                footer="Fluxus IDE",
            )

    def on_script_finish(self, script_name: str, exit_code: int):
        if self._config.get("notify_script_finish"):
            if exit_code == 0:
                self.send_embed(
                    "✅ Script Finished",
                    f"**{script_name}** completed successfully.",
                    color=3066993,  # green
                    footer="Fluxus IDE",
                )
            else:
                self.send_embed(
                    "⚠ Script Exited",
                    f"**{script_name}** exited with code **{exit_code}**.",
                    color=15105570,  # orange
                    footer="Fluxus IDE",
                )

    def on_script_error(self, script_name: str, error: str):
        if self._config.get("notify_script_error"):
            self.send_embed(
                "❌ Script Error",
                f"**{script_name}**\n```\n{error[:1800]}\n```",
                color=15158332,  # red
                footer="Fluxus IDE",
            )

    def on_save(self, file_path: str):
        if self._config.get("notify_save"):
            self.send_embed(
                "💾 File Saved",
                f"Saved **{os.path.basename(file_path)}**",
                color=8154863,
                footer="Fluxus IDE",
            )

    def send_console_output(self, script_name: str, output: str):
        if self._config.get("auto_send_console"):
            self.send_embed(
                "📋 Console Output",
                f"**{script_name}**\n```\n{output[:1800]}\n```",
                color=5793266,  # teal
                footer="Fluxus IDE",
            )

    @staticmethod
    def _post(url: str, payload: dict):
        try:
            import urllib.request
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json", "User-Agent": "Fluxus-IDE/0.1"},
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass  # fail silently


# ── Global sender instance ─────────────────────────────────────────

_sender: WebhookSender | None = None


def get_webhook_sender() -> WebhookSender:
    global _sender
    if _sender is None:
        _sender = WebhookSender()
    return _sender


# ── Settings panel widget ──────────────────────────────────────────

class DiscordWebhookPanel(QFrame):
    """Discord webhook configuration panel."""

    settings_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WebhookPanel")
        self._config = load_webhook_config()
        self._build()

    def _build(self):
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.setLayout(outer)

        # Header
        header = QFrame()
        header.setObjectName("WebhookHeader")
        header.setFixedHeight(44)
        h_lay = QHBoxLayout()
        h_lay.setContentsMargins(12, 0, 12, 0)
        h_lay.setSpacing(8)
        header.setLayout(h_lay)

        title = QLabel("🔔  Discord Webhook")
        title.setObjectName("PanelTitle")
        h_lay.addWidget(title)
        h_lay.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setObjectName("AccentButton")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save)
        h_lay.addWidget(save_btn)

        test_btn = QPushButton("Test")
        test_btn.setObjectName("SmallButton")
        test_btn.setCursor(Qt.PointingHandCursor)
        test_btn.clicked.connect(self._test)
        h_lay.addWidget(test_btn)

        outer.addWidget(header)

        # Scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("WebhookScroll")

        content = QWidget()
        form = QVBoxLayout()
        form.setContentsMargins(16, 12, 16, 12)
        form.setSpacing(12)
        content.setLayout(form)

        # Enable toggle
        self._enabled_cb = QCheckBox("Enable Discord Webhook")
        self._enabled_cb.setChecked(self._config.get("enabled", False))
        self._enabled_cb.setObjectName("SettingsCheckbox")
        form.addWidget(self._enabled_cb)

        # Webhook URL
        form.addWidget(self._section("Webhook URL"))
        self._url_input = QLineEdit()
        self._url_input.setObjectName("SettingsInput")
        self._url_input.setPlaceholderText("https://discord.com/api/webhooks/...")
        self._url_input.setText(self._config.get("webhook_url", ""))
        self._url_input.setEchoMode(QLineEdit.Password)
        form.addWidget(self._url_input)

        # Username
        form.addWidget(self._section("Bot Username"))
        self._username = QLineEdit()
        self._username.setObjectName("SettingsInput")
        self._username.setText(self._config.get("username", "Fluxus IDE"))
        form.addWidget(self._username)

        # Avatar URL
        form.addWidget(self._section("Avatar URL (optional)"))
        self._avatar = QLineEdit()
        self._avatar.setObjectName("SettingsInput")
        self._avatar.setPlaceholderText("https://example.com/avatar.png")
        self._avatar.setText(self._config.get("avatar_url", ""))
        form.addWidget(self._avatar)

        # Notification toggles
        form.addWidget(self._section("Notifications"))

        self._notify_run = QCheckBox("Script started")
        self._notify_run.setChecked(self._config.get("notify_script_run", True))
        form.addWidget(self._notify_run)

        self._notify_finish = QCheckBox("Script finished")
        self._notify_finish.setChecked(self._config.get("notify_script_finish", True))
        form.addWidget(self._notify_finish)

        self._notify_error = QCheckBox("Script errors")
        self._notify_error.setChecked(self._config.get("notify_script_error", True))
        form.addWidget(self._notify_error)

        self._notify_save = QCheckBox("File saved")
        self._notify_save.setChecked(self._config.get("notify_save", False))
        form.addWidget(self._notify_save)

        self._auto_console = QCheckBox("Auto-send console output")
        self._auto_console.setChecked(self._config.get("auto_send_console", False))
        form.addWidget(self._auto_console)

        # Custom message
        form.addWidget(self._section("Send Custom Message"))
        self._custom_msg = QPlainTextEdit()
        self._custom_msg.setObjectName("WebhookCustomMsg")
        self._custom_msg.setPlaceholderText("Type a message to send to Discord…")
        self._custom_msg.setFixedHeight(80)
        form.addWidget(self._custom_msg)

        send_btn = QPushButton("Send Message")
        send_btn.setObjectName("AccentButton")
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.clicked.connect(self._send_custom)
        form.addWidget(send_btn)

        form.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

    def _section(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("SettingsSectionLabel")
        return lbl

    def _gather(self) -> dict:
        return {
            "enabled": self._enabled_cb.isChecked(),
            "webhook_url": self._url_input.text().strip(),
            "username": self._username.text().strip() or "Fluxus IDE",
            "avatar_url": self._avatar.text().strip(),
            "notify_script_run": self._notify_run.isChecked(),
            "notify_script_finish": self._notify_finish.isChecked(),
            "notify_script_error": self._notify_error.isChecked(),
            "notify_save": self._notify_save.isChecked(),
            "auto_send_console": self._auto_console.isChecked(),
            "embed_color": self._config.get("embed_color", 8154863),
        }

    def _save(self):
        cfg = self._gather()
        save_webhook_config(cfg)
        self._config = cfg
        sender = get_webhook_sender()
        sender.reload()
        self.settings_changed.emit(cfg)

    def _test(self):
        self._save()
        sender = get_webhook_sender()
        sender.send_embed(
            "🧪 Test Notification",
            "If you see this, your Fluxus IDE webhook is working!",
            color=3066993,
            fields=[
                {"name": "Status", "value": "Connected", "inline": True},
                {"name": "IDE Version", "value": "v0.1", "inline": True},
            ],
            footer="Fluxus IDE — Test",
        )

    def _send_custom(self):
        msg = self._custom_msg.toPlainText().strip()
        if not msg:
            return
        self._save()
        sender = get_webhook_sender()
        sender.send_message(msg)
        self._custom_msg.clear()
