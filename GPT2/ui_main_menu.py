import sys
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QApplication, QWidget, QVBoxLayout, QPushButton
from PyQt6.QtGui import QPainter, QLinearGradient, QColor
from PyQt6.QtCore import Qt, pyqtSignal
from ui_editor_window import EditorWindow


# 1. СНАЧАЛА ОБЪЯВЛЯЕМ КЛАСС МЕНЮ
class MainMenuWidget(QWidget):
    create_by_algo_clicked = pyqtSignal()
    draw_manual_clicked = pyqtSignal()
    exit_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(25)

        self.btn_algo = QPushButton("Создать блок-схему по\nалгоритму")
        self.btn_manual = QPushButton("Нарисовать блок-схему\nвручную")
        self.btn_exit = QPushButton("Выход")

        button_style = """
            QPushButton {
                background-color: rgba(235, 245, 255, 0.85);
                border: none;
                border-radius: 35px;
                color: #000000;
                font-family: "Segoe UI", "Arial", sans-serif;
                font-size: 18px;
                font-style: italic;
                min-width: 420px;
                max-width: 420px;
                min-height: 70px;
                max-height: 70px;
            }
            QPushButton:hover { background-color: rgba(220, 238, 255, 0.95); }
            QPushButton:pressed { background-color: rgba(200, 225, 255, 0.9); }
        """
        self.btn_algo.setStyleSheet(button_style)
        self.btn_manual.setStyleSheet(button_style)
        self.btn_exit.setStyleSheet(button_style)

        layout.addWidget(self.btn_algo)
        layout.addWidget(self.btn_manual)
        layout.addWidget(self.btn_exit)

        self.btn_algo.clicked.connect(self.create_by_algo_clicked.emit)
        self.btn_manual.clicked.connect(self.draw_manual_clicked.emit)
        self.btn_exit.clicked.connect(self.exit_clicked.emit)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor("#B2C7CE"))
        gradient.setColorAt(0.5, QColor("#A1B6BC"))
        gradient.setColorAt(1.0, QColor("#8D9FA5"))
        painter.fillRect(self.rect(), gradient)
        painter.end()


# 2. ЗАТЕМ ИДЕТ КЛАСС ГЛАВНОГО ОКНА, КОТОРЫЙ ЕГО ИСПОЛЬЗУЕТ
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(1100, 750)  # Подстраиваем под стартовый размер редактора

        self.central_stacked = QStackedWidget()
        self.setCentralWidget(self.central_stacked)

        # 1. Создаем и добавляем Главное Меню (Индекс 0)
        self.main_menu = MainMenuWidget()
        self.central_stacked.addWidget(self.main_menu)

        # Подключаем сигналы к методам переключения
        self.main_menu.create_by_algo_clicked.connect(self.open_algo_mode)
        self.main_menu.draw_manual_clicked.connect(self.open_manual_mode)
        self.main_menu.exit_clicked.connect(self.close)

    def open_algo_mode(self):
        """Открывает режим генерации по псевдокоду"""
        # Создаем окно редактора в автоматическом режиме (manual_mode=False)
        # Передаем self.show_main_menu в качестве колбэка для кнопки «Назад в меню»
        self.algo_screen = EditorWindow(main_menu_callback=self.show_main_menu, manual_mode=False)

        # Добавляем в стек и делаем активным
        idx = self.central_stacked.addWidget(self.algo_screen)
        self.central_stacked.setCurrentIndex(idx)

    def open_manual_mode(self):
        """Открывает режим ручного рисования"""
        # Создаем окно редактора в ручном режиме (manual_mode=True)
        self.manual_screen = EditorWindow(main_menu_callback=self.show_main_menu, manual_mode=True)

        # Добавляем в стек и делаем активным
        idx = self.central_stacked.addWidget(self.manual_screen)
        self.central_stacked.setCurrentIndex(idx)

    def show_main_menu(self):
        """Возвращает пользователя на главный экран меню"""
        # Переключаемся на самый первый виджет (Главное меню)
        self.central_stacked.setCurrentIndex(0)

        # Удаляем старые экраны из памяти, чтобы при следующем открытии они были чистыми
        # (Начиная с конца стека, чтобы не нарушить индексы)
        for i in range(self.central_stacked.count() - 1, 0, -1):
            widget = self.central_stacked.widget(i)
            self.central_stacked.removeWidget(widget)
            widget.deleteLater()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())