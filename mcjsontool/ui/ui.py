from PyQt5.QtCore import pyqtSlot, QMetaObject, Q_ARG
from PyQt5.QtGui import QImage

from mcjsontool.render.glrender import OffscreenModelRendererThread
from mcjsontool.render.model import BlockModel
from mcjsontool.resource.workspace import Workspace, ResourceLocation
from . import main_ui
from PyQt5.QtWidgets import QMainWindow


class JSONToolUI(QMainWindow, main_ui.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.asyncModelRenderer = OffscreenModelRendererThread(self)
        self.asyncModelRenderer.start()

        self.workspace = None

    @pyqtSlot(Workspace)
    def setWorkspace(self, w):
        self.navWidget.setWorkspace(w)
        QMetaObject.invokeMethod(self.asyncModelRenderer, "setWorkspace", Q_ARG(Workspace, w))
        self.workspace = w

    # MASSIVE TODO: add functionality
