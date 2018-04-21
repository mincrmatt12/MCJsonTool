from PyQt5.QtCore import pyqtSlot, QMetaObject, Q_ARG

from mcjsontool.render.glrender import OffscreenModelRendererThread
from mcjsontool.resource.recentstore import RecentStore
from mcjsontool.resource.workspace import Workspace
from mcjsontool.ui.main.openfileman import OpenFileManager
from mcjsontool.ui.workspace.workspacewizard import WorkspaceWizard
from . import main_ui
from PyQt5.QtWidgets import QMainWindow, QAction


class JSONToolUI(QMainWindow, main_ui.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.asyncModelRenderer = OffscreenModelRendererThread(self)
        self.asyncModelRenderer.start()

        self.workspace = None
        self.workspaceWizard = None

        self.actionWorkspace.triggered.connect(self.newWorkspace)
        self.activePlugins = []
        self.recent_workspaces = RecentStore("workspaces")

        self.open_file_man = OpenFileManager(self, self.tabs)
        self.navWidget.open_file.connect(self.on_open_file)
        if self.recent_workspaces.most_recent:
            self.setWorkspace(Workspace.load_from_file(self.recent_workspaces.most_recent[1]))

        self.menuRecent.triggered.connect(self.on_recent)
        self.update_recent()

    def update_recent(self):
        c = 0
        self.menuRecent.clear()
        for i in self.recent_workspaces:
            if c > 10:
                break
            c += 1
            act = QAction(i[0], self)
            act.setData(i)
            self.menuRecent.addAction(act)

    def closeEvent(self, *args, **kwargs):
        self.recent_workspaces.save()

    @pyqtSlot(str)
    def on_open_file(self, f):
        self.open_file_man.open_file(f)

    @pyqtSlot(QAction)
    def on_recent(self, act):
        workspace = Workspace.load_from_file(act.data()[1])
        self.recent_workspaces.most_recent = act.data()[0]
        self.setWorkspace(workspace)
        self.update_recent()

    @pyqtSlot(Workspace)
    def setWorkspace(self, w):
        self.navWidget.setWorkspace(w)
        self.open_file_man.setWorkspace(w)
        QMetaObject.invokeMethod(self.asyncModelRenderer, "setWorkspace", Q_ARG(Workspace, w))
        self.workspace = w

    @pyqtSlot(Workspace, str)
    def setNewWorkspace(self, w: Workspace, s):
        self.recent_workspaces.most_recent = (w.name, s)
        self.setWorkspace(w)
        self.update_recent()

    @pyqtSlot()
    def newWorkspace(self):
        self.workspaceWizard = WorkspaceWizard(self)
        self.workspaceWizard.newWorkspaceEmitted.connect(self.setNewWorkspace)
        self.workspaceWizard.exec_()
