"""
ScriptCard — a visual card widget representing a single Minescript script.
Shows icon, name, version, description, author, tags, and action buttons.
"""

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QPointF
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS


class ScriptCard(QFrame):
    """A card widget that represents one script with its metadata."""

    run_clicked = Signal(str)        # script path
    edit_clicked = Signal(str)       # script path
    configure_clicked = Signal(str)  # script path
    toggle_clicked = Signal(str)     # script path
    delete_clicked = Signal(str)     # script path
    favorite_clicked = Signal(str)   # script path

    def __init__(self, script_path: str, meta: dict, parent=None):
        super().__init__(parent)
        self.script_path = script_path
        self.meta = meta
        self.setObjectName("ScriptCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._setup_shadow()
        self._build()

    def _setup_shadow(self):
        """Install an animated drop shadow for hover lift effect."""
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(6)
        self._shadow.setColor(QColor(0, 0, 0, 40))
        self._shadow.setOffset(0, 2)
        self.setGraphicsEffect(self._shadow)

    def enterEvent(self, event):
        # Lift up — increase shadow
        a1 = QPropertyAnimation(self._shadow, b"blurRadius")
        a1.setDuration(140)
        a1.setStartValue(self._shadow.blurRadius())
        a1.setEndValue(22)
        a1.setEasingCurve(QEasingCurve.OutCubic)
        a1.start()
        self._sa1 = a1

        a2 = QPropertyAnimation(self._shadow, b"offset")
        a2.setDuration(140)
        a2.setStartValue(self._shadow.offset())
        a2.setEndValue(QPointF(0, 6))
        a2.setEasingCurve(QEasingCurve.OutCubic)
        a2.start()
        self._sa2 = a2
        super().enterEvent(event)

    def leaveEvent(self, event):
        a1 = QPropertyAnimation(self._shadow, b"blurRadius")
        a1.setDuration(180)
        a1.setStartValue(self._shadow.blurRadius())
        a1.setEndValue(6)
        a1.setEasingCurve(QEasingCurve.OutCubic)
        a1.start()
        self._sa1 = a1

        a2 = QPropertyAnimation(self._shadow, b"offset")
        a2.setDuration(180)
        a2.setStartValue(self._shadow.offset())
        a2.setEndValue(QPointF(0, 2))
        a2.setEasingCurve(QEasingCurve.OutCubic)
        a2.start()
        self._sa2 = a2
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        # Quick dip on press
        a1 = QPropertyAnimation(self._shadow, b"blurRadius")
        a1.setDuration(60)
        a1.setStartValue(self._shadow.blurRadius())
        a1.setEndValue(3)
        a1.setEasingCurve(QEasingCurve.InQuad)
        a1.start()
        self._sa1 = a1

        a2 = QPropertyAnimation(self._shadow, b"offset")
        a2.setDuration(60)
        a2.setStartValue(self._shadow.offset())
        a2.setEndValue(QPointF(0, 1))
        a2.setEasingCurve(QEasingCurve.InQuad)
        a2.start()
        self._sa2 = a2
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        a1 = QPropertyAnimation(self._shadow, b"blurRadius")
        a1.setDuration(120)
        a1.setStartValue(self._shadow.blurRadius())
        a1.setEndValue(22)
        a1.setEasingCurve(QEasingCurve.OutBack)
        a1.start()
        self._sa1 = a1

        a2 = QPropertyAnimation(self._shadow, b"offset")
        a2.setDuration(120)
        a2.setStartValue(self._shadow.offset())
        a2.setEndValue(QPointF(0, 6))
        a2.setEasingCurve(QEasingCurve.OutBack)
        a2.start()
        self._sa2 = a2

        # If click was not on a button, open in editor
        child = self.childAt(event.position().toPoint())
        if not isinstance(child, QPushButton):
            self.edit_clicked.emit(self.script_path)

        super().mouseReleaseEvent(event)

    def _build(self) -> None:
        outer = QHBoxLayout()
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(14)
        self.setLayout(outer)

        # Icon
        icon_lbl = QLabel(self.meta.get("icon", "📜"))
        icon_lbl.setObjectName("CardIcon")
        icon_lbl.setFixedSize(48, 48)
        icon_lbl.setAlignment(Qt.AlignCenter)
        outer.addWidget(icon_lbl)

        # Favorite star + run count (vertical beside icon)
        fav_col = QVBoxLayout()
        fav_col.setContentsMargins(0, 0, 0, 0)
        fav_col.setSpacing(2)

        is_fav = self.meta.get("favorite", False)
        self._fav_btn = QPushButton("★" if is_fav else "☆")
        self._fav_btn.setObjectName("FavButton")
        self._fav_btn.setCursor(Qt.PointingHandCursor)
        self._fav_btn.setFixedSize(24, 24)
        self._fav_btn.setToolTip("Toggle favorite")
        self._fav_btn.setStyleSheet(
            f"color: {'#f5c842' if is_fav else COLORS.get('text_dim', '#6a6a8a')};"
            f" background: transparent; border: none; font-size: 16px;"
        )
        self._fav_btn.clicked.connect(lambda: self.favorite_clicked.emit(self.script_path))
        fav_col.addWidget(self._fav_btn, 0, Qt.AlignCenter)

        run_count = self.meta.get("run_count", 0)
        if run_count > 0:
            rc_lbl = QLabel(f"▶{run_count}")
            rc_lbl.setObjectName("RunCountLabel")
            rc_lbl.setToolTip(f"Run {run_count} time{'s' if run_count != 1 else ''}")
            rc_lbl.setStyleSheet(
                f"color: {COLORS.get('text_dim', '#6a6a8a')};"
                f" font-size: 9px; background: transparent;"
            )
            rc_lbl.setAlignment(Qt.AlignCenter)
            fav_col.addWidget(rc_lbl, 0, Qt.AlignCenter)

        fav_col.addStretch()
        outer.addLayout(fav_col)

        # Center: name, description, tags
        center = QVBoxLayout()
        center.setContentsMargins(0, 0, 0, 0)
        center.setSpacing(3)

        # Name + version row
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_lbl = QLabel(self.meta.get("name", "Untitled"))
        name_lbl.setObjectName("CardName")
        name_row.addWidget(name_lbl)

        ver_lbl = QLabel(f"v{self.meta.get('version', '1.0.0')}")
        ver_lbl.setObjectName("CardVersion")
        name_row.addWidget(ver_lbl)
        name_row.addStretch()

        # Enabled badge
        enabled = self.meta.get("enabled", True)
        badge = QLabel("Active" if enabled else "Disabled")
        badge.setObjectName("CardBadgeActive" if enabled else "CardBadgeDisabled")
        name_row.addWidget(badge)
        center.addLayout(name_row)

        # Description
        desc = self.meta.get("description", "")
        if desc:
            desc_lbl = QLabel(desc)
            desc_lbl.setObjectName("CardDescription")
            desc_lbl.setWordWrap(True)
            desc_lbl.setMaximumHeight(34)
            center.addWidget(desc_lbl)

        # Tags + author row
        info_row = QHBoxLayout()
        info_row.setSpacing(6)
        author = self.meta.get("author", "")
        if author:
            auth_lbl = QLabel(f"by {author}")
            auth_lbl.setObjectName("CardAuthor")
            info_row.addWidget(auth_lbl)

        tags = self.meta.get("tags", [])
        for tag in tags[:4]:
            tag_lbl = QLabel(tag)
            tag_lbl.setObjectName("CardTag")
            info_row.addWidget(tag_lbl)

        info_row.addStretch()
        center.addLayout(info_row)

        outer.addLayout(center, 1)

        # Action buttons (vertical stack)
        actions = QVBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(4)

        run_btn = QPushButton("▶ Run")
        run_btn.setObjectName("CardRunButton")
        run_btn.setCursor(Qt.PointingHandCursor)
        run_btn.setFixedWidth(80)
        run_btn.clicked.connect(lambda: self.run_clicked.emit(self.script_path))
        actions.addWidget(run_btn)

        edit_btn = QPushButton("✏ Edit")
        edit_btn.setObjectName("CardConfigButton")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setFixedWidth(80)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.script_path))
        actions.addWidget(edit_btn)

        cfg_btn = QPushButton("⚙ Params")
        cfg_btn.setObjectName("CardConfigButton")
        cfg_btn.setCursor(Qt.PointingHandCursor)
        cfg_btn.setFixedWidth(80)
        cfg_btn.clicked.connect(lambda: self.configure_clicked.emit(self.script_path))
        actions.addWidget(cfg_btn)

        del_btn = QPushButton("🗑")
        del_btn.setObjectName("CardDangerButton")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setFixedWidth(80)
        del_btn.setToolTip("Delete script")
        del_btn.clicked.connect(lambda: self.delete_clicked.emit(self.script_path))
        actions.addWidget(del_btn)

        outer.addLayout(actions)

    def update_meta(self, meta: dict) -> None:
        """Replace meta and rebuild (simple approach)."""
        self.meta = meta
        # Remove all children and rebuild
        while self.layout().count():
            child = self.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                _clear_layout(child.layout())
        self._build()


def _clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
        elif child.layout():
            _clear_layout(child.layout())
