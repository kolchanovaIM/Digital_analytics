from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QApplication,
    QHBoxLayout
)

from ui_auto_mode import AutoModeWindow
from ui_manual_mode import ManualModeWindow


class MainMenu(QWidget):

    def __init__(self):

        super().__init__()

        self.drag_pos = QPoint()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
        )

        self.resize(1280, 720)

        self.setStyleSheet("""
            QWidget{
                background:qlineargradient(
                    x1:0,
                    y1:0,
                    x2:1,
                    y2:1,
                    stop:0 #BDD1D5,
                    stop:1 #A9C0C8
                );
            }
        """)

        self.setup_ui()

    # =====================================================
    # UI
    # =====================================================

    def setup_ui(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # =========================================
        # TOP BAR
        # =========================================

        top = QWidget()

        top.setFixedHeight(52)

        top.setStyleSheet("""
            background:transparent;
        """)

        top_layout = QHBoxLayout(top)

        top_layout.setContentsMargins(
            12,
            8,
            12,
            8
        )

        # MENU ICON

        menu_btn = QPushButton("☰")

        menu_btn.setFixedSize(42, 36)

        menu_btn.setStyleSheet("""
            QPushButton{
                background:transparent;
                border:none;
                color:#6E7E84;
                font-size:28px;
                font-weight:600;
            }
        """)

        top_layout.addWidget(menu_btn)

        top_layout.addStretch()

        # WINDOW BUTTONS

        for text, callback in [
            ("—", self.showMinimized),
            ("□", self.toggle_max),
            ("✕", self.close)
        ]:

            btn = QPushButton(text)

            btn.setFixedSize(34, 28)

            btn.setStyleSheet("""
                QPushButton{
                    background:rgba(255,255,255,0.45);
                    border:none;
                    border-radius:10px;
                    color:#3A4E55;
                    font-size:15px;
                }

                QPushButton:hover{
                    background:white;
                }
            """)

            btn.clicked.connect(callback)

            top_layout.addWidget(btn)

        root.addWidget(top)

        # =========================================
        # CENTER
        # =========================================

        center = QWidget()

        center_layout = QVBoxLayout(center)

        center_layout.setSpacing(28)

        center_layout.setContentsMargins(
            0,
            80,
            0,
            0
        )

        center_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop
        )

        # =========================================
        # BUTTONS
        # =========================================

        buttons = [
            (
                "Создать блок-схему по\nалгоритму",
                self.open_auto
            ),
            (
                "Нарисовать блок-схему\nвручную",
                self.open_manual
            ),
            (
                "Выход",
                QApplication.quit
            )
        ]

        for text, callback in buttons:

            btn = QPushButton(text)

            btn.setFixedSize(540, 96)

            btn.setFont(
                QFont(
                    "Segoe UI",
                    20,
                    QFont.Weight.Medium
                )
            )

            btn.setStyleSheet("""
                QPushButton{
                    background:#E8F0F6;
                    border:none;
                    border-radius:48px;
                    color:black;
                    padding:8px;
                    text-align:center;
                }

                QPushButton:hover{
                    background:#DCEAF3;
                }

                QPushButton:pressed{
                    background:#D1E2EE;
                }
            """)

            btn.clicked.connect(callback)

            center_layout.addWidget(
                btn,
                alignment=Qt.AlignmentFlag.AlignHCenter
            )

        root.addWidget(center)

    # =====================================================
    # OPEN WINDOWS
    # =====================================================

    def open_auto(self):

        self.window = AutoModeWindow()

        self.window.show()

    def open_manual(self):

        self.window = ManualModeWindow()

        self.window.show()

    # =====================================================
    # WINDOW CONTROL
    # =====================================================

    def toggle_max(self):

        if self.isMaximized():

            self.showNormal()

        else:

            self.showMaximized()

    # =====================================================
    # DRAG
    # =====================================================

    def mousePressEvent(self, event):

        if (
            event.button()
            == Qt.MouseButton.LeftButton
        ):

            self.drag_pos = (
                event.globalPosition().toPoint()
            )

    def mouseMoveEvent(self, event):

        if (
            event.buttons()
            == Qt.MouseButton.LeftButton
        ):

            delta = (
                event.globalPosition().toPoint()
                - self.drag_pos
            )

            self.move(
                self.pos() + delta
            )

            self.drag_pos = (
                event.globalPosition().toPoint()
            )