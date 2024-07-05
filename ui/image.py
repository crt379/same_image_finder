import hashlib
import time
import cv2
import numpy as np

from PyQt5.QtGui import (
    QImage, 
    QPixmap, 
    QWheelEvent, 
    QPainter,
    QCursor,
)
from PyQt5.QtCore import (
    pyqtSlot, 
    pyqtSignal, 
    QRect, 
    Qt,
    QTimer,
)
from PyQt5.QtWidgets import (
    QGraphicsPixmapItem, 
    QGraphicsScene, 
    QGraphicsView, 
    QWidget, 
    QTabBar,
    QMenu,
    QAction,
    QFileDialog,
    QMessageBox,
)

from ui.state import AppState, ImageState
from db.image_path_dao import ImagePathDao
from db.sift_dao import SiftDao
from tool.file import get_file_suffix
from tool.sift import count_by_down as count_sift, count_image_md5


class ImageView(QGraphicsView):
    leftMouseButtonPressed = pyqtSignal(float, float)
    leftMouseButtonReleased = pyqtSignal(float, float)

    def __init__(self, state: AppState, parent=None) -> None:
        super().__init__(parent)

        self._DEF_ZOOM = 1
        self._MAX_ZOOM = 40
        self._MIN_ZOOM = -20

        self._state: AppState = state

        self._image_path_dao: ImagePathDao | None = None
        if self._state.get_db_conn() is not None:
            self._image_path_dao = ImagePathDao(self._state.get_db_conn())
            self._image_path_dao.create()

        self._image = None
        self._pixmap = None

        self._threads = self._state.get_threads()

        self._press_events = []
        self._press_latest_time = None

        self._release_events = []
        self._release_latest_time = None

        # ms
        self._press_timeout = 300
        self._release_timeout = 150

        self._timer = QTimer()
        self._timer.timeout.connect(self.__click_handle)

        self.right_menu = QMenu()

    def setup(self):
        pass

    def set_image_path(self, image_path) -> (np.ndarray | None, str | None):
        image_buf = np.fromfile(image_path, dtype=np.uint8)
        try:
            image = cv2.imdecode(image_buf, cv2.IMREAD_COLOR)
        except Exception:
            image = None

        if image is None:
            return image, None

        image_md5 = hashlib.md5(image).hexdigest()
            
        if self._image_path_dao is not None:
            if self._image_path_dao.select(path=image_path):
                self._image_path_dao.update(image_path, image_md5)
            else:
                self._image_path_dao.insert(image_path, image_md5)

        self.set_image(image)

        return image, image_md5

    def set_image(self, image: np.ndarray):
        # 创建场景
        self._image = None
        scene = QGraphicsScene()

        if image is not None:
            qimage = QImage(
                image.data,
                image.shape[1],
                image.shape[0],
                image.shape[1] * 3,
                QImage.Format_RGB888
            ).rgbSwapped()

            self._image = qimage

            self._pixmap = QPixmap.fromImage(self._image)

            # 创建像素图元
            item = QGraphicsPixmapItem(self._pixmap)
            # 平滑缩放
            item.setTransformationMode(Qt.SmoothTransformation)

            # 以鼠标所在位置为锚点进行缩放
            self.setTransformationAnchor(self.AnchorUnderMouse)
            self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

            # 设置场景
            scene.addItem(item)

        self.resetTransform()
        # 将场景添加至视图
        self.setScene(scene)

    def __image_zoom(self):
        if self._pixmap is None:
            return
        
        pw = self._pixmap.width()
        ph = self._pixmap.height()
        w = self.width()
        h = self.height()
        rw = w / pw
        rh = h / ph
        zoom = min(rw, rh) * 0.99
        if zoom < 1:
            self.scale(zoom, zoom)

    def resetTransform(self):
        super().resetTransform()
        self.__image_zoom()
        self._zoom = self._DEF_ZOOM

    @pyqtSlot()
    def up(self, viewAnchor=QGraphicsView.AnchorUnderMouse):
        """
        放大图像
        """
        zoom = self._zoom + 1
        if zoom > self._MAX_ZOOM or zoom < self._zoom:
            return
        self._zoom = zoom

        self.setTransformationAnchor(viewAnchor)

        self.scale(1.1, 1.1)

        # 还原 anchor
        self.setTransformationAnchor(self.AnchorUnderMouse)

    @pyqtSlot()
    def down(self, viewAnchor=QGraphicsView.AnchorUnderMouse):
        """
        缩小图像
        """
        zoom = self._zoom - 1
        if zoom < self._MIN_ZOOM or zoom > self._zoom:
            return
        self._zoom = zoom

        self.setTransformationAnchor(viewAnchor)

        self.scale(1 / 1.1, 1 / 1.1)

        # 还原 anchor
        self.setTransformationAnchor(self.AnchorUnderMouse)

    # 鼠标滑轮
    def wheelEvent(self, event: QWheelEvent) -> None:
        if self._image:
            if event.angleDelta().y() > 0:
                self.up()
            else:
                self.down()

    def __right_click_handle(self):
        if self._image:
            self.right_menu.exec_(QCursor.pos())

    def __right_double_click_handle(self):
        if self._image and self._zoom != self._DEF_ZOOM:
            self.resetTransform()

    def __click_handle(
            self, 
            click_r=[[Qt.RightButton], [Qt.RightButton]],
            double_click_r=[[Qt.RightButton], [Qt.RightButton, Qt.RightButton]],
        ):
        self._timer.stop()

        # print(self._press_events, self._release_events)
        if self._press_events == click_r[0] and self._release_events == click_r[1]:
            self.__right_click_handle()
        elif self._press_events == double_click_r[0] and self._release_events == double_click_r[1]:
            self.__right_double_click_handle()

        self._press_events = []
        self._release_events = []
        
    # 鼠标点击事件
    def mousePressEvent(self, event):
        self._press_latest_time = time.time()
        
        self._timer.start(self._press_timeout)
        button = event.button()
        self._press_events.append(button)
        if button == Qt.LeftButton:
            if self._image:
                scene_pos = self.mapToScene(event.pos())
                self.setDragMode(QGraphicsView.ScrollHandDrag)
                self.leftMouseButtonPressed.emit(scene_pos.x(), scene_pos.y())

        QGraphicsView.mousePressEvent(self, event)

    # 鼠标释放事件
    def mouseReleaseEvent(self, event):
        self._release_latest_time = time.time()
        sub = int((self._release_latest_time - self._press_latest_time) * 1000)
        t = max((self._press_timeout - sub) + self._release_timeout, self._release_timeout)
        t = min(t, self._press_timeout)

        self._timer.start(t)
        button = event.button()
        self._release_events.append(button)
        if button == Qt.LeftButton:
            if self._image:
                scene_pos = self.mapToScene(event.pos())
                self.setDragMode(QGraphicsView.NoDrag)
                self.leftMouseButtonReleased.emit(scene_pos.x(), scene_pos.y())
        QGraphicsView.mouseReleaseEvent(self, event)


class ImageUi(QWidget):

    def __init__(self, width, height, state: AppState):
        super().__init__()
        self.state = ImageState()
        self.state.count_sift_handle = self.__count_sift_0

        self._state = state
        self._state.register("image-ui", self.state)

        self._threads = self._state.get_threads()

        self._top_paths = []
        self.path_image = {}
        
        top_h = 50

        tab_bar_style = (
            "QTabBar {"
            "   border: 1px solid #130c0e;"
            "   border-top-left-radius: 10px;"
            "   border-top-right-radius: 10px;"
            "}"
            "\n"
            "QTabBar::tab {"
            "   border-right: 1px solid;"
            f"   height: {top_h}px;"
            "}"
            "\n"
            "QTabBar::tab:first {"
            "   border-top-left-radius: 10px;"
            "}"
            "\n"
            "QTabBar::tab:last {"
            "   border-top-right-radius: 10px;"
            "}"
            "\n"
            "QTabBar::tab:only-one {"
            "   border-top-left-radius: 10px;"
            "   border-top-right-radius: 10px;"
            "}"
            "QTabBar::tab:selected {"
            "   background: DeepSkyBlue;"
            "   border-bottom: 3px solid red;"
            "}"
            "\n"
        )

        self._top_tab_bar = QTabBar(self, tabsClosable=True)
        self._top_tab_bar.setStyleSheet(tab_bar_style)
        self._top_tab_bar.setGeometry(QRect(0, 0, width, top_h))
        self._top_tab_bar.tabBarClicked.connect(self.__top_tab_clicked_callback)
        self._top_tab_bar.tabCloseRequested.connect(self.__top_tab_close_callback)
        
        self._image_view = ImageView(state, self)
        self._image_view.setStyleSheet("border:2px solid #130c0e;")
        self._image_view.setGeometry(QRect(0, top_h, width, height-top_h))
        self._image_view.setup()

        save_image_action = QAction("图片另存", self._image_view)
        save_image_action.triggered.connect(self.__save_image)

        show_sift_action = QAction("显示sift图", self._image_view)
        show_sift_action.triggered.connect(self.__show_sift)

        self._image_view.right_menu.addAction(save_image_action)
        self._image_view.right_menu.addAction(show_sift_action)

        self._sift_dao: SiftDao | None = None
        if self._state.get_db_conn() is not None:
            self._sift_dao = SiftDao(self._state.get_db_conn())
            self._sift_dao.create()

    def __top_tab_set_current(self, index):
        if len(self._top_paths) == 0:
            self.set_image(None)
            self.state.current_image = None
            self.state.current_image_md5 = None
            self.state.current_image_path = None
            return

        image_path = self._top_paths[index]
        if self.state.current_image_path == image_path:
            return

        image = self.path_image[image_path]
        image_md5 = count_image_md5(image)

        self.set_image(image)
        self._top_tab_bar.setCurrentIndex(index)

        self.state.current_image = image
        self.state.current_image_md5 = image_md5
        self.state.current_image_path = image_path

    def __top_tab_clicked_callback(self, index):
        if len(self._top_paths) == 0:
            return
        
        self.__top_tab_set_current(index)

    def __top_tab_close_callback(self, index):
        self._top_tab_bar.removeTab(index)

        path = self._top_paths.pop(index)
        del self.path_image[path]

        while index >= 0:
            try:
                path = self._top_paths[index]
                break
            except Exception:
                index -= 1

        self.__top_tab_set_current(index)

    def __top_add_tab(self, image_path, image):
        self._top_paths.append(image_path)    
        self.path_image[image_path] = image
        
        return self._top_tab_bar.addTab(image_path)
        
    def set_image(self, image) -> None:
        self._image_view.set_image(image)

    def set_image_path(self, image_path) -> None:
        if image_path == self.state.current_image_path:
            return
        
        image = self.path_image.get(image_path) if image_path is not None else None
        image_md5 = count_image_md5(image) if image is not None else None
        if image_path is None:
            self.set_image(image)
        elif image is not None:
            self.set_image(image)
            for i, p in enumerate(self._top_paths):
                if p == image_path:
                    self._top_tab_bar.setCurrentIndex(i)
                    break
        else:
            image, image_md5 = self._image_view.set_image_path(image_path)
            if image is None:
                return
            
            index = self.__top_add_tab(image_path, image)
            self._top_tab_bar.setCurrentIndex(index)
            self.__count_sift_0(image_path, image, tab_set_select=False, image_md5=image_md5)

        self.state.current_image = image
        self.state.current_image_md5 = image_md5
        self.state.current_image_path = image_path

    def __count_sift_0(self, image_path, image, tab_set_select=False, image_md5=None):
        thread, thread_id = self._threads.get()
        if thread is None:
            return
        
        def back(data):
            self._threads.release(thread_id)

            sift_image, des, _ = data
            if sift_image is None:
                return
            
            md5 = image_md5
            if md5 is None:
                md5 = count_image_md5(image)
                
            if self._sift_dao is not None and not self._sift_dao.select(md5):
                self._sift_dao.insert(md5, des)

            sift_path = image_path + ".sift"
            index = self.__top_add_tab(sift_path, sift_image)
            if tab_set_select:
                self.__top_tab_set_current(index)

        thread.set_work(count_sift)
        thread.set_parameters(image)
        thread.signal.connect(back)
        thread.start()

        return
    
    def __save_image(self):
        path = self.state.current_image_path
        path_suffix = get_file_suffix(path)
        if path_suffix == ".sift":
            path = path[:-5]
            path_suffix = get_file_suffix(path)
            if path_suffix:
                path = path[:-len(path_suffix)] + ".sift" + path_suffix
            else:
                path += ".sift"
        else:
            path = path[:-len(path_suffix)] + ".tmp" + path_suffix

        save_file_name = QFileDialog.getSaveFileName(self, '保存文件', path)
        save_file_path = save_file_name[0]
        if save_file_path == "":
            return
        
        try:
            image = self.state.current_image
            cv2.imwrite(save_file_path, image, [cv2.IMWRITE_JPEG_QUALITY, 100])
        except Exception as e:
            QMessageBox(QMessageBox.Warning, '保存失败', str(e)).exec_()
            return

        QMessageBox(QMessageBox.Information, '成功', f'保存成功! 保存路径: {save_file_path}').exec_()

    def __show_sift(self):
        path_suffix = get_file_suffix(self.state.current_image_path)
        if path_suffix == ".sift":
            QMessageBox(QMessageBox.Information, '提示', f'所显示图像已是sift图!').exec_()
        else:
            sift_path = self.state.current_image_path + ".sift"
            sift_image = self.path_image.get(sift_path)

            if sift_image is None:
                self.__count_sift_0(self.state.current_image_path, self.state.current_image, tab_set_select=True, image_md5=self.state.current_image_md5)
            else:
                index = 0
                for i, p in enumerate(self._top_paths):
                    if p == sift_path:
                        index = i
                        break
                
                self.__top_tab_set_current(index)
