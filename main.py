import sys

from PyQt5.QtWidgets import QApplication

from ui.main_window import MainUi

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainUi()
    window.start()
    sys.exit(app.exec_())