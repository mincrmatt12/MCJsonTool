import sys

from PyQt5.QtGui import QSurfaceFormat
from PyQt5.QtWidgets import QApplication
from mcjsontool.ui.ui import JSONToolUI
import mcjsontool.plugin

if __name__ == "__main__":
    app = QApplication(sys.argv)
    format_ = QSurfaceFormat()
    format_.setVersion(4, 3)
    format_.setDepthBufferSize(24)
    format_.setProfile(QSurfaceFormat.CoreProfile)
    QSurfaceFormat.setDefaultFormat(format_)
    # temp: setup temp workspac

    w = JSONToolUI()
    w.show()

    sys.exit(app.exec_())
