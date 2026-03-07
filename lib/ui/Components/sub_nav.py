"""
SubNavPage — horizontal tab bar that groups related panels under one sidebar entry.
Each sidebar category maps to a SubNavPage containing a row of tab buttons + stacked content.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS


class SubNavButton(QPushButton):
    """Single button in the horizontal sub-nav strip."""

    def __init__(self, label: str, tag: str, parent=None):
        super().__init__(label, parent)
        self.tag = tag
        self.setObjectName("SubNavButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setFixedHeight(32)


class SubNavBar(QFrame):
    """Horizontal strip of tab buttons for switching sub-pages."""

    tab_changed = Signal(str)  # tag of the selected tab

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SubNavBar")
        self.setFixedHeight(38)
        self._buttons: list[SubNavButton] = []

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(12, 4, 12, 0)
        self._layout.setSpacing(2)
        self.setLayout(self._layout)

    def add_tab(self, icon: str, label: str, tag: str) -> SubNavButton:
        btn = SubNavButton(f"{icon}  {label}", tag, self)
        btn.clicked.connect(lambda checked, t=tag: self._on_click(t))
        self._buttons.append(btn)
        self._layout.addWidget(btn)
        return btn

    def finalize(self) -> None:
        """Call after adding all tabs to add trailing stretch."""
        self._layout.addStretch()

    def _on_click(self, tag: str) -> None:
        self.select(tag)
        self.tab_changed.emit(tag)

    def select(self, tag: str) -> None:
        for btn in self._buttons:
            btn.setChecked(btn.tag == tag)

    @property
    def tags(self) -> list[str]:
        return [b.tag for b in self._buttons]


class SubNavPage(QFrame):
    """
    A page containing a horizontal sub-nav bar and a stacked widget.
    Drop-in replacement for a single stacked page — each sidebar category
    gets one SubNavPage in the main page stack.
    """

    sub_page_changed = Signal(str)  # tag of active sub-page

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SubNavPage")
        self._tag_map: dict[str, int] = {}

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self._nav = SubNavBar(self)
        layout.addWidget(self._nav)

        self._stack = QStackedWidget(self)
        self._stack.setObjectName("SubNavStack")
        layout.addWidget(self._stack, 1)

        self._nav.tab_changed.connect(self._switch)

    def add_sub_page(self, icon: str, label: str, tag: str, widget: QWidget) -> None:
        """Add a widget as a sub-page with a tab button."""
        idx = self._stack.addWidget(widget)
        self._tag_map[tag] = idx
        self._nav.add_tab(icon, label, tag)

    def finalize(self) -> None:
        """Call after adding all sub-pages."""
        self._nav.finalize()
        if self._nav.tags:
            self._nav.select(self._nav.tags[0])
            self._stack.setCurrentIndex(0)

    def _switch(self, tag: str) -> None:
        idx = self._tag_map.get(tag, 0)
        self._stack.setCurrentIndex(idx)
        self.sub_page_changed.emit(tag)

    def select_sub_page(self, tag: str) -> None:
        """Programmatically switch to a sub-page."""
        self._nav.select(tag)
        self._switch(tag)

    def current_tag(self) -> str:
        for tag, idx in self._tag_map.items():
            if idx == self._stack.currentIndex():
                return tag
        return ""
