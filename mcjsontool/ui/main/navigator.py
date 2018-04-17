import pathlib

from PyQt5.QtCore import QAbstractItemModel, Qt, QVariant, QModelIndex, pyqtSlot, QSortFilterProxyModel
from PyQt5.QtWidgets import QWidget, QTabWidget, QTreeView, QVBoxLayout, QSizePolicy

from mcjsontool.resource.workspace import ResourceLocation, Workspace
from ...plugin.baseplugin import BasePlugin


class FileModel(QAbstractItemModel):
    class FileModelNode:
        def __init__(self, parent, resourcelocation, text):
            self.parent = parent
            self.resourcelocation = resourcelocation
            self.text = text

        def __len__(self):
            return 0

        def childAtRow(self, row):
            raise IndexError("Bad")

        def row(self):
            if self.parent:
                return self.parent.children.index(self)
            return 0

    class FolderOrDomainModelNode(FileModelNode):
        def __init__(self, parent, name):
            super(FileModel.FolderOrDomainModelNode, self).__init__(parent, name, name)
            self.children = []

        def __len__(self):
            return len(self.children)

        def childAtRow(self, row):
            return self.children[row]

    def __init__(self, workspace):
        super().__init__()
        self.workspace = workspace
        self.workspace.refresh_file_cache()  # make sure files are up to date
        self.root = FileModel.FolderOrDomainModelNode(None, "root node")

        resources = map(ResourceLocation.from_real_path, workspace.list_files())
        hives = {}
        for i in resources:
            if i.data[0] not in hives:
                hives[i.data[0]] = []
            hives[i.data[0]].append(i)

        for entry in hives:
            root = FileModel.FolderOrDomainModelNode(self.root, entry)
            self.root.children.append(root)
            nodes = {"": root}

            for resource in hives[entry]:
                split_up = pathlib.Path(resource.data[1]).parts
                basename = ""
                parent_ = ""
                for i in split_up[:-1]:
                    parent_ = basename
                    if basename != "":
                        basename += "/"
                    basename += i
                    if basename not in nodes:
                        new_node = FileModel.FolderOrDomainModelNode(nodes[parent_], i)
                        nodes[parent_].children.append(new_node)
                        nodes[basename] = new_node
                node = nodes[basename]
                node.children.append(FileModel.FileModelNode(node, resource, split_up[-1]))

    def flags(self, index):
        n = self.nodeFromIndex(index)
        if n is None:
            return 0
        if type(n) is FileModel.FileModelNode:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        else:
            return Qt.ItemIsEnabled

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        node = self.nodeFromIndex(index)
        if role == Qt.DisplayRole:
            return QVariant(node.text)
        elif role == Qt.EditRole:
            return QVariant(node.text)
        elif role == Qt.UserRole and type(node) is FileModel.FileModelNode:
            return QVariant(node.resourcelocation)
        else:
            return QVariant()

    def headerData(self, p_int, Qt_Orientation, role=None):
        if Qt_Orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant("Name")
        return QVariant()

    def columnCount(self, parent=None, *args, **kwargs):
        return 1

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.nodeFromIndex(parent))

    def parent(self, index=None):
        if not index.isValid():
            return QModelIndex()
        child = index.internalPointer()
        parent = child.parent

        if parent == self.root:
            return QModelIndex()
        return self.createIndex(parent.row(), 0, parent)

    def nodeFromIndex(self, index):
        if index.isValid():
            return index.internalPointer()
        else:
            return self.root

    def index(self, p_int, p_int_1, parent=None, *args, **kwargs):
        assert self.root
        branch = self.nodeFromIndex(parent)
        assert branch is not None
        return self.createIndex(p_int, p_int_1, branch.childAtRow(p_int))

    def tabName(self):
        return "Files"


class NavigatorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.tab_view = QTabWidget(self)
        self.tab_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.layout.addWidget(self.tab_view)
        self.setLayout(self.layout)

    @pyqtSlot(Workspace)
    def setWorkspace(self, w):
        self.workspace = w
        self.models = [FileModel(w)]
        for i in BasePlugin.PLUGIN_TYPES:
            self.models.extend(
                [x(w) for x in i.get_additional_models_for_navigator()]
            )
        self._add_tabs()

    def _add_tabs(self):
        self.tab_view.clear()
        for i in self.models:
            tree_widget = QTreeView(self)
            proxy = QSortFilterProxyModel(self)
            proxy.setSourceModel(i)
            tree_widget.setModel(proxy)
            tree_widget.setSortingEnabled(True)
            self.tab_view.addTab(tree_widget, i.tabName())
