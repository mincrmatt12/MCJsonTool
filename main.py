import sys

from PyQt5.QtGui import QSurfaceFormat
from PyQt5.QtWidgets import QApplication
from mcjsontool.ui.ui import JSONToolUI

# debug

from mcjsontool.resource.fileloaders import JarFileProvider
from mcjsontool.resource.workspace import Workspace

workspace = Workspace("test workspace", 0)
workspace.providers.append(JarFileProvider(r"C:\Users\matth\AppData\Roaming\.minecraft\versions\1.12\1.12.jar"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    format_ = QSurfaceFormat()
    format_.setVersion(4, 3)
    format_.setDepthBufferSize(24)
    format_.setProfile(QSurfaceFormat.CoreProfile)
    QSurfaceFormat.setDefaultFormat(format_)
    # temp: setup temp workspac

    w = JSONToolUI()
    w.setWorkspace(workspace)
    w.show()

    sys.exit(app.exec_())
