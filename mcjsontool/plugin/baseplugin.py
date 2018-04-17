import abc
from PyQt5.QtWidgets import QWidget


class BasePlugin(metaclass=abc.ABCMeta):
    """
    The MCJsonTool system uses plugins to classify each kind of json to be edited. Each open file has an associated
    plugin to define how to draw its ui and various other things

    To create one, subclass BasePlugin
    """

    PLUGIN_TYPES = [

    ]

    def __init__(self, file_location, workspace):
        self.file_location = file_location
        self.workspace = workspace
        pass

    @classmethod
    def get_additional_models_for_navigator(cls):
        """
        Get a list of additional QAbstractItemModels to add to the navigator.
        Your model must:
            - give data using the UserRole containing a path to the content, to handle double-click
            - take a workspace as its only constructor parameter
            - provide a function called tabName() which returns the tab name

        :return: list of additional models (can be empty)
        """
        return []

    def get_ui_widget(self) -> QWidget:
        """
        Get the Qt widget that this plugin will show.

        :return: A QWidget
        :rtype: QWidget
        """
        return None  # abstract


def register_plugin(plugin):
    """
    Register a plugin

    Used like this:

    >>> @register_plugin
    ... class MyPlugin(BasePlugin):
    ...     pass # class code here

    :param plugin: the plugin to register (usually passed with a decorator)
    :return: the plugin, again to conform with decorators
    """
    BasePlugin.PLUGIN_TYPES.append(plugin)
    return plugin
