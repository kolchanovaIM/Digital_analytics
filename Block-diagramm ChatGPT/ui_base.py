from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QLinearGradient, QColor, QPalette, QBrush
from constants import BACKGROUND_START, BACKGROUND_END, TEXT_DARK

class FramelessWindow(QWidget):
    """Базовое кастомное окно без стандартной системной рамки ОС с поддержкой Drag-n-Drop."""
    def __init__(self, title_text="Конструктор"):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.resize(1024, 768)
        self._drag_position = QPoint()

        # Главный контейнер
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Кастомный заголовок (Градиент)
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(40)
        tb_layout = QHBoxLayout(self.title_bar)
        tb_layout.setContentsMargins(15, 0, 10, 0)

        self.title_label = QLabel(title_text)
        self.title_label.setStyleSheet(f"color: {TEXT_DARK}; font-weight: bold; font-family: Arial; font-size: 13px;")
        tb_layout.addWidget(self.title_label)
        tb_layout.addStretch()

        # Кнопки управления окном
        btn_style = "QPushButton { border: none; background: transparent; font-size: 14px; width: 30px; height: 30px; } QPushButton:hover { background-color: rgba(255,255,255,0.3); }"
        self.btn_minimize = QPushButton("—")
        self.btn_minimize.setStyleSheet(btn_style)
        self.btn_minimize.clicked.connect(self.showMinimized)
        tb_layout.addWidget(self.btn_minimize)

        self.btn_close = QPushButton("✕")
        self.btn_close.setStyleSheet("QPushButton { border: none; background: transparent; font-size: 14px; width: 30px; height: 30px; } QPushButton:hover { background-color: #E81123; color: white; }")
        self.btn_close.clicked.connect(self.close)
        tb_layout.addWidget(self.btn_close)

        self.main_layout.addWidget(self.title_bar)

        # Установка градиентного фона заголовка
        palette = self.title_bar.palette()
        gradient = QLinearGradient(0, 0, 1024, 0)
        gradient.setColorAt(0.0, QColor(BACKGROUND_START))
        gradient.setColorAt(1.0, QColor(BACKGROUND_END))
        palette.setBrush(QPalette.ColorRole.Window, QBrush(gradient))
        self.title_bar.setAutoFillBackground(True)
        self.title_bar.setPalette(palette)

        # Контейнер для дочернего контента
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.content_area)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() < 40:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_position = QPoint()
        super().mouseReleaseEvent(event)