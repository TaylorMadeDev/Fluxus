"""
Fluxus animation utilities — reusable helpers for premium smooth feel.

Provides:
- Fade in/out for windows and widgets
- Slide transitions for page stacks
- Scale pulse on click
- Hover glow / lift via QGraphicsOpacityEffect + QPropertyAnimation
- Animated stacked widget with crossfade/slide
"""

from PySide6.QtCore import (
    QEasingCurve, QParallelAnimationGroup, QPoint, QPropertyAnimation,
    QRect, QSequentialAnimationGroup, Qt, QTimer, QAbstractAnimation,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QStackedWidget,
    QWidget,
)

# ── Duration presets ───────────────────────────────────────────────
DURATION_FAST = 120        # instant feel – hover / micro
DURATION_NORMAL = 220      # standard transition
DURATION_SMOOTH = 350      # page transitions, open/close
DURATION_SLOW = 500        # dramatic entrance

EASING_SMOOTH = QEasingCurve.OutCubic
EASING_BOUNCE = QEasingCurve.OutBack
EASING_SNAP = QEasingCurve.InOutQuad
EASING_DECEL = QEasingCurve.OutQuart


# ── Fade helpers ───────────────────────────────────────────────────

def _ensure_opacity_effect(widget: QWidget) -> QGraphicsOpacityEffect:
    """Get or install an opacity effect on the widget."""
    eff = widget.graphicsEffect()
    if not isinstance(eff, QGraphicsOpacityEffect):
        eff = QGraphicsOpacityEffect(widget)
        eff.setOpacity(1.0)
        widget.setGraphicsEffect(eff)
    return eff


def fade_in(widget: QWidget, duration: int = DURATION_SMOOTH,
            start: float = 0.0, end: float = 1.0,
            easing: QEasingCurve = EASING_SMOOTH,
            callback=None) -> QPropertyAnimation:
    """Animate widget opacity from *start* → *end*."""
    eff = _ensure_opacity_effect(widget)
    eff.setOpacity(start)
    widget.show()
    anim = QPropertyAnimation(eff, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(easing)
    if callback:
        anim.finished.connect(callback)
    anim.start()
    # prevent GC
    widget._flx_fade_anim = anim
    return anim


def fade_out(widget: QWidget, duration: int = DURATION_NORMAL,
             start: float = 1.0, end: float = 0.0,
             easing: QEasingCurve = EASING_SMOOTH,
             callback=None) -> QPropertyAnimation:
    """Animate widget opacity from *start* → *end*, optionally hide on finish."""
    eff = _ensure_opacity_effect(widget)
    eff.setOpacity(start)
    anim = QPropertyAnimation(eff, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(easing)
    if callback:
        anim.finished.connect(callback)
    anim.start()
    widget._flx_fade_anim = anim
    return anim


# ── Window open / close ───────────────────────────────────────────

def window_open_animation(window: QWidget, duration: int = DURATION_SMOOTH):
    """Fade window in using setWindowOpacity (avoids QPainter conflicts)."""
    window.setWindowOpacity(0.0)

    # Use a QTimeLine-style approach with QPropertyAnimation on a helper
    class _OpacityProxy:
        def __init__(self, w):
            self._w = w
            self._val = 0.0
        def _get(self): return self._val
        def _set(self, v):
            self._val = v
            self._w.setWindowOpacity(v)

    proxy = _OpacityProxy(window)
    # We can't animate a non-QObject, so use a QTimer step approach
    steps = max(1, duration // 16)  # ~60fps
    window._open_step = 0
    window._open_steps = steps

    def _tick():
        window._open_step += 1
        t = min(window._open_step / window._open_steps, 1.0)
        # ease-out cubic: 1 - (1-t)^3
        eased = 1.0 - (1.0 - t) ** 3
        window.setWindowOpacity(eased)
        if t >= 1.0:
            timer.stop()

    timer = QTimer(window)
    timer.setInterval(16)
    timer.timeout.connect(_tick)
    timer.start()
    window._flx_open_timer = timer
    return timer


def window_close_animation(window: QWidget, duration: int = DURATION_NORMAL,
                           callback=None):
    """Fade-out using setWindowOpacity, then call callback."""
    steps = max(1, duration // 16)
    window._close_step = 0
    window._close_steps = steps

    def _tick():
        window._close_step += 1
        t = min(window._close_step / window._close_steps, 1.0)
        # ease-in quad: t^2
        eased = 1.0 - t * t
        window.setWindowOpacity(eased)
        if t >= 1.0:
            timer.stop()
            if callback:
                callback()

    timer = QTimer(window)
    timer.setInterval(16)
    timer.timeout.connect(_tick)
    timer.start()
    window._flx_close_timer = timer
    return timer


# ── Hover shadow / glow ───────────────────────────────────────────

def install_hover_shadow(widget: QWidget, color: str = "#00000040",
                          blur_rest: int = 8, blur_hover: int = 20,
                          y_rest: int = 2, y_hover: int = 6):
    """
    Installs a QGraphicsDropShadowEffect that animates on enter/leave.
    Must be connected via eventFilter or enterEvent/leaveEvent.
    Returns (shadow_effect, animate_in_fn, animate_out_fn).
    """
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur_rest)
    shadow.setColor(QColor(color))
    shadow.setOffset(0, y_rest)
    widget.setGraphicsEffect(shadow)

    def animate_in():
        a1 = QPropertyAnimation(shadow, b"blurRadius")
        a1.setDuration(DURATION_FAST)
        a1.setStartValue(shadow.blurRadius())
        a1.setEndValue(blur_hover)
        a1.setEasingCurve(EASING_SMOOTH)
        a1.start()
        widget._flx_shadow_in = a1

        a2 = QPropertyAnimation(shadow, b"offset")
        a2.setDuration(DURATION_FAST)
        a2.setStartValue(shadow.offset())
        a2.setEndValue(QPoint(0, y_hover))
        a2.setEasingCurve(EASING_SMOOTH)
        a2.start()
        widget._flx_shadow_off_in = a2

    def animate_out():
        a1 = QPropertyAnimation(shadow, b"blurRadius")
        a1.setDuration(DURATION_FAST)
        a1.setStartValue(shadow.blurRadius())
        a1.setEndValue(blur_rest)
        a1.setEasingCurve(EASING_SMOOTH)
        a1.start()
        widget._flx_shadow_out = a1

        a2 = QPropertyAnimation(shadow, b"offset")
        a2.setDuration(DURATION_FAST)
        a2.setStartValue(shadow.offset())
        a2.setEndValue(QPoint(0, y_rest))
        a2.setEasingCurve(EASING_SMOOTH)
        a2.start()
        widget._flx_shadow_off_out = a2

    return shadow, animate_in, animate_out


# ── Animated Stacked Widget ───────────────────────────────────────

class AnimatedStackedWidget(QStackedWidget):
    """
    QStackedWidget replacement with smooth slide transitions.
    Uses position-based animation only (no opacity on complex pages)
    to avoid QPainter conflicts with child widget effects.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration = DURATION_NORMAL
        self._animating = False
        self._next_idx = -1

    def setCurrentIndex(self, index: int) -> None:  # noqa: N802
        if index == self.currentIndex() or self._animating:
            super().setCurrentIndex(index)
            return
        if index < 0 or index >= self.count():
            return

        current_widget = self.currentWidget()
        next_widget = self.widget(index)
        if not current_widget or not next_widget:
            super().setCurrentIndex(index)
            return

        self._animating = True
        self._next_idx = index

        # Direction: slide left or right based on index
        direction = 1 if index > self.currentIndex() else -1
        offset = int(self.width() * 0.06)  # subtle shift

        # Position next widget slightly off, then slide in
        next_widget.setGeometry(0, 0, self.width(), self.height())
        next_widget.show()
        next_widget.raise_()

        nxt_slide = QPropertyAnimation(next_widget, b"pos")
        nxt_slide.setDuration(self._duration)
        nxt_slide.setStartValue(QPoint(direction * offset, 0))
        nxt_slide.setEndValue(QPoint(0, 0))
        nxt_slide.setEasingCurve(EASING_DECEL)
        nxt_slide.finished.connect(self._on_transition_done)
        nxt_slide.start()
        self._flx_page_anim = nxt_slide

    def _on_transition_done(self):
        self._animating = False
        if self._next_idx >= 0:
            super().setCurrentIndex(self._next_idx)
            self._next_idx = -1


# ── Button press scale pulse ──────────────────────────────────────

class AnimatedButton:
    """
    Mixin-style helper — call install() on any QPushButton to add
    a subtle press scale animation.

    Usage::

        AnimatedButton.install(my_button)
    """

    @staticmethod
    def install(button):
        """Monkey-patch enter/leave/press/release events for micro-animations."""
        original_enter = button.enterEvent
        original_leave = button.leaveEvent
        original_press = button.mousePressEvent
        original_release = button.mouseReleaseEvent

        def _on_enter(event):
            _ensure_opacity_effect(button)
            a = QPropertyAnimation(button.graphicsEffect(), b"opacity")
            a.setDuration(DURATION_FAST)
            a.setStartValue(button.graphicsEffect().opacity())
            a.setEndValue(1.0)
            a.setEasingCurve(EASING_SMOOTH)
            a.start()
            button._flx_hover_anim = a
            original_enter(event)

        def _on_leave(event):
            eff = button.graphicsEffect()
            if isinstance(eff, QGraphicsOpacityEffect):
                a = QPropertyAnimation(eff, b"opacity")
                a.setDuration(DURATION_FAST)
                a.setStartValue(eff.opacity())
                a.setEndValue(0.85)
                a.setEasingCurve(EASING_SMOOTH)
                a.start()
                button._flx_hover_anim = a
            original_leave(event)

        def _on_press(event):
            # Quick opacity dip for tactile feel
            eff = button.graphicsEffect()
            if isinstance(eff, QGraphicsOpacityEffect):
                a = QPropertyAnimation(eff, b"opacity")
                a.setDuration(60)
                a.setStartValue(eff.opacity())
                a.setEndValue(0.6)
                a.setEasingCurve(QEasingCurve.InQuad)
                a.start()
                button._flx_press_anim = a
            original_press(event)

        def _on_release(event):
            eff = button.graphicsEffect()
            if isinstance(eff, QGraphicsOpacityEffect):
                a = QPropertyAnimation(eff, b"opacity")
                a.setDuration(DURATION_FAST)
                a.setStartValue(eff.opacity())
                a.setEndValue(1.0)
                a.setEasingCurve(EASING_BOUNCE)
                a.start()
                button._flx_release_anim = a
            original_release(event)

        # Set resting opacity slightly below 1 so hover "brightens"
        eff = _ensure_opacity_effect(button)
        eff.setOpacity(0.85)

        button.enterEvent = _on_enter
        button.leaveEvent = _on_leave
        button.mousePressEvent = _on_press
        button.mouseReleaseEvent = _on_release
