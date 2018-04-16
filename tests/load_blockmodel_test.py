from mcjsontool.resource.workspace import Workspace, ResourceLocation
from mcjsontool.resource.fileloaders import JarFileProvider
from mcjsontool.render.model import BlockModel

workspace = Workspace("test workspace", 0)
workspace.providers.append(JarFileProvider(r"C:\Users\matth\AppData\Roaming\.minecraft\versions\1.12\1.12.jar"))

a = BlockModel.load_from_file(workspace, ResourceLocation("minecraft", "models/block/andesite.json"))