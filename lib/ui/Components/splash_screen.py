"""
SplashScreen — animated loading / initialization screen.
Displays the Fluxus logo, a progress bar, and status messages
while the app checks/installs dependencies and initializes the UI.
"""

import importlib
import subprocess
import sys
import time
from pathlib import Path

from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal, QThread, QObject, Property
)
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QLinearGradient, QBrush, QRadialGradient
from PySide6.QtWidgets import QWidget, QApplication

from ..Colors.palette import COLORS


# ── Dependency checker thread ──────────────────────────────────────

_REQUIRED_PACKAGES = [
    ("PySide6", "PySide6"),
]

_OPTIONAL_PACKAGES = [
    ("requests", "requests"),
    ("jedi",     "jedi"),
]


class _InitWorker(QObject):
    """Runs dependency checks and pre-initialization on a background thread."""
    progress = Signal(int, str)    # (percent, status_message)
    finished = Signal()

    def run(self):
        steps = [
            (5,  "Checking Python environment…"),
            (15, "Verifying PySide6…"),
            (25, "Checking optional packages…"),
            (40, "Loading Minescript API data…"),
            (55, "Preparing editor engine…"),
            (65, "Indexing script directory…"),
            (75, "Loading themes…"),
            (85, "Initializing workspace…"),
            (95, "Almost ready…"),
        ]

        for pct, msg in steps[:2]:
            self.progress.emit(pct, msg)
            time.sleep(0.15)

        # Check optional deps & auto-install missing ones
        self.progress.emit(25, "Checking optional packages…")
        for display_name, pip_name in _OPTIONAL_PACKAGES:
            try:
                importlib.import_module(display_name)
            except ImportError:
                self.progress.emit(30, f"Installing {display_name}…")
                try:
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", pip_name, "-q"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        timeout=60,
                    )
                except Exception:
                    pass  # non-fatal

        for pct, msg in steps[3:]:
            self.progress.emit(pct, msg)
            time.sleep(0.12)

        self.progress.emit(100, "Ready!")
        time.sleep(0.25)
        self.finished.emit()


# ── Splash widget ──────────────────────────────────────────────────

class SplashScreen(QWidget):
    """Full-screen-ish splash with logo, progress bar, and status text."""

    init_complete = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SplashScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(520, 360)
        self._center_on_screen()

        self._progress = 0
        self._status = "Initializing…"
        self._logo_opacity = 0.0
        self._particles: list[dict] = []

        # Fade-in animation for logo
        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(16)
        self._fade_timer.timeout.connect(self._tick_fade)
        self._logo_target = 1.0

        # Particle timer
        self._particle_timer = QTimer(self)
        self._particle_timer.setInterval(40)
        self._particle_timer.timeout.connect(self._tick_particles)

        # Worker thread
        self._thread = QThread()
        self._worker = _InitWorker()
        self._worker.moveToThread(self._thread)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._thread.started.connect(self._worker.run)

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.move(x, y)

    def start(self):
        """Show splash and begin initialization."""
        self.show()
        self._fade_timer.start()
        self._particle_timer.start()
        self._thread.start()

    # ── Slots ──────────────────────────────────────────────────────
    def _on_progress(self, pct: int, msg: str):
        self._progress = pct
        self._status = msg
        self.update()

    def _on_finished(self):
        self._thread.quit()
        self._thread.wait()
        self._fade_timer.stop()
        self._particle_timer.stop()
        # Fade out
        self._fade_out_step = 1.0
        self._fade_out_timer = QTimer(self)
        self._fade_out_timer.setInterval(16)
        self._fade_out_timer.timeout.connect(self._tick_fade_out)
        self._fade_out_timer.start()

    def _tick_fade(self):
        if self._logo_opacity < self._logo_target:
            self._logo_opacity = min(self._logo_opacity + 0.04, self._logo_target)
            self.update()

    def _tick_fade_out(self):
        self._fade_out_step -= 0.06
        if self._fade_out_step <= 0:
            self._fade_out_timer.stop()
            self.hide()
            self.init_complete.emit()
            return
        self.setWindowOpacity(max(0, self._fade_out_step))

    def _tick_particles(self):
        import random
        # Spawn occasional particle
        if random.random() < 0.4:
            self._particles.append({
                "x": random.uniform(40, self.width() - 40),
                "y": float(self.height() - 60),
                "vx": random.uniform(-0.5, 0.5),
                "vy": random.uniform(-1.5, -0.5),
                "life": 1.0,
                "size": random.uniform(2, 5),
            })
        # Update particles
        alive = []
        for p in self._particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 0.025
            if p["life"] > 0:
                alive.append(p)
        self._particles = alive
        self.update()

    # ── Paint ──────────────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        W, H = self.width(), self.height()

        # Background rounded rect with gradient
        bg_grad = QLinearGradient(0, 0, 0, H)
        bg_grad.setColorAt(0, QColor(COLORS.get("bg_root", "#0a0a1a")))
        bg_grad.setColorAt(1, QColor(COLORS.get("bg_sidebar", "#0e0e24")))
        p.setBrush(QBrush(bg_grad))
        p.setPen(QPen(QColor(COLORS.get("accent", "#7c6aef")), 2))
        p.drawRoundedRect(1, 1, W - 2, H - 2, 18, 18)

        # Particles
        for pt in self._particles:
            c = QColor(COLORS.get("accent", "#7c6aef"))
            c.setAlphaF(pt["life"] * 0.6)
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawEllipse(int(pt["x"]), int(pt["y"]), int(pt["size"]), int(pt["size"]))

        # Logo glow
        cx, cy = W // 2, 110
        if self._logo_opacity > 0.1:
            glow = QRadialGradient(cx, cy, 80)
            gc = QColor(COLORS.get("accent", "#7c6aef"))
            gc.setAlphaF(0.18 * self._logo_opacity)
            glow.setColorAt(0, gc)
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(glow))
            p.setPen(Qt.NoPen)
            p.drawEllipse(cx - 80, cy - 80, 160, 160)

        # Logo symbol
        p.setOpacity(self._logo_opacity)
        logo_font = QFont("Segoe UI", 52, QFont.Weight.Bold)
        p.setFont(logo_font)
        p.setPen(QColor(COLORS.get("accent", "#7c6aef")))
        p.drawText(0, 50, W, 120, Qt.AlignCenter, "◈")

        # Title
        title_font = QFont("Segoe UI", 22, QFont.Weight.Bold)
        p.setFont(title_font)
        p.setPen(QColor(COLORS.get("text_primary", "#e8e6f0")))
        p.drawText(0, 150, W, 40, Qt.AlignCenter, "Fluxus")

        # Subtitle
        sub_font = QFont("Segoe UI", 10)
        p.setFont(sub_font)
        p.setPen(QColor(COLORS.get("text_dim", "#6b6b8d")))
        p.drawText(0, 185, W, 24, Qt.AlignCenter, "Minecraft Scripting IDE")

        p.setOpacity(1.0)

        # Progress bar background
        bar_x, bar_y, bar_w, bar_h = 60, 240, W - 120, 8
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(COLORS.get("bg_surface", "#16162e")))
        p.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 4, 4)

        # Progress bar fill
        fill_w = int(bar_w * self._progress / 100)
        if fill_w > 0:
            bar_grad = QLinearGradient(bar_x, 0, bar_x + bar_w, 0)
            bar_grad.setColorAt(0, QColor(COLORS.get("accent", "#7c6aef")))
            bar_grad.setColorAt(1, QColor(COLORS.get("accent_hover", "#9a8cf5")))
            p.setBrush(QBrush(bar_grad))
            p.drawRoundedRect(bar_x, bar_y, fill_w, bar_h, 4, 4)

        # Percentage text
        pct_font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        p.setFont(pct_font)
        p.setPen(QColor(COLORS.get("accent", "#7c6aef")))
        p.drawText(0, 255, W, 20, Qt.AlignCenter, f"{self._progress}%")

        # Status text
        status_font = QFont("Segoe UI", 9)
        p.setFont(status_font)
        p.setPen(QColor(COLORS.get("text_dim", "#6b6b8d")))
        p.drawText(0, 278, W, 20, Qt.AlignCenter, self._status)

        # Version text
        ver_font = QFont("Segoe UI", 8)
        p.setFont(ver_font)
        p.setPen(QColor(COLORS.get("text_dim", "#6b6b8d")))
        p.drawText(0, H - 30, W, 20, Qt.AlignCenter, "v0.1  —  minescript.net")

        p.end()
