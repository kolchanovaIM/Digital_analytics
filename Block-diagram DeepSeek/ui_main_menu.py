from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QApplication
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent
from ui_auto_mode import AutoModeWindow
from ui_manual_mode import ManualModeWindow


class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedHeight(36)
        self._drag_pos = None
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(4)

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
        self.close_btn.clicked.connect(self.window().close)

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


class MainMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Главное меню")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(1024, 768)

        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title_bar = TitleBar(self)
        layout.addWidget(self.title_bar, alignment=Qt.AlignmentFlag.AlignTop)

        layout.addStretch()

        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(20)

        self.btn_auto = QPushButton("Создать блок-схему по алгоритму")
        self.btn_manual = QPushButton("Нарисовать блок-схему вручную")
        self.btn_exit = QPushButton("Выход")

        button_layout.addWidget(self.btn_auto)
        button_layout.addWidget(self.btn_manual)
        button_layout.addWidget(self.btn_exit)

        layout.addWidget(button_container, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        self.btn_auto.clicked.connect(self.open_auto_mode)
        self.btn_manual.clicked.connect(self.open_manual_mode)
        self.btn_exit.clicked.connect(QApplication.quit)

        self._apply_styles()

        self.auto_window = None
        self.manual_window = None

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #BDD1D5,
                    stop: 1 #97B4BE
                );
            }
            QWidget#centralWidget {
                background: transparent;
            }
            QPushButton {
                background-color: #EBF5FF;
                border: none;
                border-radius: 20px;
                color: #333333;
                font-style: italic;
                font-size: 18px;
                padding: 15px 30px;
            }
            QPushButton:hover {
                background-color: #D6ECFF;
            }
            QPushButton#windowControlButton {
                background: transparent;
                border: none;
                color: #444444;
                font-size: 18px;
                font-weight: bold;
                border-radius: 6px;
                font-style: normal;
                padding: 0px;
            }
            QPushButton#windowControlButton:hover {
                background: rgba(0, 0, 0, 0.08);
            }
        """)

        self.btn_auto.setStyleSheet("""
            QPushButton {
                background-color: #EBF5FF;
                border: none;
                border-radius: 20px;
                color: #333333;
                font-style: italic;
                font-size: 18px;
                padding: 15px 30px;
            }
            QPushButton:hover {
                background-color: #D6ECFF;
            }
        """)
        self.btn_manual.setStyleSheet(self.btn_auto.styleSheet())
        self.btn_exit.setStyleSheet(self.btn_auto.styleSheet())

    def open_auto_mode(self):
        self.auto_window = AutoModeWindow(self)
        self.auto_window.setGeometry(self.geometry())
        self.hide()
        self.auto_window.show()

    def open_manual_mode(self):
        self.manual_window = ManualModeWindow(self)
        self.manual_window.setGeometry(self.geometry())
        self.hide()
        self.manual_window.show()