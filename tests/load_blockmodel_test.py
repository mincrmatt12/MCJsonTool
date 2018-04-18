import glm

from OpenGL import GL
from PyQt5.QtCore import pyqtSlot, QTimer
from PyQt5.QtGui import QOpenGLWindow, QSurface, QSurfaceFormat
from PyQt5.QtWidgets import QOpenGLWidget, QApplication

from mcjsontool.render.glrender import ModelRenderer
from mcjsontool.resource.workspace import Workspace, ResourceLocation
from mcjsontool.resource.fileloaders import JarFileProvider
from mcjsontool.render.model import BlockModel

workspace = Workspace("test workspace", 0)
workspace.providers.append(JarFileProvider(r"C:\Users\matth\AppData\Roaming\.minecraft\versions\1.12\1.12.jar"))

a = BlockModel.load_from_file(workspace, ResourceLocation("minecraft", "models/block/acacia_fence_gate_open.json"))
all_models = workspace.list_files()
all_models = list(filter(lambda x: "models/block" in x, all_models))

class MyOPENGL(QOpenGLWindow):
    def __init__(self, *__args):
        super().__init__(*__args)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timer_fired)
        self.timer.start(100)

    def initializeGL(self):
        #print("A"
        self.renderer = ModelRenderer(workspace, self)
        #GL.glDepthFunc(GL.GL_LESS)
        self. i = 0

    def paintGL(self):
        print("A")
        GL.glClearColor(0, 0, 0, 0)
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT | GL.GL_COLOR_BUFFER_BIT)
        a = BlockModel.load_from_file(workspace, all_models[self.i])
        self.i += 1
        try:
            self.renderer.setup_data_for_block_model(a)
            self.renderer.draw_loaded_model(glm.lookAt(glm.vec3(20, 20, 20), glm.vec3(8, 8, 8), glm.vec3(0, 1, 0)),None)
        except:
            return

    @pyqtSlot()
    def timer_fired(self):
        self.update()


app = QApplication([])
format = QSurfaceFormat()
format.setVersion(4, 3)
format.setDepthBufferSize(24)
format.setProfile(QSurfaceFormat.CoreProfile)
QSurfaceFormat.setDefaultFormat(format)
a_ = MyOPENGL()
a_.show()
app.exec_()
