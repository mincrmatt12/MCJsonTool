import ctypes
import glm

import OpenGL.GL as GL
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QObject, pyqtSlot
from PyQt5.QtGui import QImage, QOpenGLContext, QOpenGLShaderProgram, QOpenGLShader, QSurface, QOpenGLVersionProfile, \
    QOffscreenSurface, QSurfaceFormat
from queue import Queue

from mcjsontool.render.model import BlockModel
from mcjsontool.resource.workspace import Workspace


class OffscreenModelRendererThread(QThread):
    TEX_SIZE = 128
    renderedTexture = pyqtSignal(str, QImage)

    def __init__(self, parent_screen):
        super().__init__()
        self.parent_screen = parent_screen
        self.started.connect(self.started_)
        self.workspace = None
        self.offscreen_surface = QOffscreenSurface()
        self.offscreen_surface.requestedFormat().setVersion(4, 3)
        self.offscreen_surface.requestedFormat().setProfile(QSurfaceFormat.CoreProfile)
        self.offscreen_surface.requestedFormat().setDepthBufferSize(24)
        self.offscreen_surface.setFormat(self.offscreen_surface.requestedFormat())
        self.offscreen_surface.create()

    @pyqtSlot()
    def started_(self):
        self.ctx = QOpenGLContext(self.offscreen_surface)
        self.ctx.setFormat(self.offscreen_surface.requestedFormat())
        self.ctx.create()
        self.fbo = -1
        self.tex = -1
        self.rbuf = -1
        self.setup_fbo()

        self.renderer = ModelRenderer(self.workspace, self.offscreen_surface)

    @pyqtSlot(Workspace)
    def setWorkspace(self, w):
        if hasattr(self, "renderer"):
            self.renderer.set_workspace(w)
        else:
            self.workspace = w

    def setup_fbo(self):
        self.ctx.makeCurrent(self.offscreen_surface)
        self.tex = GL.glGenTextures(1)
        self.fbo = GL.glGenFramebuffers(1)
        self.rbuf = GL.glGenRenderbuffers(1)

        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, OffscreenModelRendererThread.TEX_SIZE,
                        OffscreenModelRendererThread.TEX_SIZE, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, None)

        GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, self.rbuf)
        GL.glRenderbufferStorage(GL.GL_RENDERBUFFER, GL.GL_DEPTH_COMPONENT24, OffscreenModelRendererThread.TEX_SIZE,
                                 OffscreenModelRendererThread.TEX_SIZE)

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo)
        GL.glFramebufferRenderbuffer(GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT, GL.GL_RENDERBUFFER, self.rbuf)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, self.tex, 0)
        if GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER) != GL.GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("Framebuffer is not complete!")
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)

    @pyqtSlot(str, BlockModel)
    def queue_render_order(self, order_name, model):
        """
        Render a block model in item format. Subscribing (connecting) to the renderedTexture signal allows you to get the rendered texture back.

        Pass in an order name so you know which image you got back

        :param order_name: the order name. passed to renderedTexture
        :param model: the blockmodel
        :return:
        """
        self.ctx.makeCurrent(self.offscreen_surface)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo)
        GL.glViewport(0, 0, OffscreenModelRendererThread.TEX_SIZE, OffscreenModelRendererThread.TEX_SIZE)
        GL.glClearColor(0, 0, 0, 0)
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT | GL.GL_COLOR_BUFFER_BIT)
        self.renderer.setup_data_for_block_model(model)
        self.renderer.resize(OffscreenModelRendererThread.TEX_SIZE, OffscreenModelRendererThread.TEX_SIZE)
        self.renderer.draw_loaded_model(glm.lookAt(glm.vec3(15, 5, 5), glm.vec3(5, 5, 5), glm.vec3(0, 1, 0)), "gui",
                                        glm.ortho(-10, 10, 10, -10, 0.1, 50))
        tex_str = GL.glReadPixels(0, 0, OffscreenModelRendererThread.TEX_SIZE, OffscreenModelRendererThread.TEX_SIZE,
                                  GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, outputType=bytes)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        qimage = QImage(tex_str, OffscreenModelRendererThread.TEX_SIZE, OffscreenModelRendererThread.TEX_SIZE,
                        OffscreenModelRendererThread.TEX_SIZE * 4, QImage.Format_RGBA8888)
        qimage = qimage.mirrored(vertical=True)
        self.renderedTexture.emit(order_name, qimage)


class ModelRenderer(QObject):
    """
    The ModelRenderer wraps an opengl context so you can draw models to it. Currently supports blockmodels.

    You need: an opengl surface, an opengl context and a workspace instance.
    """

    def __init__(self, workspace, surface: QSurface):
        super().__init__()

        self.surf = surface
        prof = QOpenGLVersionProfile()
        prof.setVersion(2, 0)

        self.vao = GL.glGenVertexArrays(1)
        self.vbo, self.vbo2 = GL.glGenBuffers(2)

        self.texture = -1
        self.current_model: BlockModel = None
        self.workspace = workspace

        self.array1, array2 = None, None

        self.shader = QOpenGLShaderProgram()
        self.shader.addShaderFromSourceFile(QOpenGLShader.Vertex, "shader/block.vertex.glsl")
        self.shader.addShaderFromSourceFile(QOpenGLShader.Fragment, "shader/block.fragment.glsl")
        self.shader.link()

        self.proj_mat = glm.perspective(1.57, self.surf.size().width() / self.surf.size().height(), 0.1, 100)
        self.texture = GL.glGenTextures(1)

    def set_workspace(self, workspace):
        self.workspace = workspace

    def setup_data_for_block_model(self, model: BlockModel):
        """
        Setup the vbo & texture for a block model

        todo: optimize for repeats

        You probably should call render after using this function
        :param model: the blockmodel to setup for
        """
        self.current_model = model
        print(self.workspace)
        atlas = model.create_model_atlas(self.workspace)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, atlas.size[0], atlas.size[1], 0, GL.GL_RGBA,
                        GL.GL_UNSIGNED_BYTE, atlas.data)
        verts, uvs = model.compile_to_vertex_list(atlas)
        verts = list(map(lambda x: list(x), verts))
        uvs = list(map(lambda x: list(x), uvs))
        GL.glBindVertexArray(self.vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        self.array1 = np.array(verts, dtype=np.float32).ravel()
        self.array2 = np.array(uvs, dtype=np.float32).ravel()
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.array1.size * 4, self.array1, GL.GL_DYNAMIC_DRAW)
        GL.glEnableVertexAttribArray(0)
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(0, 4, GL.GL_FLOAT, GL.GL_FALSE, 0, ctypes.c_void_p(0))
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo2)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.array1.size * 4, self.array2, GL.GL_DYNAMIC_DRAW)
        GL.glVertexAttribPointer(1, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, ctypes.c_void_p(0))
        GL.glBindVertexArray(0)
        self.array_size = len(verts)
        self.array = verts

    def _plumb_shader_for(self, proj_view: glm.mat4, model_transform):
        self.shader.bind()
        GL.glUniformMatrix4fv(1, 1, GL.GL_FALSE, glm.value_ptr(proj_view))
        GL.glUniformMatrix4fv(0, 1, GL.GL_FALSE, glm.value_ptr(model_transform))
        print(model_transform * self.array[0])
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)

    def draw_loaded_model(self, view_matrix, transform_name, proj=None):
        """
        Draw the loaded model with transforms and view

        :param proj: projection matrix for doing ortho
        :param view_matrix: View matrix (y should be up)
        :param transform_name: Transform name in model
        """
        if self.current_model is None:
            raise ValueError("No model is loaded!")

        if proj is None:
            proj = self.proj_mat

        print(self.current_model.transforms[transform_name])

        self._plumb_shader_for(proj * view_matrix, self.current_model.transforms[transform_name])
        GL.glBindVertexArray(self.vao)

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, len(self.array))

    def resize(self, width, height):
        """
        Resize the modelRenderer to acommodate for differing aspect ratios
        """
        self.proj_mat = glm.perspective(1.57, width / height, 0.1, 100)
