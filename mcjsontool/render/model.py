import json

from ..resource.workspace import Workspace, DomainResourceLocation


class BlockModel:
    """
    A BlockModel holds a full definition for a block.

    This definition includes:
        - a list of cubes (elements)
        - texture variables and resourcelocations (if defined)
        - transforms

    When rendering a block model, you need:
        - a ModelAtlas (use create_model_atlas)
        - list of vertices and uvs
    """
    def __init__(self):
        self.cubes = None
        self.textures = {}
        self.transforms = {}

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
        self._update_textures()  # make sure references are good

        self.transforms.update(parent.transforms)  # although transforms are represented differently,
        # we still override them

    def _update_textures(self):
        """
        Updates texture references
        """

        did_something = False

        for i in self.textures:
            if type(i) is str:
                if i.startswith("#"):
                    ref_name = i[1:]
                    if ref_name in self.textures:
                        self.textures[i] = self.textures[ref_name]
                        did_something = True
                else:
                    self.textures[i] = DomainResourceLocation("textures", self.textures[i])
                    did_something = True
        if did_something:
            self._update_textures()  # call recursively until nothing can be done.

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
            if "parent" in json_data:
                parent = BlockModel.load_from_file(workspace, DomainResourceLocation("models", json_data["parent"]))
