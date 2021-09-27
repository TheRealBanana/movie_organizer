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
        #HLayout to contain our widgets
        self.searchTemplateHLayout = QtWidgets.QHBoxLayout(self)
        self.searchTemplateHLayout.setObjectName("searchTemplateHLayout")

        #First widget is the dropdown to select which param to search with
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

        #AND/OR checkbox. Multiple values can be searched for in a single field by separating them with a semicolon
        #This checkbox controls whether we use AND or OR in our SQL query. OR'ing has been the default behavior.
        self.andorCheckbox = QtWidgets.QCheckBox(self)
        self.andorCheckbox.setToolTip("Checked = multiple entries for this field are AND'd together, unchecked they are OR'd together. ")
        self.searchTemplateHLayout.addWidget(self.andorCheckbox)

        #spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        #self.searchTemplateHLayout.addItem(spacerItem2)

        #Text box entry for selected parameter. In the future this could be dynamically updated for the selected param
        # e.g. dropdown for genre, dual input for number range w/ runtime and year
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

        #Delete button to remove param
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


    def returnData(self):
        #Just simply access to our field value
        return self.searchTemplateEntry.text()

    def andorState(self):
        #return the AND/OR checkbox state
        return "AND" if self.andorCheckbox.isChecked() else "OR"

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