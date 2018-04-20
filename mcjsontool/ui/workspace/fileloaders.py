import pathlib

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, QPushButton, QFileDialog

from mcjsontool.resource.fileloaders import FolderFileProvider, JarFileProvider


class FolderEditWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout()

        self.label = QLabel(self)
        self.label.setText("Folder Source")
        self.label.setAlignment(Qt.AlignHCenter)

        self.layout.addWidget(self.label)
        self.layout.addStretch()

        self.layout2 = QHBoxLayout()
        self.label2 = QLabel(self)
        self.label2.setText("Path to asset folder (should contain a folder called assets)")
        self.lineEdit = QLineEdit(self)
        self.browseButton = QPushButton("...", self)

        self.layout2.addWidget(self.label2)
        self.layout2.addWidget(self.lineEdit)
        self.layout2.addWidget(self.browseButton)

        self.browseButton.clicked.connect(self.on_browse)

        self.layout.addLayout(self.layout2)
        self.setLayout(self.layout)

    def is_valid(self):
        return pathlib.Path(self.lineEdit.text()).exists()

    def create_provider(self):
        return FolderFileProvider(self.lineEdit.text())

    def __str__(self):
        return f"Folder: {self.lineEdit.text()}"

    @pyqtSlot()
    def on_browse(self):
        filepath = QFileDialog.getExistingDirectory(parent=self, caption="Select path to folder")
        if filepath:
            self.lineEdit.setText(filepath)


class JarEditWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout()

        self.label = QLabel(self)
        self.label.setText("Jarfile Source")
        self.label.setAlignment(Qt.AlignHCenter)

        self.layout.addWidget(self.label)
        self.layout.addStretch()

        self.layout2 = QHBoxLayout()
        self.label2 = QLabel(self)
        self.label2.setText("Path to jarfile")
        self.lineEdit = QLineEdit(self)
        self.browseButton = QPushButton("...", self)

        self.layout2.addWidget(self.label2)
        self.layout2.addWidget(self.lineEdit)
        self.layout2.addWidget(self.browseButton)

        self.browseButton.clicked.connect(self.on_browse)
        self.layout.addLayout(self.layout2)
        self.setLayout(self.layout)

    def is_valid(self):
        return pathlib.Path(self.lineEdit.text()).exists()

    def create_provider(self):
        return JarFileProvider(self.lineEdit.text())

    def __str__(self):
        return f"JAR: {self.lineEdit.text()}"

    @pyqtSlot()
    def on_browse(self):
        filepath, *a = QFileDialog.getOpenFileName(parent=self, caption="Select path to jar",
                                                   filter="Jarfile (*.jar)")
        if filepath:
            self.lineEdit.setText(filepath)
