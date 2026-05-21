import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpacerItem, QSizePolicy, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QPainter, QLinearGradient, QColor, QBrush


class GradientWidget(QWidget):
    def __init__(self, color_start: str, color_end: str, parent=None):
        super().__init__(parent)
        self._color_start = QColor(color_start)
        self._color_end = QColor(color_end)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, self._color_start)
        gradient.setColorAt(1.0, self._color_end)
        painter.fillRect(self.rect(), QBrush(gradient))


class MainMenuWindow(QMainWindow):

    _BTN_STYLE = """
        QPushButton {
            background-color: #EBF5FF;
            color: #2C3E50;
            border: none;
            border-radius: 28px;
            padding: 14px 40px;
            font-size: 15px;
            font-style: italic;
            font-family: 'Segoe UI', 'Arial', sans-serif;
        }
        QPushButton:hover {
            background-color: #D0E8FA;
        }
        QPushButton:pressed {
            background-color: #B8D9F5;
        }
    """

    _WIN_BTN_BASE = """
        QPushButton {
            background-color: rgba(255, 255, 255, 40);
            color: #1B3A45;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-family: 'Segoe UI', 'Arial', sans-serif;
            padding: 0px;
        }
        QPushButton:hover {
            background-color: rgba(255, 255, 255, 90);
        }
        QPushButton:pressed {
            background-color: rgba(255, 255, 255, 130);
        }
    """

    _WIN_BTN_CLOSE = """
        QPushButton {
            background-color: rgba(255, 255, 255, 40);
            color: #1B3A45;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-family: 'Segoe UI', 'Arial', sans-serif;
            padding: 0px;
        }
        QPushButton:hover {
            background-color: rgba(220, 60, 60, 200);
            color: white;
        }
        QPushButton:pressed {
            background-color: rgba(180, 30, 30, 220);
            color: white;
        }
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(" ")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.showMaximized()

        self._auto_window = None
        self._manual_window = None
        self._drag_pos = QPoint()
        self._dragging = False

        self._build_ui()

    def _build_ui(self):
        central = GradientWidget("#BDD1D5", "#97B4BE")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        titlebar = QWidget()
        titlebar.setFixedHeight(44)
        titlebar.setStyleSheet("background: transparent;")
        titlebar.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        titlebar_layout = QHBoxLayout(titlebar)
        titlebar_layout.setContentsMargins(12, 6, 12, 6)
        titlebar_layout.setSpacing(6)
        titlebar_layout.addStretch()

        btn_minimize = QPushButton("—")
        btn_minimize.setFixedSize(32, 32)
        btn_minimize.setStyleSheet(self._WIN_BTN_BASE)
        btn_minimize.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_minimize.clicked.connect(self.showMinimized)

        self._btn_maximize = QPushButton("□")
        self._btn_maximize.setFixedSize(32, 32)
        self._btn_maximize.setStyleSheet(self._WIN_BTN_BASE)
        self._btn_maximize.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_maximize.clicked.connect(self._toggle_maximize)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(32, 32)
        btn_close.setStyleSheet(self._WIN_BTN_CLOSE)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.close)

        titlebar_layout.addWidget(btn_minimize)
        titlebar_layout.addWidget(self._btn_maximize)
        titlebar_layout.addWidget(btn_close)

        root_layout.addWidget(titlebar)

        center_wrapper = QWidget()
        center_wrapper.setStyleSheet("background: transparent;")
        center_wrapper_layout = QVBoxLayout(center_wrapper)
        center_wrapper_layout.setContentsMargins(0, 0, 0, 44)
        center_wrapper_layout.setSpacing(0)
        center_wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(" ")
        title_font = QFont("Segoe UI", 32)
        title_font.setBold(True)
        title_font.setItalic(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #1B3A45; background: transparent; letter-spacing: 1px;")
        content_layout.addWidget(title)

        content_layout.addSpacerItem(
            QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )

        subtitle = QLabel(" ")
        subtitle_font = QFont("Segoe UI", 11)
        subtitle_font.setItalic(True)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #2C4F5C; background: transparent;")
        content_layout.addWidget(subtitle)

        content_layout.addSpacerItem(
            QSpacerItem(0, 50, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )

        btn_auto = QPushButton("  Создать блок-схему по алгоритму")
        btn_auto.setMinimumSize(380, 56)
        btn_auto.setStyleSheet(self._BTN_STYLE)
        btn_auto.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_auto.clicked.connect(self._open_auto_mode)
        content_layout.addWidget(btn_auto)

        content_layout.addSpacerItem(
            QSpacerItem(0, 18, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )

        btn_manual = QPushButton("  Нарисовать блок-схему вручную")
        btn_manual.setMinimumSize(380, 56)
        btn_manual.setStyleSheet(self._BTN_STYLE)
        btn_manual.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_manual.clicked.connect(self._open_manual_mode)
        content_layout.addWidget(btn_manual)

        content_layout.addSpacerItem(
            QSpacerItem(0, 18, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )

        btn_exit = QPushButton("  Выход")
        btn_exit.setMinimumSize(380, 56)
        btn_exit.setStyleSheet(self._BTN_STYLE)
        btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exit.clicked.connect(self._exit_app)
        content_layout.addWidget(btn_exit)

        center_wrapper_layout.addWidget(content_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(center_wrapper, stretch=1)

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self._btn_maximize.setText("□")
        else:
            self.showMaximized()
            self._btn_maximize.setText("❐")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.position().y() <= 44:
                self._dragging = True
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            if self.isMaximized():
                self.showNormal()
                self._btn_maximize.setText("□")
                self._drag_pos = QPoint(self.width() // 2, 22)
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(event)

    def _open_auto_mode(self):
        from ui_auto_mode import AutoModeWindow
        if self._auto_window is None or not self._auto_window.isVisible():
            self._auto_window = AutoModeWindow(main_menu=self)
            self._auto_window.setGeometry(self.geometry())
            if self.isMaximized():
                self._auto_window.showMaximized()
            else:
                self._auto_window.setWindowState(self.windowState())
                self._auto_window.show()
        else:
            self._auto_window.raise_()
            self._auto_window.activateWindow()
        self.hide()

    def _open_manual_mode(self):
        from ui_manual_mode import ManualModeWindow
        if self._manual_window is None or not self._manual_window.isVisible():
            self._manual_window = ManualModeWindow(main_menu=self)
            self._manual_window.setGeometry(self.geometry())
            if self.isMaximized():
                self._manual_window.showMaximized()
            else:
                self._manual_window.setWindowState(self.windowState())
                self._manual_window.show()
        else:
            self._manual_window.raise_()
            self._manual_window.activateWindow()
        self.hide()

    def _exit_app(self):
        QApplication.quit()

    def _open_manual_mode_with_xml(self, xml_path: str = None):
        """
        Открывает ручной режим с загрузкой XML-файла.

        Args:
            xml_path: Путь к XML-файлу с блок-схемой
        """
        try:
            from ui_manual_mode import ManualModeWindow

            # Создаём новое окно ручного режима
            self._manual_window = ManualModeWindow(main_menu=self)
            self._manual_window.setGeometry(self.geometry())

            if self.isMaximized():
                self._manual_window.showMaximized()
            else:
                self._manual_window.setWindowState(self.windowState())
                self._manual_window.show()

            # Загружаем XML после того, как окно отобразилось
            if xml_path and Path(xml_path).exists():
                # Используем QTimer.singleShot для загрузки после отображения окна
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(100, lambda: self._manual_window.load_from_xml(xml_path))

            self.hide()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть ручной режим:\n{str(e)}")