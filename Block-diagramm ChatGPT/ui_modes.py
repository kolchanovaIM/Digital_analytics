from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel
)

from core_parser import (
    ParseError,
    NodeData,
    EdgeData
)

from ui_auto_mode import AutoModeWindow
from ui_manual_mode import ManualModeWindow


# =========================================================
# AUTO MODE WRAPPER
# =========================================================

class AutoMode(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        label = QLabel(
            "Режим автоматической генерации"
        )

        layout.addWidget(label)

        self.window = AutoModeWindow()
        self.window.show()


# =========================================================
# MANUAL MODE WRAPPER
# =========================================================

class ManualMode(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        label = QLabel(
            "Режим ручного рисования"
        )

        layout.addWidget(label)

        self.window = ManualModeWindow()
        self.window.show()


# =========================================================
# EXPORTS
# =========================================================

__all__ = [
    "AutoModeWindow",
    "ManualModeWindow",
    "ParseError",
    "NodeData",
    "EdgeData"
]