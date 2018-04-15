import math
import numpy as np

from ..resource.workspace import Workspace
from PIL import Image
import io


class Texture:
    """
    Holds a texture with width, height and its texture data in rgba.
    """
    def __init__(self):
        self.w = 0
        self.h = 0
        self.data = None  # i = y * (w * 4) + x * 4 = (r, g, b, a)

    @classmethod
    def load_from_file(cls, workspace, location, enforce_square=True):
        """
        Load a texture from a file

        :param enforce_square: if true, crop image to square (eliminates problems in things like animated textures)
        :param workspace: workspace to load from
        :type workspace: Workspace

        :param location: location of file
        :return:
        """
        with workspace.get_file(location, 'rb') as f:
            im: Image.Image = Image.open(io.BytesIO(f.read()))
        im.load()
        self = cls()

        if im.width != im.height and enforce_square:
            # for now we just crop out animation frames
            im.crop((0, 0, im.width-1, im.width-1))

        self.w = im.width
        self.h = im.height
        if len(im.getbands()) == 3:
            im.putalpha(255)
        self.data = im.tobytes()


class ModelAtlas:
    TEX_SIZE = 128

    """
    A ModelAtlas holds a bunch of textures on a grid, so the shader only needs one texture per block.

    Representation is a grid of 16x16 textures. (animated textures only use their first frame)
    Size is calculated once, and drawn at construction. Otherwise similar api to a :py:class:`Texture`.
    """

    def __init__(self, textures):
        """
        Create a new ModelAtlas

        :param textures: dictionary of names to :py:class:`Texture` instances
        """
        self.textures = textures
        self.data = None
        self.size = [-1, -1]
        self._positions = {}

        self._layout()

    def _subgrid_layout(self, smaller, new_size, small_size, extra=()):
        """
        Layout a subgrid

        :param smaller: list of smaller tiles
        :param new_size: size to pack to
        :param small_size: incoming size
        :param extra: things that are already new_size
        :return: list of locations
        """

        size_factor = new_size / small_size
        grids = [
            []
        ]

        c_pos = [0, 0]

        for i in smaller:
            grids[-1].append((i, c_pos.copy()))
            c_pos[0] += small_size
            if c_pos[0] == size_factor * small_size:
                c_pos[1] += small_size
                c_pos[0] = 0
            if c_pos[1] == size_factor * small_size:
                grids.append([])
                c_pos = [0, 0]

        if not grids[-1]:
            grids = grids[:-1]

        for i in extra:
            grids.append([(i, [0, 0])])

        return grids

    def _blit(self, texture, to):
        """
        Blit a texture to the atlas. Also updates the entry in the _positions table

        .. danger:
            Only works while laying out, i.e. when the array is 3d

        :param texture: blit me
        :param to: here
        """
        self._positions[texture] = to
        self.data[to[1]:to[1]+self.textures[texture].h, to[0]:to[0]+self.textures[texture].w] = \
            np.array(self.textures[texture].data).reshape((self.textures[texture].h, self.textures[texture].w, 4))
        # that crazy thing does a blit with numpy magic (maybe) (hopefully)

    def _draw_grid(self, c_pos, grid):
        """
        Recursively draw this grid, starting at c_pos

        :param c_pos: start at
        :param grid: draw this
        """
        for element in grid:
            to_draw, at = element
            a_pos = c_pos[0] + at[0], c_pos[1] + at[1]
            if type(to_draw) is str:
                self._blit(to_draw, a_pos)
            else:
                self._draw_grid(a_pos, grid)

    def _layout(self):
        """
        Layout the modelatlas
        """

        size_filtered = {}
        sizes = []
        for i in self.textures:
            if self.textures[i].w in size_filtered:
                size_filtered[self.textures[i].w].append(i)
            else:
                size_filtered[self.textures[i].w] = [i]
                sizes.append(self.textures[i].w)
        sizes.sort()
        grids = []
        previous_size = sizes[0]
        for i in sizes:
            grids = self._subgrid_layout(grids, i, previous_size, size_filtered[i])
            previous_size = i

        h_size = len(grids)*sizes[-1]
        row_count = ModelAtlas.TEX_SIZE // h_size
        if row_count < 1:
            row_count = 1
        h_size = row_count * sizes[-1]
        columns = math.ceil(len(grids)/h_size)

        self.data = np.zeros((h_size, columns*sizes[-1], 4))

        c_pos = [0, 0]
        for i in grids:
            self._draw_grid(c_pos, i)
            c_pos[0] += sizes[-1]
            if c_pos[0] == h_size:
                c_pos[0] = 0
                c_pos[1] += sizes[-1]

        self.data = self.data.reshape(4*h_size*columns*sizes[-1])
        self.size = [h_size, columns*sizes[-1]]

    def uv_for(self, tex, u, v):
        """
        Get the UV for a texture in this atlas

        :param tex: texture name
        :param u: u, in pixels
        :param v: v, in pixels
        :return: U, V (floats)
        """
        c_pos = self._positions[tex]
        a_pos = c_pos[0] + u, c_pos[1] + v
        return a_pos[0] / self.size[0], a_pos[1] / self.size[1]
