import json
import glm
import math
from typing import List, Tuple

from mcjsontool.render.texture import ModelAtlas, Texture
from ..resource.workspace import Workspace, DomainResourceLocation, ResourceLocation


class Cube:
    """
    Represents one cube in a model

    Faces dictionary contains keys for each side if it is to be drawn.

    MC coordinate system for dummies:
        - east = +x
        - south = +z
        - up = +y

    Faces dictionary refers to (texture_name, uv1, uv2)

    TODO: add rotation support
    """

    AXES = {
        "x": glm.vec3(1, 0, 0),
        "y": glm.vec3(0, 1, 0),
        "z": glm.vec3(0, 0, 1)
    }

    # coord = self.start + self.off * [0] + self.off * [1] * up + self.off * [2] * right
    # last is left/right axis, up/down axis neg means invert start/end
    FACES = {
        "up": (glm.vec3(0, 1, 0), glm.vec3(0, 0, 1), glm.vec3(1, 0, 0), [0, 2], [True, True]),
        "down": (glm.vec3(1, 0, 1), glm.vec3(0, 0, -1), glm.vec3(-1, 0, 0), [0, 2], [False, False]),
        "east": (glm.vec3(1, 0, 0), glm.vec3(0, 1, 0), glm.vec3(0, 0, 1), [1, 2], [True, True]),
        "west": (glm.vec3(0, 1, 1), glm.vec3(0, -1, 0), glm.vec3(0, 0, -1), [1, 2], [False, False]),
        "south": (glm.vec3(0, 0, 1), glm.vec3(0, 1, 0), glm.vec3(1, 0, 0), [1, 0], [True, True]),
        "north": (glm.vec3(1, 1, 0), glm.vec3(0, -1, 0), glm.vec3(-1, 0, 0), [1, 0], [False, False])
    }

    def __init__(self, start, end):
        self.start = glm.vec3(*start)
        self.end = glm.vec3(*end)
        self.off = self.end - self.start
        self.matrix = glm.mat4(1)
        self.faces = {}

    def set_rotation(self, origin, axis, angle, rescale):
        """
        Sets rotation matrix on this cube.

        :param origin: rotation origin
        :param axis: rotation axis
        :param angle: rotation angle
        :param rescale: fixme: currently ignored
        :return:
        """
        self.matrix = glm.translate(glm.mat4(1), -glm.vec3(*origin))
        self.matrix = glm.rotate(self.matrix, math.radians(angle), Cube.AXES[axis])
        self.matrix = glm.translate(self.matrix, glm.vec3(*origin))

    def remove_face(self, face):
        """
        Remove this face from rendering

        :param face: the face name
        """
        del self.faces[face]

    def set_face(self, face, texture, uv1=None, uv2=None):
        """
        Add a face to this cube

        :param face: face name, one of (down, up, north, south, west, east)
        :param texture: texture reference (variable name)
        :param uv1: x1, y1
        :param uv2: x2, y2
        """
        if uv1 is None and uv2 is None:
            dat = Cube.FACES[face]
            uv1 = [
                max(0, min(16, (self.start if dat[4][0] else self.end)[int(abs(dat[3][0]))])),
                max(0, min(16, (self.start if dat[4][1] else self.end)[int(abs(dat[3][1]))])),
            ]
            uv2 = [
                max(0, min(16, (self.start if not dat[4][0] else self.end)[int(abs(dat[3][0]))])),
                max(0, min(16, (self.start if not dat[4][1] else self.end)[int(abs(dat[3][1]))])),
            ]

        self.faces[face] = (texture, uv1, uv2)

    def _transform_vertex_list(self, l: List[glm.vec4]) -> List[glm.vec4]:
        """
        Transform some vertices by this cube's matrix.

        :param l: list
        :return: a new list of vectors
        """
        return list(map(lambda x: self.matrix * x, l))

    def compile_to_vertex_list(self, atlas: ModelAtlas) -> Tuple[List[glm.vec4], List[glm.vec3]]:
        """
        Create a list of vertices from this cube, pre-transformed

        :param atlas: An atlas to use
        :return: List of vertices, list of uvs
        """
        vertices = []
        uvs = []
        for face in self.faces:
            dat = Cube.FACES[face]
            texture, uv1, uv2 = self.faces[face]
            v1 = self.start + (self.off * dat[0])
            v2 = v1 + (self.off * dat[1])
            v3 = v2 + (self.off * dat[2])
            v4 = v1 + (self.off * dat[2])
            vertices.append(glm.vec4(v1, 1))
            uvs.append(atlas.uv_for(texture, uv1[0], uv1[1]))
            vertices.append(glm.vec4(v2, 1))
            uvs.append(atlas.uv_for(texture, uv1[0], uv2[1]))
            vertices.append(glm.vec4(v3, 1))
            uvs.append(atlas.uv_for(texture, uv2[0], uv2[1]))
            vertices.append(glm.vec4(v1, 1))
            uvs.append(atlas.uv_for(texture, uv1[0], uv1[1]))
            vertices.append(glm.vec4(v4, 1))
            uvs.append(atlas.uv_for(texture, uv2[0], uv1[1]))
            vertices.append(glm.vec4(v3, 1))
            uvs.append(atlas.uv_for(texture, uv2[0], uv2[1]))

        return self._transform_vertex_list(vertices), uvs


class BlockModel:
    """
    A BlockModel holds a full definition for a block. BlockModels can also
    be modified by ModelStates to do different things

    This definition includes:
        - a list of cubes (elements)
        - texture variables and resourcelocations (if defined)
        - transforms

    When rendering a block model, you need:
        - a ModelAtlas (use create_model_atlas)
        - list of vertices and uvs
        - a ModelState (optionally)


    """
    def __init__(self):
        self.cubes = None
        self.textures = {}
        self.transforms = {}

    def create_model_atlas(self, workspace) -> ModelAtlas:
        """
        Create a model atlas from this model's textures (configure with a state to get its textures)

        :param workspace: workspace to load textures from
        :return: a model atlas
        """
        self._update_textures()
        return ModelAtlas(self._get_loaded_textures(workspace))

    def compile_to_vertex_list(self, atlas):
        """
        Create a list of vertices from this model. Transforming for desired display is left to other code

        :param atlas: An atlas to use
        :return: List of vertices, list of uvs
        """
        verts, uvs = [], []
        for i in self.cubes:
            nv, nu = i.compile_to_vertex_list(atlas)
            verts.extend(nv)
            uvs.extend(nu)
        return verts, uvs

    def _get_loaded_textures(self, workspace):
        """
        Get a dictionary of all textures in Texture format
        :param workspace: workspace to load from
        :return: dict of textures
        """
        if self.cubes is None:
            usable = list(self.textures.keys())
        else:
            usable = list()
            for cube in self.cubes:
                for face in cube.faces:
                    usable.append(cube.faces[face][0])
            usable = list(set(usable))
        filtered_textures = {k: v for k, v in self.textures.items() if isinstance(v, ResourceLocation) and k in usable}
        if len(filtered_textures) is 0:
            raise ValueError("fail')")
        return {k: Texture.load_from_file(workspace, v, True) for k, v in filtered_textures.items()}

    def apply_state(self, state):
        """
        Apply a ModelState
        :param state: to apply
        :return: a new model with this state
        :rtype: BlockModel
        """
        pass

    def merge_with_parent(self, parent):
        """
        Merges this instance with a parent one in place.

        :param parent: the parent
        :type parent: BlockModel
        """

        # first, check if parent has cubes
        if parent.cubes is not None:
            if self.cubes is None:
                self.cubes = parent.cubes.copy() # only if we don't define cubes do we override

        # next, try to override textures
        new_textures = parent.textures.copy()
        new_textures.update(self.textures)
        self.textures = new_textures
        self._update_textures()  # make sure references are good

        self.transforms.update(parent.transforms)  # although transforms are represented differently,
        # we still override them

    def _update_textures(self):
        """
        Updates texture references
        """

        did_something = False

        for i in self.textures:
            if type(self.textures[i]) is str:
                if self.textures[i].startswith("#"):
                    ref_name = self.textures[i][1:]
                    if ref_name in self.textures:
                        self.textures[i] = self.textures[ref_name]
                        did_something = True
                else:
                    self.textures[i] = DomainResourceLocation("textures", self.textures[i], filetype=".png")
                    did_something = True
        if did_something:
            self._update_textures()  # call recursively until nothing can be done.\

    @classmethod
    def _create_transform_for(cls, rot, scale, trans):
        mat = glm.mat4(1)
        mat = glm.rotate(mat, rot[0], glm.vec3(1, 0, 0))
        mat = glm.rotate(mat, rot[1], glm.vec3(0, 1, 0))
        mat = glm.rotate(mat, rot[2], glm.vec3(0, 0, 1))
        mat = glm.translate(mat, glm.vec3(trans))
        mat = glm.scale(mat, glm.vec3(scale))
        return mat

    @classmethod
    def load_from_file(cls, workspace: Workspace, location):
        """
        Load model from a location

        :param workspace: workspace to load in
        :param location: location/path to model
        :return: a loaded model
        :rtype: BlockModel
        """
        with workspace.get_file(location) as f:
            json_data = json.load(f)
            model = cls()
            if "textures" in json_data:
                model.textures = json_data["textures"]
                model._update_textures()
            if "elements" in json_data:
                model.cubes = []
                for element in json_data["elements"]:
                    cube = Cube(element["from"], element["to"])
                    if "rotation" in element:
                        rotation: dict = element["rotation"]
                        origin = rotation.get("origin", [8, 8, 8])
                        axis = rotation["axis"]
                        angle = rotation.get("angle", 0)
                        rescale = rotation.get("rescale", False)
                        cube.set_rotation(origin, axis, angle, rescale)
                    for face_n, face in element["faces"].items():
                        if "uv" in face:
                            cube.set_face(face_n, face["texture"][1:], face["uv"][:2], face["uv"][2:])
                        else:
                            cube.set_face(face_n, face["texture"][1:])
                    model.cubes.append(cube)
            if "display" in json_data:
                for kind, data in json_data["display"].items():
                    model.transforms[kind] = cls._create_transform_for(data["rotation"], data["scale"], data["translation"])
            model.transforms[None] = glm.mat4(1)
            if "parent" in json_data:
                parent = BlockModel.load_from_file(workspace, DomainResourceLocation("models", json_data["parent"], filetype=".json"))
                model.merge_with_parent(parent)
            return model
