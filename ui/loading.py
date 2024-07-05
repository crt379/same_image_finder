import sys

from PyQt5.QtCore import Qt, QSize
# from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QLabel, QDialog, QGridLayout, QApplication, QPushButton


class Loading(QDialog):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("loading")
        self.setFixedSize(QSize(300, 120))
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.MSWindowsFixedSizeDialogHint | Qt.WindowStaysOnTopHint)


        self.layout: QGridLayout = QGridLayout()
        self.setLayout(self.layout)

        self.__set_label()

    def __set_label(self):
        self.label = QLabel("正在处理，请稍候...")
        # self.label.setStyleSheet("border:2px solid #130c0e;")
        # self.label.setScaledContents(True)
        # self.label.setFixedSize(QSize(w, h))

        # self.movie = QMovie("loading.gif")
        # self.movie.start()
        # self.movie_label.setMovie(self.movie)

        self.layout.addWidget(self.label, 1, 1)
        
    def set_done_button(self):
        btn = QPushButton()
        btn.setText("确定")

        self.layout.addWidget(btn, 2, 1, Qt.AlignRight | Qt.AlignVCenter)
        
    def show(self) -> None:
        return super().show()

    def close(self) -> bool:
        return super().close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Loading()
    window.show()
    sys.exit(app.exec_())
