import sys
from PyQt5.QtWidgets import QApplication
from mcjsontool.ui.ui import JSONToolUI

# debug

from mcjsontool.resource.fileloaders import JarFileProvider
from mcjsontool.resource.workspace import Workspace

workspace = Workspace("test workspace", 0)
workspace.providers.append(JarFileProvider(r"C:\Users\matth\AppData\Roaming\.minecraft\versions\1.12\1.12.jar"))

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # temp: setup temp workspac

    w = JSONToolUI()
    w.navWidget.setWorkspace(workspace)
    w.show()

    sys.exit(app.exec_())
