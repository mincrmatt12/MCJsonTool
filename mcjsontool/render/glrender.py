from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QOpenGLContext, QOpenGLVertexArrayObject, QOpenGLBuffer, QOpenGLTexture

from mcjsontool.render.model import BlockModel


class OffscreenModelRenderer(QThread):
    renderedTexture = pyqtSignal(str, QImage)


class ModelRenderer(QObject):
    def __init__(self, ogl_context: QOpenGLContext, workspace):
        super().__init__()

        self.ogl_context = ogl_context
        self.vao = QOpenGLVertexArrayObject(self)

        self.vbo_pos = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
        self.vbo_uv = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
        self.texture = None
        self.workspace = workspace

    def setup_data_for_block_model(self, model: BlockModel):
        atlas = model.create_model_atlas(self.workspace)
        self.texture = QOpenGLTexture(QOpenGLTexture.Target2D)
        self.texture.setMinificationFilter(QOpenGLTexture.Nearest)
        self.texture.setMagnificationFilter(QOpenGLTexture.Nearest)
        self.texture.setSize(*atlas.size)
        self.texture.setFormat(QOpenGLTexture.RGBA8U)
        self.texture.allocateStorage()
        #self.texture.setData(0, ) # should set data