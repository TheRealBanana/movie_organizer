from PyQt5 import QtWidgets, QtCore, QtGui

DB_FIELDS = []

class searchParameterWidget(QtWidgets.QWidget):
    removeSelfRequest = QtCore.pyqtSignal(QtCore.QVariant)

    def __init__(self, fieldlist, parent=None):
        super(searchParameterWidget, self).__init__(parent=parent)
        self.paramType = None # Will use to track which field to use when building SQL queries from these widgets
        self.parent = parent
        self.setupWidget(fieldlist)

    def setupWidget(self, fieldlist):
        self.searchTemplateHLayout = QtWidgets.QHBoxLayout(self)
        self.searchTemplateHLayout.setObjectName("searchTemplateHLayout")
        self.paramSelectionDropdown = QtWidgets.QComboBox(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.paramSelectionDropdown.sizePolicy().hasHeightForWidth())
        self.paramSelectionDropdown.setSizePolicy(sizePolicy)
        self.paramSelectionDropdown.setMinimumSize(QtCore.QSize(20, 0))
        self.paramSelectionDropdown.setObjectName("paramSelectionDropdown")
        self.paramSelectionDropdown.activated["QString"].connect(self.changedFieldType)
        for f in fieldlist:
            self.paramSelectionDropdown.addItem(f)
        self.searchTemplateHLayout.addWidget(self.paramSelectionDropdown)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.searchTemplateHLayout.addItem(spacerItem2)
        self.searchTemplateEntry = QtWidgets.QLineEdit(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.searchTemplateEntry.sizePolicy().hasHeightForWidth())
        self.searchTemplateEntry.setSizePolicy(sizePolicy)
        self.searchTemplateEntry.setMinimumSize(QtCore.QSize(0, 25))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.searchTemplateEntry.setFont(font)
        self.searchTemplateEntry.setClearButtonEnabled(True)
        self.searchTemplateEntry.setObjectName("searchTemplateEntry")
        self.searchTemplateHLayout.addWidget(self.searchTemplateEntry)
        self.searchTemplateRemoveButton = QtWidgets.QPushButton(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.searchTemplateRemoveButton.sizePolicy().hasHeightForWidth())
        self.searchTemplateRemoveButton.setSizePolicy(sizePolicy)
        self.searchTemplateRemoveButton.setMinimumSize(QtCore.QSize(25, 25))
        self.searchTemplateRemoveButton.setMaximumSize(QtCore.QSize(25, 25))
        self.searchTemplateRemoveButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../icons/delete-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.searchTemplateRemoveButton.setIcon(icon)
        self.searchTemplateRemoveButton.setIconSize(QtCore.QSize(16, 16))
        self.searchTemplateRemoveButton.setFlat(True)
        self.searchTemplateRemoveButton.setObjectName("searchTemplateRemoveButton")
        self.searchTemplateRemoveButton.clicked.connect(lambda: self.removeSelfRequest.emit(self))
        self.searchTemplateHLayout.addWidget(self.searchTemplateRemoveButton)

    def changedFieldType(self, fieldname):
        print("Changed field to: %s" % fieldname)