from PyQt5 import QtWidgets, QtCore, QtGui


class SearchParameterWidget(QtWidgets.QWidget):
    removeSelfRequest = QtCore.pyqtSignal(QtCore.QVariant)
    searchParamFieldUpdate = QtCore.pyqtSignal((str, str, QtCore.QVariant))

    def __init__(self, parent=None):
        super(SearchParameterWidget, self).__init__(parent=parent)
        self.paramType = None # Will use to track which field to use when building SQL queries from these widgets
        self.parent = parent
        self.currentfield = ""
        self.setupWidget()

    def setupWidget(self):
        self.searchTemplateHLayout = QtWidgets.QHBoxLayout(self)
        self.searchTemplateHLayout.setObjectName("searchTemplateHLayout")
        self.paramSelectionDropdown = QtWidgets.QComboBox(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.paramSelectionDropdown.sizePolicy().hasHeightForWidth())
        self.paramSelectionDropdown.setSizePolicy(sizePolicy)
        self.paramSelectionDropdown.setMinimumSize(QtCore.QSize(90, 0))
        self.paramSelectionDropdown.setObjectName("paramSelectionDropdown")
        self.paramSelectionDropdown.setEditable(False)
        self.paramSelectionDropdown.activated["QString"].connect(self.changedFieldType)
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
        #Combobox starts on a field so we need to remove it from the list of options
        #We could start on a blank but this is nicer. With this system I can keep pressing the add
        #search param button and it will automatically stop adding new fields when the field list is
        #depleted.


    def returnData(self):
        #Just simply access to our field value
        return self.searchTemplateEntry.text()

    def updateFieldList(self, updatedstringlist):
        #Preserve whatever selection we had before because our model will change the indices
        self.paramSelectionDropdown.clear()
        updatedstringlist[self.currentfield] = True
        for field, enabled in updatedstringlist.items():
            if enabled:
                self.paramSelectionDropdown.addItem(field)
        if self.currentfield == "":
            self.changedFieldType(self.paramSelectionDropdown.itemText(0))
        QtWidgets.QApplication.processEvents()
        self.paramSelectionDropdown.setCurrentText(self.currentfield)  # Will only change index if QComboBox.editable==False

    def changedFieldType(self, fieldname):
        self.searchParamFieldUpdate.emit(self.currentfield, fieldname, self)
        self.currentfield = fieldname