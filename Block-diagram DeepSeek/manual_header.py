# manual_header.py
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QToolButton, QMenu, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMouseEvent


class HeaderBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("headerBar")
        self.setFixedHeight(36)
        self._drag_pos = None
        self.parent_window = parent

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(4)

        # Используем обычный QPushButton вместо QToolButton
        self.menu_btn = QPushButton("☰")
        self.menu_btn.setFixedSize(34, 34)
        self.menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #444444;
                font-size: 18px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(0,0,0,0.08);
            }
        """)
        layout.addWidget(self.menu_btn)

        layout.addStretch()

        self.minimize_btn = QPushButton("–")
        self.maximize_btn = QPushButton("🗖")
        self.close_btn = QPushButton("✕")

        for btn in (self.minimize_btn, self.maximize_btn, self.close_btn):
            btn.setFixedSize(34, 34)
            btn.setObjectName("windowControlButton")
            layout.addWidget(btn)

        self.minimize_btn.setStyleSheet(self._base_style())
        self.maximize_btn.setStyleSheet(self._base_style())
        self.close_btn.setStyleSheet(self._close_style())

        self.minimize_btn.clicked.connect(self.window().showMinimized)
        self.maximize_btn.clicked.connect(self._toggle_maximize)
        self.close_btn.clicked.connect(QApplication.instance().quit)

    def _base_style(self):
        return """
            QPushButton {
                background: rgba(255, 255, 255, 0);
                border: none;
                color: #444444;
                font-size: 18px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(0, 0, 0, 0.08);
            }
        """

    def _close_style(self):
        return """
            QPushButton {
                background: rgba(255, 255, 255, 0);
                border: none;
                color: #444444;
                font-size: 18px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(232, 17, 35, 0.9);
                color: white;
            }
        """

    def _toggle_maximize(self):
        win = self.window()
        if win.isMaximized():
            win.showNormal()
            self.maximize_btn.setText("🗖")
        else:
            win.showMaximized()
            self.maximize_btn.setText("🗗")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if not win.isMaximized():
                self._drag_pos = event.globalPosition().toPoint() - win.pos()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos is not None:
            win = self.window()
            if not win.isMaximized():
                win.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        super().mouseReleaseEvent(event)