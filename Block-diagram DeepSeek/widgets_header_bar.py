# widgets_header_bar.py — исправленная версия с поддержкой бургер-меню
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QToolButton, QMenu, QApplication, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent, QAction, QPixmap


class HeaderBar(QWidget):
    def __init__(self, parent, export_png_callback=None, export_pdf_callback=None):
        super().__init__(parent)
        self.setObjectName("headerBar")
        self.setFixedHeight(36)
        self._drag_pos = None
        
        # Колбэки для экспорта
        self._export_png_callback = export_png_callback
        self._export_pdf_callback = export_pdf_callback

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(4)

        # Кнопка меню
        self.menu_btn = QToolButton()
        self.menu_btn.setText("☰")
        self.menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                color: #444444;
                font-size: 18px;
                font-weight: bold;
                padding: 4px 8px;
            }
            QToolButton:hover {
                background: rgba(0,0,0,0.08);
                border-radius: 4px;
            }
        """)
        
        # Создаём меню
        self._create_menu()
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

    def _create_menu(self):
        """Создаёт меню для кнопки ☰."""
        self.menu = QMenu(self)
        self.menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:hover {
                background: #DDEEF3;
            }
            QMenu::separator {
                height: 1px;
                background: #ddd;
                margin: 4px 10px;
            }
        """)

        # Экспорт в PNG
        if self._export_png_callback:
            action_png = QAction("Сохранить как PNG", self)
            action_png.triggered.connect(self._export_png_callback)
            self.menu.addAction(action_png)

            # Экспорт в PDF
            if self._export_pdf_callback:
                action_pdf = QAction("Сохранить как PDF", self)
                action_pdf.triggered.connect(self._export_pdf_callback)
                self.menu.addAction(action_pdf)

            self.menu.addSeparator()

        # Возврат в главное меню
        action_back = QAction("← Назад", self)
        action_back.triggered.connect(self._go_back)
        self.menu.addAction(action_back)

        self.menu_btn.setMenu(self.menu)

    def set_export_callbacks(self, png_callback, pdf_callback):
        """Устанавливает колбэки для экспорта."""
        self._export_png_callback = png_callback
        self._export_pdf_callback = pdf_callback
        # Пересоздаём меню с новыми колбэками
        self.menu.clear()
        self._create_menu()

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

    def _go_back(self):
        win = self.window()
        if hasattr(win, 'main_menu') and win.main_menu:
            win.main_menu.show()
        win.close()

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