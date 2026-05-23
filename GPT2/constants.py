from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PyQt6.QtCore import Qt, QPoint, QRect, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QPen, QBrush, QFont
from PyQt6.QtWidgets import (
    QWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QVBoxLayout,
)

WINDOW_BG = "#F5FBFC"
TITLE_GRADIENT_START = "#BDD1D5"
TITLE_GRADIENT_END = "#97B4BE"
TOOLBAR_BG = "rgba(221,238,243,0.95)"
GRID_COLOR = "#B4C8D0"
PROCESS_COLOR = "#FFFFFF"
DECISION_COLOR = "#FFFFFF"
IO_COLOR = "#FFFFFF"
TERMINAL_COLOR = "#FFFFFF"

# Цвет контура и элементов управления (можно оставить или настроить)
HANDLE_COLOR = "#1F6FB2"
SCENE_RECT = 5000
DEFAULT_ITEM_WIDTH = 140
DEFAULT_ITEM_HEIGHT = 60
DEFAULT_FONT_FAMILY = "Courier New"
DEFAULT_FONT_SIZE = 11

GRID_STEP = 20
SCENE_RECT = 10000
MIN_ZOOM = 0.05
MAX_ZOOM = 20.0
PREVIEW_MIN_SCALE = 0.2
PREVIEW_MAX_SCALE = 3.0
PREVIEW_SCALE_STEP = 1.2


class TitleBar(QWidget):
    minimizeRequested = pyqtSignal()
    maximizeRequested = pyqtSignal()
    closeRequested = pyqtSignal()

    def __init__(self, title: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._drag_pos: QPoint | None = None
        self._drag_active = False
        self._maximized = False
        self.setFixedHeight(42)
        self.setObjectName("TitleBar")
        self.setStyleSheet(
            f"""
            QWidget#TitleBar {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {TITLE_GRADIENT_START}, stop:1 {TITLE_GRADIENT_END});
            }}
            QToolButton {{
                border: none;
                background: transparent;
                color: #21414D;
                font-size: 14px;
                min-width: 28px;
                max-width: 28px;
                min-height: 24px;
                max-height: 24px;
                border-radius: 8px;
            }}
            QToolButton:hover {{
                background: rgba(255,255,255,0.35);
            }}
            QLabel {{
                color: #17333D;
                font-weight: 600;
            }}
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 8, 4)
        layout.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.title_label)
        layout.addStretch(1)

        self.btn_min = QToolButton(self)
        self.btn_min.setText("–")
        self.btn_min.clicked.connect(self.minimizeRequested.emit)
        layout.addWidget(self.btn_min)

        self.btn_max = QToolButton(self)
        self.btn_max.setText("□")
        self.btn_max.clicked.connect(self.maximizeRequested.emit)
        layout.addWidget(self.btn_max)

        self.btn_close = QToolButton(self)
        self.btn_close.setText("✕")
        self.btn_close.clicked.connect(self.closeRequested.emit)
        layout.addWidget(self.btn_close)

    def setTitle(self, title: str) -> None:
        self.title_label.setText(title)

    def setMaximizedState(self, maximized: bool) -> None:
        self._maximized = maximized
        self.btn_max.setText("❐" if maximized else "□")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_active and self._drag_pos is not None:
            window = self.window()
            if window is not None and not window.isMaximized():
                delta = event.globalPosition().toPoint() - self._drag_pos
                window.move(window.pos() + delta)
                self._drag_pos = event.globalPosition().toPoint()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_active = False
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.maximizeRequested.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class FramelessWindow(QWidget):
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinMaxButtonsHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(f"background: {WINDOW_BG};")
        self._title_bar = TitleBar(title, self)
        self._title_bar.minimizeRequested.connect(self.showMinimized)
        self._title_bar.maximizeRequested.connect(self.toggleMaximizeRestore)
        self._title_bar.closeRequested.connect(self.close)

        self._body = QFrame(self)
        self._body.setObjectName("BodyFrame")
        self._body.setStyleSheet("QFrame#BodyFrame { background: transparent; }")
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._title_bar)
        layout.addWidget(self._body, 1)

    @property
    def title_bar(self) -> TitleBar:
        return self._title_bar

    @property
    def body_layout(self) -> QVBoxLayout:
        return self._body_layout

    def setWindowTitleText(self, title: str) -> None:
        self.setWindowTitle(title)
        self._title_bar.setTitle(title)

    def toggleMaximizeRestore(self) -> None:
        if self.isMaximized():
            self.showNormal()
            self._title_bar.setMaximizedState(False)
        else:
            self.showMaximized()
            self._title_bar.setMaximizedState(True)

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            self._title_bar.setMaximizedState(self.isMaximized())
        super().changeEvent(event)


def base_font(family: str = DEFAULT_FONT_FAMILY, size: int = DEFAULT_FONT_SIZE) -> QFont:
    font = QFont(family, size)
    font.setStyleHint(QFont.StyleHint.TypeWriter)
    return font


def make_tool_button(text: str = "", tooltip: str = "", checkable: bool = False) -> QToolButton:
    btn = QToolButton()
    btn.setText(text)
    btn.setToolTip(tooltip)
    btn.setCheckable(checkable)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(
        """
        QToolButton {
            border: 1px solid rgba(55,80,90,0.25);
            background: rgba(255,255,255,0.72);
            border-radius: 12px;
            padding: 4px;
        }
        QToolButton:hover {
            background: rgba(255,255,255,0.95);
        }
        QToolButton:checked {
            background: rgba(149,180,190,0.45);
            border: 1px solid rgba(46,86,98,0.45);
        }
        """
    )
    return btn


def snap_value(value: float, step: int = GRID_STEP) -> float:
    return round(value / step) * step

