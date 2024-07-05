import os

from PyQt5.QtCore import QRect, QCoreApplication
from PyQt5.QtWidgets import (
        QMainWindow, QDesktopWidget, QWidget, 
        QMenuBar, QMenu, QAction, QGridLayout, 
        QStatusBar, QFileDialog,
    )

from conf.config import config
from ui.image import ImageUi
from ui.files import FilesUi
from ui.operats import OperatsUi
from ui.state import AppState
from ui.thread_work import ThreadWorkS
from db.conn import sift_db_connect


class MainUi(QMainWindow):

    def __init__(self) -> None:
        super().__init__()

        self._width = None
        self._height = None

        self._menubar = None

        self._files_ui = None
        self._image_ui = None
        self._operats_ui = None

        # 根路径
        self._path = os.path.dirname(os.path.abspath("__file__"))

        self.state = AppState()
        self.state.config = config

        self.state.set_run_path(self._path)
        self.state.set_db_conn(sift_db_connect())
        self.state.set_threads(ThreadWorkS(self.state.config.get("threads", {}).get("max", 1)))

    def __set_width_heigh(self):
        # 获取屏幕坐标系
        screen = QDesktopWidget().screenGeometry()
        self._width = int(screen.width() * 0.7)
        self._height = int(screen.height() * 0.8)
        # self.resize(self._width, self._height)
        self.setFixedSize(self._width, self._height)
        self.setAutoFillBackground(True)

    def start(self):
        self.setObjectName("Form")
        self.setWindowTitle(QCoreApplication.translate("MainWindow", "图像管理系统"))
        self.__set_width_heigh()
        self.__menu_bar()
        self.__widget_init()
        self.show()

    def __menu_bar(self):
        """
        菜单栏
        """
        menubar = QMenuBar(self)
        menubar.setObjectName("menubar")
        menubar.setGeometry(QRect(0, 0, self._width, 23))
        self._menubar = menubar
        self.__menu_file()
        self.__memu_setup()

        self.setMenuBar(self._menubar)

    def __menu_file(self):
        """
        菜单栏 - 文件
        """
        menubar_file = QMenu(self._menubar)
        menubar_file.setObjectName("menu_file")
        menubar_file.setTitle(QCoreApplication.translate("MainWindow", "文件"))

        open_image = QAction("打开...", self)
        open_image.setStatusTip('打开图像')
        open_image.triggered.connect(self.__open_image)
        menubar_file.addAction(open_image)

        open_directory = QAction('打开文件夹...', self)
        open_directory.setStatusTip('打开文件夹')
        open_directory.triggered.connect(self.__open_directory)
        menubar_file.addAction(open_directory)

        self._menubar.addAction(menubar_file.menuAction())

    def __open_image(self):
        image_suffixs = self.state.config.get("image", {}).get("image_suffixs", [])
        filter = f"*{' *'.join(image_suffixs)};;All Files(*)" if len(image_suffixs) > 0 else "All Files(*)"
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "打开图像", 
            ".", 
            filter,
        )
        if filename == "":
            return
        
        self.state.publish("open-image", filename)

    def __open_directory(self):
        filename = QFileDialog.getExistingDirectory(self, "选取文件夹", ".")
        if filename == "":
            return
        
        self.state.publish("open-directory", filename)

    def __memu_setup(self):
        """
        菜单栏 - 设置
        """
        memu_setup = QMenu(self._menubar)
        memu_setup.setObjectName("menu_setup")
        memu_setup.setTitle(QCoreApplication.translate("MainWindow", "设置"))

        setup = QAction("设置...", self)
        setup.setStatusTip('打开设置')
        memu_setup.addAction(setup)

        self._menubar.addAction(memu_setup.menuAction())

    def __widget_init(self):
        """
        小部件
        """
        self.__widget_geometry()
        self.__widget_files()
        self.__widget_image()
        # 图像下方
        self.__widget_operats()
        # 底部
        self.__widget_statusbar()

        self.__final()

    def __widget_geometry(self):
        self._files_l = int(self._width * 0.01)
        self._files_t = self._menubar.height() * 2
        self._files_w = int(self._width * 0.15)
        self._files_h = int(self._height * 0.9)

        self._image_l = self._files_l * 2 + self._files_w
        self._image_t = self._files_t
        # self._image_w = self._width - self._files_w - int(self._width * 0.05)
        self._image_w = self._width - self._files_w - int(self._width * 0.03)
        self._image_h = int(self._height * 0.8)

        self._operats_l = self._image_l
        self._operats_t = self._files_t * 2 + self._image_h
        self._operats_w = self._image_w
        self._operats_h = int(self._height * 0.05)

        self._right_l = self._image_l + self._image_w
        self._right_t = self._image_t
        self._right_w = self._width - self._right_l
        self._right_h = self._image_h

    def __widget_files(self):
        # 目录结构
        l = self._files_l
        t = self._files_t
        w = self._files_w
        h = self._files_h

        files = QWidget(self)
        files.setObjectName("widget_files")
        files.setGeometry(QRect(l, t, w, h))
        # files.setStyleSheet("border:1px solid #130c0e;")
        # 
        files_layout = QGridLayout(files)
        files_layout.setObjectName("widget_files_layout")
        files_layout.setContentsMargins(0, 0, 0, 0)

        self._files_ui = FilesUi()
        self._files_ui.set_files_model(self._path, self.__files_layout_callback)

        files_layout.addWidget(self._files_ui)

    def __files_layout_callback(self, image_path):
        if not os.path.isfile(image_path):
            return

        self._image_ui.set_image_path(image_path)

    def __widget_image(self):
        # 显示图片布局
        l = self._image_l
        t = self._image_t
        w = self._image_w
        h = self._image_h

        image = QWidget(self)
        image.setObjectName("widget_image")
        image.setGeometry(QRect(l, t, w, h))
        # image.setStyleSheet("border:2px solid #130c0e;")
        # 图片里面的布局
        image_layout = QGridLayout(image)
        image_layout.setObjectName("widget_image_layout")
        image_layout.setContentsMargins(0, 0, 0, 0)

        self._image_ui = ImageUi(w, h, self.state)
        image_layout.addWidget(self._image_ui)

    def __widget_operats(self):
        l = self._operats_l
        t = self._operats_t
        w = self._operats_w
        h = self._operats_h

        operats = QWidget(self)
        operats.setObjectName("widget_operats")
        operats.setGeometry(QRect(l, t, w, h))
        # operats.setStyleSheet("border:2px solid #130c0e;")

        operats_layout = QGridLayout(operats)
        operats_layout.setObjectName("widget_operats_layout")
        # operats_layout.setContentsMargins(0, 0, 0, 0)

        self._operats_ui = OperatsUi(w, h, self.state)

        operats_layout.addWidget(self._operats_ui)

    def __widget_statusbar(self):
        statusbar = QStatusBar(self)
        statusbar.setObjectName("widget_statusbar")
        statusbar.setStyleSheet("border:2px solid #130c0e;")

        self.setStatusBar(statusbar)

    def __final(self):
        self.state.subscribe("open-image", self._image_ui.set_image_path)
        self.state.subscribe(
            "open-directory", 
            lambda filename: self._files_ui.set_files_model(filename, self.__files_layout_callback),
        )