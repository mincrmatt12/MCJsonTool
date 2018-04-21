from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QWizard, QMessageBox, QFileDialog, QDialog, QInputDialog, QAbstractItemView, QVBoxLayout, \
    QWidget

from mcjsontool.resource import fileloaders
from mcjsontool.resource.workspace import Workspace
from .workspacewizard_ui import Ui_Wizard


class WorkspaceWizard(QWizard, Ui_Wizard):
    newWorkspaceEmitted = pyqtSignal(Workspace, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)
        self.workspaceObject = None

        self.locationBrowse.clicked.connect(self.browseButtonCB)
        self.edit_widgets = []

        self.settingsList.setSelectionMode(QAbstractItemView.SingleSelection)
        self.settingsList.currentRowChanged.connect(self.newSelection)
        self.addButton.clicked.connect(self.addEditWidget)
        self.removeButton.clicked.connect(self.removeEditWidget)
        self.finished.connect(self.on_finish)
        self.selected = None

    @pyqtSlot()
    def addEditWidget(self):
        list_ = [x.__name__ for x in fileloaders.fileloaders]
        user_select, ok = QInputDialog.getItem(self, "Select source type", "Please select a source type from the options below", list_, editable=False)
        if ok:
            i = list_.index(user_select)
            edit_widget = fileloaders.fileloaderui[i].create_edit_widget(self.settingsBox)
            self.edit_widgets.append(edit_widget)
            self.update_list()

    @pyqtSlot(int)
    def newSelection(self, x):
        if 0 <= x < len(self.edit_widgets):
            if self.settingsBox.layout() is None:
                layout = QVBoxLayout()
                layout.addWidget(self.edit_widgets[x])
                self.selected = self.edit_widgets[x]
                self.settingsBox.setLayout(layout)
            else:
                self.settingsBox.layout().removeWidget(self.selected)
                self.selected: QWidget
                self.selected.setParent(self)
                self.settingsBox.layout().addWidget(self.edit_widgets[x])
                self.selected = self.edit_widgets[x]
                self.update()

    @pyqtSlot()
    def removeEditWidget(self):
        if self.settingsList.selectedIndexes():
            i = self.settingsList.selectedIndexes()[0].row()
            del self.edit_widgets[i]
            self.update_list()

    def update_list(self):
        self.settingsList.clear()
        for i in self.edit_widgets:
            self.settingsList.addItem(str(i))

    @pyqtSlot()
    def browseButtonCB(self):
        filepath, *a = QFileDialog.getSaveFileName(parent=self, caption="Select path to save workspace", filter="Workspaces (*.mcjtwp)")
        if filepath:
            self.locationEdit.setText(filepath)

    @pyqtSlot(int)
    def on_finish(self, result):
        if result == QDialog.Rejected:
            return
        else:
            workspace = Workspace(self.nameEdit.text(), Workspace.EDITMODE_EDIT if self.editMode.isChecked() else Workspace.EDITMODE_RESOURCEPACK)
            for i in self.edit_widgets:
                workspace.providers.append(i.create_provider())
            workspace.refresh_file_cache(wait_for_complete=False)
            workspace.save_to_file(self.locationEdit.text())
            self.newWorkspaceEmitted.emit(workspace, self.locationEdit.text())

    def validateCurrentPage(self):
        if self.currentPage() == self.nameTypePage:
            if self.nameEdit.text() is not "" and self.locationEdit.text() is not "":
                return True
            else:
                # noinspection PyCallByClass
                QMessageBox.critical(self, "Error", "Please fill in all fields.")
                return False
        elif self.currentPage() == self.sourcesPage:
            if all((x.is_valid() for x in self.edit_widgets)):
                return True
            else:
                QMessageBox.critical(self, "Error", "Please fill in all fields (make sure you check all sources)")
                return False
        return True
