import abc
import os
import pickle
import threading
import time
import pathlib

from PyQt5.QtWidgets import QWidget

REFRESH_FILES_AFTER = 1200


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
            args = list(args)
            if ":" not in args[0]:
                args[0] = "minecraft:" + args[0]
            self.data = list(args[0].split(":"))
        elif len(args) == 2:
            self.data = list(args)
        else:
            self.data = [args[0], os.path.join(*args[1:])]

    @classmethod
    def from_real_path(cls, path):
        path = pathlib.Path(path)
        if path.parts[0] != "assets":
            raise ValueError(f"Path must be relative to the folder containing assets. Got {path.parts[0]} instead.")
        domain = path.parts[1]
        relative_path = pathlib.Path(*path.parts[2:])
        return cls(domain, str(relative_path))

    def __repr__(self):
        return f'ResourceLocation({":".join(self.data)})'

    def __str__(self):
        return ":".join(self.data)

    def __getitem__(self, item):
        return self.data[item]

    def __add__(self, other):
        if type(other) is str:
            return ResourceLocation(self.data[0], self.data[1] + other)

    def __iadd__(self, other):
        self.data[1] += other

    def __eq__(self, other):
        if isinstance(other, ResourceLocation):
            return self.get_real_path() == other.get_real_path()
        else:
            return super(ResourceLocation, self).__eq__(other)

    def get_real_path(self):
        return os.path.join("assets", self.data[0], self.data[1])


class DomainResourceLocation(ResourceLocation):
    """
    DomainResourceLocations are like resourcelocations, but prepend a domain before the path when you know
    what kind of resource you want. Optionally adds filetypes
    """

    def __init__(self, domain, *resourcelocation, filetype=""):
        """
        Create a new DomainResourceLocation

        >>> ResourceLocation("mc", "textures/123.png") == DomainResourceLocation("textures", "mc", "123", filetype=".png")

        :param domain: The type or domain of a resource
        :param resourcelocation: normal parameters to pass to resourcelocation constructor
        """
        super().__init__(*resourcelocation)
        self.data[1] = os.path.join(domain, self.data[1]) + filetype


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

    @abc.abstractmethod
    def list_paths(self):
        """
        Return a list of paths that this provider has
        """
        return []

    @classmethod
    def create_edit_widget(self, parent) -> QWidget:
        """
        Create a QWidget to edit this Provider (or source as the UI calls them) (who named this crap?) (me?) (i have no knowledge of this)
        :return: QWidget
        :param parent: The widget that your widget should be a child of
        """
        return QWidget(parent)


class Workspace:
    EDITMODE_EDIT = 0x00
    EDITMODE_RESOURCEPACK = 0x01

    """
    Workspace holds a virtual folder that represents all assets for any given instance of minecraft.
    It also contains metadata about how the user wants to use this data: to edit it, or to make a resource pack
    based on it. Currently only editing is supported though.
    
    In theory resourcepack files should just edit a journal of files that have been edited, allowing for a resource pack to be created.

    Any workspace contains a list of providers, each of which actually give the file&contents

    This class is picklable
    """

    def __init__(self, name, mode):
        self.providers = []
        self.name = name
        self.mode = mode
        self.file_list_cache = []
        self.last_file_update_time = 0

        self.file_list_lock = threading.Lock()

    @classmethod
    def load_from_file(cls, path):
        with open(path, "rb") as f:
            return pickle.load(f)

    def __getstate__(self):
        dict_ = self.__dict__.copy()
        del dict_["file_list_lock"]
        return dict_

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.file_list_lock = threading.Lock()

    def save_to_file(self, path):
        with open(path, "wb") as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)

    def get_file(self, path, mode="r"):
        """
        Gets a reference to an open file

        :param mode: mode to open file in
        :param path: path to file, can be either a string (real path) or ResourceLocation (mod and path)
        :return: an open file referring to it
        """
        if hasattr(path, "get_real_path") and callable(path.get_real_path):
            path = path.get_real_path()

        path = os.path.normpath(path)

        for i in self.providers:
            if i.provides_path(path):
                return i.open_path(path, mode)
        raise FileNotFoundError(f"Could not find a reference to file {path}")

    def has_file(self, path):
        """
        Does that path exist?

        :param path: path to file, can be either a string (real path) or ResourceLocation (mod and path)
        :return: does the path exist
        """
        if hasattr(path, "get_real_path") and callable(path.get_real_path):
            path = path.get_real_path()

        path = os.path.normpath(path)

        return any((x.provides_path(path) for x in self.providers))

    def list_files(self):
        """
        Get a list of all paths known to this workspace.

        .. note:
            This function is cached to avoid large amounts of disk activity.
            If you want to force a rescan of the disk, use :py:meth:`Workspace.refresh_file_cache`

        :return: A list of all paths
        """
        if time.time() - self.last_file_update_time > REFRESH_FILES_AFTER:
            self.refresh_file_cache(wait_for_complete=not self.file_list_cache)
        with self.file_list_lock:
            return self.file_list_cache

    def _refresh_file_cache(self):
        """
        Refresh the list of known paths to this workspace. Can take a while!
        """

        file_list_cache = []
        for i in self.providers:
            file_list_cache.extend(i.list_paths())
        with self.file_list_lock:
            self.file_list_cache = file_list_cache

    def refresh_file_cache(self, wait_for_complete=True):
        """
        Refresh the list of known paths to this workspace. Allows you to do it in the background if you want.
        :param wait_for_complete: Wait for completion of the task
        """
        if wait_for_complete:
            self._refresh_file_cache()
        else:
            threading.Thread(target=self._refresh_file_cache).start()
