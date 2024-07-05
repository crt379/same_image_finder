from PyQt5.QtWidgets import QFileSystemModel, QTreeView, QWidget


class FilesTree(QTreeView):

    def __init__(self) -> None:
        self._file_system_model = QFileSystemModel()

    def setup(self):
        self.setModel(self._file_system_model)

    def set_files_model(self, path, callback):
        self._file_system_model.setRootPath(path)
        self.setRootIndex(self._file_system_model.index(path))
        for col in range(1, 4):
            self.setColumnHidden(col, True)

        def doubleck(model_idx):
            file_path = self._file_system_model.filePath(model_idx)
            file_path = file_path.replace("/", "\\")
            callback(file_path)

        self.doubleClicked.connect(doubleck)


class FilesUi(FilesTree, QWidget):

    def __init__(self):
        super().__init__()
        QWidget.__init__(self)

        self.setup()
