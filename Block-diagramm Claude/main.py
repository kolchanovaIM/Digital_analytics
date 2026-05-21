import sys
from PyQt6.QtWidgets import QApplication
from ui_main_menu import MainMenuWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FlowChart Designer")
    app.setOrganizationName("FlowChart")

    window = MainMenuWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()