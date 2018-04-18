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
        self.asyncModelRenderer.renderedTexture.connect(self.on_new_image)

        self.workspace = None
        self.actionExit.triggered.connect(self.temp)

    @pyqtSlot(Workspace)
    def setWorkspace(self, w):
        self.navWidget.setWorkspace(w)
        QMetaObject.invokeMethod(self.asyncModelRenderer, "setWorkspace", Q_ARG(Workspace, w))
        self.workspace = w

    @pyqtSlot(str, QImage)
    def on_new_image(self, s, i: QImage):
        i.save(s + ".png")

    @pyqtSlot()
    def temp(self):
        bm =  BlockModel.load_from_file(self.workspace, ResourceLocation("minecraft", "models/block/andesite.json"))
        QMetaObject.invokeMethod(self.asyncModelRenderer, "queue_render_order", Q_ARG(str, "asdf"), Q_ARG(BlockModel, bm))

    # MASSIVE TODO: add functionality
