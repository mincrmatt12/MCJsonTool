import json

from PyQt5.QtWidgets import QWidget

from mcjsontool.resource.workspace import ResourceLocation
from .baseplugin import BasePlugin, register_plugin


@register_plugin
class AdvancementPlugin(BasePlugin):
    def __init__(self, file_location, workspace):
        super().__init__(file_location, workspace)
        pass # todo: load advancement from json (file location can be passed to workspace.get_file)

    @classmethod
    def get_additional_models_for_navigator(cls):
        # todo: add custom model for this, for the advancements tab
        return []

    def get_ui_widget(self):
        return QWidget()  # temp

    @classmethod
    def handles_file(cls, file_location, workspace):
        if type(file_location) is not ResourceLocation:
            file_location = ResourceLocation.from_real_path(file_location)
        if not file_location.data[1].startswith("advancements"):
            return False
        try:
            with workspace.get_file(file_location, "r") as f:
                dat = json.load(f)
                return "criteria" in dat
        except json.JSONDecodeError:
            return False
