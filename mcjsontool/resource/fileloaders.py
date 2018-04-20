import pathlib

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, QPushButton, QFileDialog

from .workspace import FileProvider
import zipfile
import os
import glob


class JarFileProvider(FileProvider):
    class EditWidget(QWidget):
        def __init__(self, parent):
            super().__init__(parent)
            self.layout = QVBoxLayout()

            self.label = QLabel(self)
            self.label.setText("JarFile Source")
            self.label.setAlignment(Qt.AlignHCenter)

            self.layout.addWidget(self.label)
            self.layout.addStretch()

            self.layout2 = QHBoxLayout()
            self.label2 = QLabel(self)
            self.label2.setText("Path to jarfile")
            self.lineEdit = QLineEdit(self)
            self.browseButton = QPushButton("...", self)

            self.layout2.addWidget(self.label2)
            self.layout2.addWidget(self.lineEdit)
            self.layout2.addWidget(self.browseButton)

            self.browseButton.clicked.connect(self.on_browse)
            self.layout.addLayout(self.layout2)
            self.setLayout(self.layout)

        def is_valid(self):
            return pathlib.Path(self.lineEdit.text()).exists()

        def create_provider(self):
            return JarFileProvider(self.lineEdit.text())

        def __str__(self):
            return f"JAR: {self.lineEdit.text()}"

        @pyqtSlot()
        def on_browse(self):
            filepath, *a = QFileDialog.getOpenFileName(parent=self, caption="Select path to jar",
                                                       filter="Jarfile (*.jar)")
            if filepath:
                self.lineEdit.setText(filepath)

    def __init__(self, path_to_jar):
        self.path = os.path.abspath(path_to_jar)
        self.jarfile = zipfile.ZipFile(os.path.abspath(path_to_jar))

    def provides_path(self, path):
        path = path.replace(os.path.sep, "/")  # jarfiles are wierd, okay?
        return path in self.jarfile.namelist()

    def open_path(self, path, mode="r"):
        mode = mode.replace("b", "")
        path = path.replace(os.path.sep, "/")  # jarfiles are wierd, okay?
        return self.jarfile.open(path, mode)

    def list_paths(self):
        return filter(lambda x: x.startswith("assets") and ".mcassetsroot" not in x, self.jarfile.namelist())

    @classmethod
    def create_edit_widget(cls, parent):
        return JarFileProvider.EditWidget(parent)

    def __getstate__(self):
        odict = self.__dict__.copy()
        del odict["jarfile"]
        return odict

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.jarfile = zipfile.ZipFile(state["path"])


class FolderFileProvider(FileProvider):
    class EditWidget(QWidget):
        def __init__(self, parent):
            super().__init__(parent)
            self.layout = QVBoxLayout()

            self.label = QLabel(self)
            self.label.setText("Folder Source")
            self.label.setAlignment(Qt.AlignHCenter)

            self.layout.addWidget(self.label)
            self.layout.addStretch()

            self.layout2 = QHBoxLayout()
            self.label2 = QLabel(self)
            self.label2.setText("Path to asset folder (should contain a folder called assets)")
            self.lineEdit = QLineEdit(self)
            self.browseButton = QPushButton("...", self)

            self.layout2.addWidget(self.label2)
            self.layout2.addWidget(self.lineEdit)
            self.layout2.addWidget(self.browseButton)

            self.browseButton.clicked.connect(self.on_browse)

            self.layout.addLayout(self.layout2)
            self.setLayout(self.layout)

        def is_valid(self):
            return pathlib.Path(self.lineEdit.text()).exists()

        def create_provider(self):
            return FolderFileProvider(self.lineEdit.text())

        def __str__(self):
            return f"Folder: {self.lineEdit.text()}"

        @pyqtSlot()
        def on_browse(self):
            filepath = QFileDialog.getExistingDirectory(parent=self, caption="Select path to folder")
            if filepath:
                self.lineEdit.setText(filepath)

    def __init__(self, folder):
        self.folder = os.path.abspath(folder)

    def open_path(self, path, mode="r"):
        return open(os.path.join(self.folder, path), mode)

    def provides_path(self, path):
        return os.path.exists(os.path.join(self.folder, path))

    def list_paths(self):
        all_files = []
        for root, _, files in os.walk(self.folder):
            all_files.extend(filter(lambda x: x.startswith("assets"), map(lambda x: os.path.relpath(os.path.join(root, x), self.folder), files)))
        return all_files

    @classmethod
    def create_edit_widget(cls, parent):
        return FolderFileProvider.EditWidget(parent)


fileloaders = [JarFileProvider, FolderFileProvider]
