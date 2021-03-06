from .workspace import FileProvider
import zipfile
import os


class JarFileProvider(FileProvider):
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
        return fileloaderui.JarEditWidget(parent)

    def __getstate__(self):
        odict = self.__dict__.copy()
        del odict["jarfile"]
        return odict

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.jarfile = zipfile.ZipFile(state["path"])


class FolderFileProvider(FileProvider):
    def __init__(self, folder):
        self.folder = os.path.abspath(folder)

    def open_path(self, path, mode="r"):
        return open(os.path.join(self.folder, path), mode)

    def provides_path(self, path):
        return os.path.exists(os.path.join(self.folder, path))

    def list_paths(self):
        all_files = []
        for root, _, files in os.walk(self.folder):
            all_files.extend(filter(lambda x: x.startswith("assets"),
                                    map(lambda x: os.path.relpath(os.path.join(root, x), self.folder), files)))
        return all_files

    @classmethod
    def create_edit_widget(cls, parent):
        return fileloaderui.FolderEditWidget(parent)


fileloaders = [JarFileProvider, FolderFileProvider]
from ..ui.workspace import fileloaderui
