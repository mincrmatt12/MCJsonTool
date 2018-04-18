import ctypes
import glm
import numpy as np
import functools
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QOpenGLContext, QOpenGLVertexArrayObject, QOpenGLBuffer, QOpenGLTexture, \
    QOpenGLShaderProgram, QOpenGLShader, QSurface, QOpenGLVersionProfile, QMatrix4x4, QSurfaceFormat
import OpenGL.GL as GL

from mcjsontool.render.model import BlockModel


class OffscreenModelRendererThread(QThread):
    renderedTexture = pyqtSignal(str, QImage)


class ModelRenderer(QObject):
    """
    The ModelRenderer wraps an opengl context so you can draw models to it. Currently supports blockmodels.

    You need: an opengl surface, an opengl context and a workspace instance.
    """
    def __init__(self, ogl_context: QOpenGLContext, workspace, surface: QSurface):
        super().__init__()

        self.ogl_context = ogl_context
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

        self.proj_mat = glm.perspective(1.57, self.surf.size().width()/self.surf.size().height(), 0.1, 100)

    def setup_data_for_block_model(self, model: BlockModel):
        """
        Setup the vbo & texture for a block model

        todo: optimize for repeats

        You probably should call render after using this function
        :param model: the blockmodel to setup for
        """
        self.current_model = model
        atlas = model.create_model_atlas(self.workspace)
        self.texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, atlas.size[0], atlas.size[1], 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, atlas.data)
        verts, uvs = model.compile_to_vertex_list(atlas)
        verts = list(map(lambda x: list(x), verts))
        uvs = list(map(lambda x: list(x), uvs))
        GL.glBindVertexArray(self.vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        self.array1 = np.array(verts, dtype=np.float32).ravel()
        self.array2 = np.array(uvs, dtype=np.float32).ravel()
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.array1.size*4, self.array1, GL.GL_DYNAMIC_DRAW)
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
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)

    def draw_loaded_model(self, view_matrix, transform_name):
        """
        Draw the loaded model with transforms and view

        :param view_matrix: View matrix (y should be up)
        :param transform_name: Transform name in model
        """
        self.ogl_context.makeCurrent(self.surf)
        # print("shader_l", GL.glGetError())

        if self.current_model is None:
            raise ValueError("No model is loaded!")

        self._plumb_shader_for(self.proj_mat * view_matrix, self.current_model.transforms[transform_name])
        GL.glBindVertexArray(self.vao)

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, len(self.array))

    def resize(self, width, height):
        """
        Resize the modelRenderer to acommodate for differing aspect ratios
        """
        self.proj_mat = glm.perspective(1.57, width/height, 0.1, 100)
