from pathlib import Path
import ctypes
from ctypes import wintypes

from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget,
)

from ..Styling.theme import CENTER_TITLE, LOGO_TEXT, TOP_BAR_HEIGHT


class TopBar(QFrame):
    def __init__(self, root: QWidget):
        super().__init__(root)
        self.root = root
        self._drag_offset = QPoint()
        self._is_dragging = False
        self._is_pinned = False
        self._icons_dir = Path(__file__).resolve().parents[1] / "Icons"
        self._set_window_pos = self._build_set_window_pos()

        self.setObjectName("TopBar")
        self.setFixedHeight(TOP_BAR_HEIGHT)
        self._build_layout()

    def _build_layout(self) -> None:
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 6, 8, 6)
        layout.setSpacing(8)
        self.setLayout(layout)

        left = QWidget(self)
        left_layout = QHBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left.setLayout(left_layout)
        left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        logo = QLabel(LOGO_TEXT, left)
        logo.setObjectName("TopBarLogo")
        left_layout.addWidget(logo)

        center = QWidget(self)
        center_layout = QHBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        center.setLayout(center_layout)
        center.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        title = QLabel(CENTER_TITLE, center)
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("TopBarTitle")
        center_layout.addWidget(title)

        right = QWidget(self)
        right_layout = QHBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)
        right.setLayout(right_layout)
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        right_layout.addStretch(1)

        min_button = self._control_button("—")
        min_button.clicked.connect(self._minimize)
        right_layout.addWidget(min_button)

        self.max_button = self._control_button("▢")
        self.max_button.clicked.connect(self._toggle_maximize)
        right_layout.addWidget(self.max_button)

        self.pin_button = self._control_button("")
        self.pin_button.setObjectName("PinButton")
        self.pin_button.setProperty("pinned", False)
        self.pin_button.setToolTip("Pin Window")
        self.pin_button.setIconSize(QSize(16, 16))
        self._update_pin_icon()
        self.pin_button.clicked.connect(self._toggle_pin)
        right_layout.addWidget(self.pin_button)

        close_button = self._control_button("✕")
        close_button.setObjectName("CloseButton")
        close_button.clicked.connect(self.root.close)
        right_layout.addWidget(close_button)

        layout.addWidget(left)
        layout.addWidget(center)
        layout.addWidget(right)

    def _control_button(self, text: str) -> QPushButton:
        button = QPushButton(text, self)
        button.setObjectName("TopBarButton")
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedWidth(46)
        return button

    def _update_pin_icon(self) -> None:
        icon_name = "Topbar-Pin.svg" if self._is_pinned else "Topbar-Unpin.svg"
        icon_path = self._icons_dir / icon_name
        self.pin_button.setIcon(QIcon(str(icon_path)))

    def _minimize(self) -> None:
        self.root.showMinimized()

    def _toggle_maximize(self) -> None:
        state = self.root.windowState()
        is_expanded = bool(state & (Qt.WindowMaximized | Qt.WindowFullScreen))

        if is_expanded:
            self.root.showNormal()
        else:
            self.root.showMaximized()

        self._update_max_button_state()

    def _update_max_button_state(self) -> None:
        state = self.root.windowState()
        is_expanded = bool(state & (Qt.WindowMaximized | Qt.WindowFullScreen))
        self.max_button.setText("❐" if is_expanded else "▢")

    def _toggle_pin(self) -> None:
        self._is_pinned = not self._is_pinned
        if self._apply_windows_topmost(self._is_pinned):
            pass
        else:
            self.root.setWindowFlag(Qt.WindowStaysOnTopHint, self._is_pinned)
            self.root.show()
        self.pin_button.setProperty("pinned", self._is_pinned)
        self.pin_button.style().unpolish(self.pin_button)
        self.pin_button.style().polish(self.pin_button)
        self.pin_button.setToolTip("Unpin Window" if self._is_pinned else "Pin Window")
        self._update_pin_icon()

    def _build_set_window_pos(self):
        if not hasattr(ctypes, "windll"):
            return None

        set_window_pos = ctypes.windll.user32.SetWindowPos
        set_window_pos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint,
        ]
        set_window_pos.restype = wintypes.BOOL
        return set_window_pos

    def _apply_windows_topmost(self, is_topmost: bool) -> bool:
        if self._set_window_pos is None:
            return False

        hwnd = wintypes.HWND(int(self.root.winId()))
        HWND_TOPMOST = wintypes.HWND(-1)
        HWND_NOTOPMOST = wintypes.HWND(-2)
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOACTIVATE = 0x0010
        SWP_NOOWNERZORDER = 0x0200

        insert_after = HWND_TOPMOST if is_topmost else HWND_NOTOPMOST
        result = self._set_window_pos(
            hwnd,
            insert_after,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOOWNERZORDER,
        )
        return bool(result)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.root.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._is_dragging and not self.root.isMaximized():
            self.root.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._is_dragging = False
        super().mouseReleaseEvent(event)
