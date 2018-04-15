from .workspace import FileProvider
import zipfile


class JarFileProvider(FileProvider):
    def __init__(self, path_to_jar):
        self.jarfile = zipfile.ZipFile(path_to_jar)

    def provides_path(self, path):
        pass

    def open_path(self, path):
        pass

    def __getstate__(self):
        odict =