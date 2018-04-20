import json
import pathlib
import time


class RecentStore:
    """
    The recentstore allows you to keep a recent list of paths. You can also mark the last time a resource was used, along with the last used one.

    Useful for handling workspaces
    """

    def __init__(self, name):
        self.name = name
        self.filepath = pathlib.Path("~/.mcjsontool", name + ".rlist.json").expanduser()
        if not self.filepath.exists():
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            self.files = []
            self._most_recent = None
            self._last_n = 0
            self.save()
        else:
            self.load()

    def load(self):
        with self.filepath.open("r") as f:
            data = json.load(f)
            self.files = data["files"]
            self._most_recent = data["most_recent"]
            self._last_n = data["n"]

    def save(self):
        with self.filepath.open("w") as f:
            data = {
                "files": self.files,
                "most_recent": self._most_recent,
                "n": self._last_n
            }
            json.dump(data, f)

    @property
    def most_recent(self):
        if self._most_recent is None:
            return None
        return self.files[self._most_recent]

    @most_recent.setter
    def most_recent(self, x):
        """
        Set the most recently used path.

        You can set:
            - an integer - the index of the path to set to most recent
            - a string - either a path or name to set to most recent
            - a tuple:
                - either a full entry from the table
                - or just path&name, added if not existing

        This is by far the easiest way to add/update the table.

        :param x: can be a lot of things, see above
        """
        if type(x) is int:
            self._most_recent = x
            self.files[x][2] = time.time()
        else:
            if x in self.files:
                i = self.files.index(x)
                self._most_recent = i
                self.files[i][2] = time.time()
                self._most_recent = i
            elif type(x) is str:
                i = self.index(x)
                self.files[i][2] = time.time()
                self._most_recent = i
            else:
                if len(x) is 2:
                    if x[0] in self:
                        i = self.index(x[0])
                        self.files[i][2] = time.time()
                        self._most_recent = i
                        return
                    else:
                        self.files.append((x[0], x[1], time.time()))
                else:
                    self.files.append(x)
                self._most_recent = len(self.files) - 1

    def __iter__(self):
        """
        Iterate over all paths with first being the most recent entry
        """
        return iter(sorted(self.files, key=lambda x: x[2], reverse=True))

    def __contains__(self, item):
        """
        Check if a name is in the table
        """
        return item in list(x[0] for x in self.files)

    def get_by_name(self, name):
        """
        Get an entry by its name
        :return: the item (name, path, last_time)
        """
        for i in self.files:
            if i[0] == name:
                return i
        raise IndexError("not in")

    def index(self, name_or_path):
        """
        Index of a name or path
        """
        if name_or_path in self:
            return list(x[0] for x in self.files).index(name_or_path)
        else:
            return list(x[1] for x in self.files).index(name_or_path)

    def append(self,path, time_=None, name=None):
        """
        Add a new entry
        :param name: the name (leave empty for an increasing number)
        :param path: the path
        :param time_: if left out, current time, else last update time
        """
        if time_ is None:
            time_ = time.time()
        while name is None or name in self:
            name = str(self._last_n)
            self._last_n += 1
        self.files.append((name, path, time))
