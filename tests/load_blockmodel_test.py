import glm

from OpenGL import GL
from PyQt5.QtGui import QOpenGLWindow, QSurface, QSurfaceFormat
from PyQt5.QtWidgets import QOpenGLWidget, QApplication

from mcjsontool.render.glrender import ModelRenderer
from mcjsontool.resource.workspace import Workspace, ResourceLocation
from mcjsontool.resource.fileloaders import JarFileProvider
from mcjsontool.render.model import BlockModel

workspace = Workspace("test workspace", 0)
workspace.providers.append(JarFileProvider(r"C:\Users\matth\AppData\Roaming\.minecraft\versions\1.12\1.12.jar"))

a = BlockModel.load_from_file(workspace, ResourceLocation("minecraft", "models/block/dark_oak_inner_stairs.json"))


class MyOPENGL(QOpenGLWindow):
    def initializeGL(self):
        #print("A"
        self.renderer = ModelRenderer(self.context(), workspace, self)
        self.renderer.setup_data_for_block_model(a)
        #GL.glDepthFunc(GL.GL_LESS)

    def paintGL(self):
        print("A")
        GL.glClearColor(1, 0, 0, 1)
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT | GL.GL_COLOR_BUFFER_BIT)
        self.renderer.draw_loaded_model(glm.lookAt(glm.vec3(-32, 32, -32), glm.vec3(0, 0, 0), glm.vec3(0, 1, 0)), None)


app = QApplication([])
format = QSurfaceFormat()
format.setVersion(4, 3)
format.setDepthBufferSize(24)
format.setProfile(QSurfaceFormat.CoreProfile)
QSurfaceFormat.setDefaultFormat(format)
a_ = MyOPENGL()
a_.show()
app.exec_()
