import sys
from PyQt6.QtWidgets import QApplication
from ui_main_menu import MainMenu


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Конструктор блок-схем")

    window = MainMenu()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()