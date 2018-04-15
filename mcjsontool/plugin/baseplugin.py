class BasePlugin:
    """
    The MCJsonTool system uses plugins to classify each kind of json to be edited. Each open file has an associated
    plugin to define how to draw its ui and various other things

    To create one, subclass BasePlugin
    """
    def __init__(self):