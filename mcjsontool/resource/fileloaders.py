from .workspace import FileProvider
import zipfile
import os
import glob


class JarFileProvider(FileProvider):
    def __init__(self, path_to_jar):
        self.path = os.path.abspath(path_to_jar)
        self.jarfile = zipfile.ZipFile(os.path.abspath(path_to_jar))

    def provides_path(self, path):
        return path in self.jarfile.filelist()

    def open_path(self, path, mode="r"):
        return self.jarfile.open(path, mode)

    def list_paths(self):
        return filter(lambda x: x.startswith("assets"), self.jarfile.filelist())

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

    def list_paths(self):
        all_files = []
        for root, _, files in os.walk(self.folder):
            all_files.extend(filter(lambda x: x.startswith("assets"), map(lambda x: os.path.join(root, x), files)))
        return all_files
