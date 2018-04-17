from . import main_ui
from PyQt5.QtWidgets import QMainWindow


class JSONToolUI(QMainWindow, main_ui.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    # MASSIVE TODO: add functionality
