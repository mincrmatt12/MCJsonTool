from .workspace import FileProvider
import zipfile
import os


class JarFileProvider(FileProvider):
    def __init__(self, path_to_jar):
        self.path = os.path.abspath(path_to_jar)
        self.jarfile = zipfile.ZipFile(os.path.abspath(path_to_jar))

    def provides_path(self, path):
        return path in self.jarfile.filelist()

    def open_path(self, path, mode="r"):
        return self.jarfile.open(path, mode)

    def __getstate__(self):
        odict = self.__dict__
        del odict["jarfile"]
        return odict

    def __setstate__(self, state):
        self.jarfile = zipfile.ZipFile(state["path"])


class FolderFileProvider(FileProvider):
    def __init__(self, folder):
        self.folder = os.path.abspath(folder)

    def open_path(self, path, mode="r"):
        return open(os.path.join(self.folder, path), mode)

    def provides_path(self, path):
        return os.path.exists(os.path.join(self.folder, path))
