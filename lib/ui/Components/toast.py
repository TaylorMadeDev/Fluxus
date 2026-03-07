"""
Toast notification overlay — slides in from the right with smooth animations.
"""

from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve, QPoint,
    QParallelAnimationGroup,
)
from PySide6.QtWidgets import (
    QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS

_TOAST_LIFETIME_MS = 4000
_SLIDE_DURATION = 300
_FADE_OUT_DURATION = 250


class ToastWidget(QFrame):
    """A single animated toast notification."""

    def __init__(self, message: str, level: str = "info", parent=None):
        super().__init__(parent)
        self.setObjectName("ToastWidget")
        self.setFixedWidth(320)
        self.setMinimumHeight(48)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)

        color_map = {
            "info": COLORS["accent"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "error": COLORS["danger"],
        }
        border = color_map.get(level, COLORS["accent"])
        icon_map = {"info": "ℹ", "success": "✓", "warning": "⚠", "error": "✗"}
        icon = icon_map.get(level, "ℹ")

        self.setStyleSheet(
            f"QFrame#ToastWidget {{ background-color: {COLORS['bg_topbar']}; "
            f"border: 1px solid {border}; border-left: 4px solid {border}; "
            f"border-radius: 8px; }}"
        )

        lay = QHBoxLayout()
        lay.setContentsMargins(12, 8, 8, 8)
        lay.setSpacing(8)
        self.setLayout(lay)

        ic = QLabel(icon)
        ic.setStyleSheet(f"color: {border}; font-size: 16px; font-weight: 700;")
        ic.setFixedWidth(20)
        lay.addWidget(ic)

        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-family: 'Segoe UI'; font-size: 12px;"
        )
        lay.addWidget(msg, 1)

        close = QPushButton("✕")
        close.setFixedSize(20, 20)
        close.setCursor(Qt.PointingHandCursor)
        close.setStyleSheet(
            f"color: {COLORS['text_dim']}; background: transparent; border: none; font-size: 12px;"
        )
        close.clicked.connect(self._dismiss)
        lay.addWidget(close, 0, Qt.AlignTop)

        # Opacity effect for animations
        self._opacity_eff = QGraphicsOpacityEffect(self)
        self._opacity_eff.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_eff)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._dismiss)
        self._timer.start(_TOAST_LIFETIME_MS)

    def slide_in(self, target_x: int, target_y: int):
        """Animate slide from right + fade in."""
        start_x = target_x + 340  # off-screen right
        self.move(start_x, target_y)
        self.show()

        slide = QPropertyAnimation(self, b"pos")
        slide.setDuration(_SLIDE_DURATION)
        slide.setStartValue(QPoint(start_x, target_y))
        slide.setEndValue(QPoint(target_x, target_y))
        slide.setEasingCurve(QEasingCurve.OutCubic)

        fade = QPropertyAnimation(self._opacity_eff, b"opacity")
        fade.setDuration(_SLIDE_DURATION)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.OutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(slide)
        group.addAnimation(fade)
        group.start()
        self._enter_anim = group

    def _dismiss(self):
        """Fade out + slide right, then close."""
        # Slide off to the right
        cur = self.pos()
        target = QPoint(cur.x() + 340, cur.y())

        slide = QPropertyAnimation(self, b"pos")
        slide.setDuration(_FADE_OUT_DURATION)
        slide.setStartValue(cur)
        slide.setEndValue(target)
        slide.setEasingCurve(QEasingCurve.InCubic)

        fade = QPropertyAnimation(self._opacity_eff, b"opacity")
        fade.setDuration(_FADE_OUT_DURATION)
        fade.setStartValue(self._opacity_eff.opacity())
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.InCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(slide)
        group.addAnimation(fade)
        group.finished.connect(self.close)
        group.start()
        self._exit_anim = group


class ToastManager:
    """
    Manages a stack of toast notifications anchored to a parent widget.

    Usage::

        toasts = ToastManager(main_window)
        toasts.info("Script saved!")
        toasts.success("Job started")
        toasts.warning("Unsaved changes")
        toasts.error("Compile failed")
    """

    def __init__(self, parent: QWidget):
        self._parent = parent
        self._active: list[ToastWidget] = []

    def info(self, msg: str) -> None:
        self._show(msg, "info")

    def success(self, msg: str) -> None:
        self._show(msg, "success")

    def warning(self, msg: str) -> None:
        self._show(msg, "warning")

    def error(self, msg: str) -> None:
        self._show(msg, "error")

    def _show(self, msg: str, level: str) -> None:
        toast = ToastWidget(msg, level, self._parent)
        toast.destroyed.connect(lambda: self._remove(toast))
        self._active.append(toast)
        self._reposition_and_enter(toast)

    def _remove(self, toast: ToastWidget) -> None:
        if toast in self._active:
            self._active.remove(toast)
            self._reposition_active()

    def _reposition_and_enter(self, new_toast: ToastWidget) -> None:
        """Position existing toasts and slide the new one in (bottom-right)."""
        if not self._parent:
            return
        pr = self._parent.rect()
        global_bl = self._parent.mapToGlobal(pr.bottomRight())
        x = global_bl.x() - 340
        # Stack upward from bottom
        y = global_bl.y() - 20  # bottom margin
        for t in reversed(self._active):
            y -= t.sizeHint().height() + 8
            target_y = y
            if t is new_toast:
                t.slide_in(x, target_y)
            else:
                anim = QPropertyAnimation(t, b"pos")
                anim.setDuration(200)
                anim.setStartValue(t.pos())
                anim.setEndValue(QPoint(x, target_y))
                anim.setEasingCurve(QEasingCurve.OutCubic)
                anim.start()
                t._reposition_anim = anim

    def _reposition_active(self) -> None:
        """Re-stack all active toasts smoothly (bottom-right)."""
        if not self._parent:
            return
        pr = self._parent.rect()
        global_bl = self._parent.mapToGlobal(pr.bottomRight())
        x = global_bl.x() - 340
        y = global_bl.y() - 20
        for t in reversed(self._active):
            y -= t.sizeHint().height() + 8
            anim = QPropertyAnimation(t, b"pos")
            anim.setDuration(200)
            anim.setStartValue(t.pos())
            anim.setEndValue(QPoint(x, y))
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start()
            t._reposition_anim = anim
