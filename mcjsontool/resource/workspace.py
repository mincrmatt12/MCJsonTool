import abc
import os


class ResourceLocation:
    """
    Refers to something by modid and path

    e.g.:

    minecraft:textures/block/abc.png
    extrafood:models/block/abc.json
    """

    def __init__(self, *args):
        """
        Creates a new ResourceLocation

        >>> ResourceLocation("mc:texture/123.png")
        >>> ResourceLocation("mc", "texture/123.png")
        >>> ResourceLocation("mc", "texture", "123.png")
        >>> # above are all the same

        """
        if len(args) == 1:
            self.data = args[0].split(":")
        elif len(args) == 2:
            self.data = args
        else:
            self.data = args[0], os.path.join(*args[1:])

    def __repr__(self):
        return ":".join(self.data)

    def __str__(self):
        return ":".join(self.data)

    def __getitem__(self, item):
        return self.data[item]

    def get_real_path(self):
        return os.path.join("assets", self.data[0], self.data[1])


class FileProvider(metaclass=abc.ABCMeta):
    """
    Abstract base for file providers

    Must be pickle-able
    """

    @abc.abstractmethod
    def provides_path(self, path):
        """
        Does this provider provide that path?

        :param path: the path to check
        :return: boolean of if it provides it
        """
        return False

    @abc.abstractmethod
    def open_path(self, path, mode="r"):
        """
        Return an open file for this path

        :param path: the path
        :param: mode: mode to open file in
        :return: the open file
        """
        return None


class Workspace:
    """
    Workspace holds a virtual folder that represents all assets for any given instance of minecraft

    Any workspace contains a list of providers, each of which actually give the file&contents

    This class is picklable
    """
    def __init__(self, name):
        self.providers = []
        self.name = name

    def get_file(self, path, mode="r"):
        """
        Gets a reference to an open file

        :param mode: mode to open file in
        :param path: path to file, can be either a string (real path) or ResourceLocation (mod and path)
        :return: an open file referring to it
        """
        if hasattr(path, "get_real_path") and callable(path.get_real_path):
            path = path.get_real_path()

        for i in self.providers:
            if i.provides_path(path):
                return i.open(path, mode)
        raise FileNotFoundError(f"Could not find a reference to file {path}")

    def has_file(self, path):
        """
        Does that path exist?

        :param path: path to file, can be either a string (real path) or ResourceLocation (mod and path)
        :return: does the path exist
        """
        if hasattr(path, "get_real_path") and callable(path.get_real_path):
            path = path.get_real_path()