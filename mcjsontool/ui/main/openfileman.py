import pathlib
from typing import Type

from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QTabWidget, QMessageBox

from mcjsontool.plugin.baseplugin import BasePlugin
from mcjsontool.resource.workspace import Workspace


class OpenFileManager(QObject):
    """
    Manages open files on a tab manager.
    """
    def __init__(self, parent, tabman, workspace: Workspace=None):
        super().__init__(parent)
        self.workspace = workspace
        self.tabman: QTabWidget = tabman  # It's the tab-man, he'll give you money for youuuur tabs. It's the tab-man!
        self.associated_files = [None]
        self.tabman.tabCloseRequested.connect(self.closeRequest)

    def setWorkspace(self, w):
        self.workspace = w
        self.tabman.clear()
        self.associated_files.clear()

    def _open_tab_with_plugin(self, location, plugin: Type[BasePlugin]):
        open_plugin = plugin(location, self.workspace)
        self.associated_files.append(open_plugin)
        if hasattr(location, "get_real_path"):
            location = location.get_real_path()
        path = pathlib.Path(location)
        self.tabman.addTab(open_plugin.get_ui_widget(), path.parts[-1])

    @pyqtSlot(int)
    def closeRequest(self, index):
        if 0 <= index < len(self.associated_files):
            if self.associated_files[index] is None:  # welcome or other crap
                self.tabman.removeTab(index)
                del self.associated_files[index]
            else:
                plugin_: BasePlugin = self.associated_files[index]
                if not plugin_.is_saved():
                    button = QMessageBox.warning(self.tabman, "Are you sure?", "You haven't saved this file! Do you want to save it?", QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)if button == QMessageBox.Discard:
                        self.tabman.removeTab(index)
                        del self.associated_files[index]
                    elif button == QMessageBox.Save:
                        plugin_.save_file()
                        self.tabman.removeTab(index)
                        del self.associated_files[index]
                    else:
                        return

    def open_file(self, location):
        """
        Open a file from location using the attached workspace
        :param location: location to open (must be resourcelocation/path)
        :return: did the file open?
        """
        # todo: use stuff to do things (open multiple views for plugins that handle multiple kinds of files)

        for i in BasePlugin.PLUGIN_TYPES:
            i: BasePlugin
            if i.handles_file(location, self.workspace):
                self._open_tab_with_plugin(location, i)
                return True
        return False

