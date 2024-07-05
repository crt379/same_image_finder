import numpy as np

# from typing import Any
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QWidget, QMessageBox, QFileDialog

from ui.image import ImageUi
from ui.loading import Loading
from ui.state import AppState, ImageState
from ui.thread_work import MultipleThreadState, ThreadWork
from db.image_path_dao import ImagePathDao
from db.sift_dao import SiftDao
from tool.file import get_dir_all_file_path
from tool.sift import count_images, sift_good_match


class Operats(QWidget):

    def __init__(self, width, height, state: AppState) -> None:
        super().__init__()

        self._width = width
        self._height = height
        self._state = state

        self._threads = self._state.get_threads()
        
        self._sift_image = None
        
        self._show_sift_window = ImageUi(800, 500, AppState())
        self._show_sift_window.setWindowTitle("sift-image")

        self._loading_already = False
        self._loading_window = Loading()
        self._loading_window.setWindowTitle("sift-loading")

        self._sift_dao: SiftDao | None = None
        if self._state.get_db_conn() is not None:
            self._sift_dao = SiftDao(self._state.get_db_conn())
            self._sift_dao.create()

        self._image_path_dao: ImagePathDao | None = None
        if self._state.get_db_conn() is not None:
            self._image_path_dao = ImagePathDao(self._state.get_db_conn())
            self._image_path_dao.create()

    def setup(self) -> None:
        hbox = QHBoxLayout()
        self.setLayout(hbox)

        files_sift_button = QPushButton("计算目录中图像的SITF特征")
        hbox.addWidget(files_sift_button)
        files_sift_button.clicked.connect(self.__files_sift_button_h)

        find_same_image_button = QPushButton("检索已计算SIFT中的相似图像")
        hbox.addWidget(find_same_image_button)
        find_same_image_button.clicked.connect(self.__find_same_image_button_h)

    def __show_loading(self) -> None:
        if self._loading_already:
            return
        self._loading_already = True
        self._loading_window.show()

    def __close_loading(self) -> None:
        if self._loading_already:
            self._loading_already = False
            self._loading_window.close()

    def __files_sift_button_h(self):
        files_dir = QFileDialog.getExistingDirectory(self, "选择计算sift图片文件夹", ".")
        if files_dir == "":
            return
        
        files_dir = files_dir.replace("/", "\\")
        files = get_dir_all_file_path(
            files_dir, 
            (".idea", "__pycache__", "venv"), 
            self._state.get("image", {}).get("image_suffixs", []), 
            (".sift", ),
        )
        if len(files) < 1:
            QMessageBox(QMessageBox.Information, '提示', '选择目录中没有图片!').exec_()
            return

        threads: list[ThreadWork] = []
        thread_ids = []
        thread_count = min(self._threads.available_number(), len(files))
        for _ in range(thread_count):
            thread, thread_id = self._threads.get()
            if thread is None:
                break
            threads.append(thread)
            thread_ids.append(thread_id)
        
        if len(threads) < 1:
            QMessageBox(QMessageBox.Information, '提示', '没有空闲处理进程, 请稍后再试!').exec_()
            return

        thread_datas: list[list[str]] = []
        thread_work_file_count = int(len(files) / len(threads))
        for i in range(thread_count):
            a_index = i * thread_work_file_count
            e_index = a_index + thread_work_file_count
            thread_datas.append(files[a_index:e_index])
        
        index = len(threads) * thread_work_file_count
        for i, d in enumerate(files[index:]):
            ti = i // len(threads)
            thread_datas[ti].append(d)

        self.__show_loading()
        m_thread_backlog = MultipleThreadState()
        m_thread_backlog.start_wait()

        def backlog_box(thread_id):
            def backlog(sift_infos: list[tuple[str, str, tuple[np.ndarray, np.ndarray, object]]]):
                self._threads.release(thread_id)
                for image_path, image_md5, sift_info in sift_infos:
                    _, des, _ = sift_info
                    if self._image_path_dao is not None:
                        if self._image_path_dao.select(path=image_path):
                            self._image_path_dao.update(image_path, image_md5)
                        else:
                            self._image_path_dao.insert(image_path, image_md5)

                    if self._sift_dao is not None and not self._sift_dao.select(image_md5):
                        self._sift_dao.insert(image_md5, des)

                if m_thread_backlog.is_done() and m_thread_backlog.one_call():
                    self.__close_loading()
                    QMessageBox(QMessageBox.Information, '提示', '计算图像的sitf特征成功').exec_()
            
            return backlog

        for i, thread in enumerate(threads):
            work = m_thread_backlog.work(count_images)
            thread.set_work(work)
            thread.set_parameters(thread_datas[i])
            thread.signal.connect(backlog_box(thread_ids[i]))
            thread.start()

        m_thread_backlog.start_done()

    def __find_same_image_button_h(self):
        image_state: ImageState = self._state.get_state("image-ui")
        if image_state.current_image is None:
            QMessageBox(QMessageBox.Warning, 'Warning', '还没有选择检索图片!').exec_()
            return

        self.__show_loading()
        sift_info = self._sift_dao.select(image_state.current_image_md5)
        if not sift_info:
            image_state.count_sift_handle(
                image_state.current_image_path, 
                image_state.current_image, 
                image_state.current_image_md5,
                image_md5=image_state.current_image_md5,
                is_add_tab=False,
            )

            return self.__find_same_image_button_h()
        else:
            origin_des = sift_info[0][2]
            sift_infos = self._sift_dao.select()

            threads: list[ThreadWork] = []
            thread_ids = []
            thread_count = min(self._threads.available_number(), len(sift_infos))
            for _ in range(thread_count):
                thread, thread_id = self._threads.get()
                if thread is None:
                    break
                threads.append(thread)
                thread_ids.append(thread_id)

            if len(threads) < 1:
                self.__close_loading()
                QMessageBox(QMessageBox.Information, '提示', '没有空闲处理进程, 请稍后再试!').exec_()
                return
            
            thread_datas: list[list[str]] = []
            thread_work_file_count = int(len(sift_infos) / len(threads))
            for i in range(thread_count):
                a_index = i * thread_work_file_count
                e_index = a_index + thread_work_file_count
                thread_datas.append(sift_infos[a_index:e_index])

            index = len(threads) * thread_work_file_count
            for i, d in enumerate(sift_infos[index:]):
                ti = i // len(threads)
                thread_datas[ti].append(d)

            image_paths = self._image_path_dao.select()
            md5_path: dict[str, list] = {}
            for i_p in image_paths:
                try:
                    md5_path[i_p[2]].append(i_p[1])
                except KeyError:
                    md5_path[i_p[2]] = [i_p[1]]

            def get_same_image(infos):
                paths = []
                for info in infos:
                    target_image_md5 = info[1]
                    target_des = info[2]
                    good_match = sift_good_match(origin_des, target_des)
                    if len(good_match) > 15:
                        target_image_path = md5_path.get(target_image_md5)
                        paths.extend(target_image_path)

                return paths

            m_thread_state = MultipleThreadState()

            def backlog_box(thread_id):
                def backlog(paths: list[str]):
                    self._threads.release(thread_id)

                    print(paths)
                    if m_thread_state.is_done() and m_thread_state.one_call():
                        same_paths = []
                        for r in m_thread_state.results():
                            same_paths.extend(r)
                        
                        self.__close_loading()
                        if len(same_paths) > 0:
                            QMessageBox(QMessageBox.Information, '提示', f'检索到相似图像为: {",".join(same_paths)}').exec_()
                        else:
                            QMessageBox(QMessageBox.Information, '提示', '未检索到相似图像').exec_()

                return backlog

            for i, thread in enumerate(threads):
                work = m_thread_state.work(get_same_image)
                thread.set_work(work)
                thread.set_parameters(thread_datas[i])
                thread.signal.connect(backlog_box(thread_ids[i]))
                thread.start()
        
class OperatsUi(Operats):

    def __init__(self, width, height, state):
        super().__init__(width, height, state)

        self.setup()
