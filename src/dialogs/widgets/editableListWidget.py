# This widget is a combination QListWidget and two QButtons with icons for add and delete.
# Remember to set the QListWidgetItems as editable when you add them
#
# This file uses editableListWidget.ui as a base to start from but thats it.
from PyQt5 import QtCore, QtGui, QtWidgets


# Our special QListWidgetItem that has two text input boxes separated by the word "as"
class specialCharacterListItem(QtWidgets.QWidget):
    def __init__(self, actor_name, character_name, parent=None):
        super(specialCharacterListItem, self).__init__(parent)
        self.actor_name = actor_name
        self.character_name = character_name
        hlayout = QtWidgets.QHBoxLayout(parent)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.actorname_input = QtWidgets.QLineEdit()
        self.actorname_input.setFont(font)
        self.actorname_input.setText(actor_name)
        aslabel = QtWidgets.QLabel("   as   ")
        self.charactername_input = QtWidgets.QLineEdit()
        self.charactername_input.setFont(font)
        self.charactername_input.setText(character_name)
        hlayout.addWidget(self.actorname_input)
        hlayout.addWidget(aslabel)
        hlayout.addWidget(self.charactername_input)
        self.setLayout(hlayout)

class editableListWidget(QtWidgets.QWidget):
    def __init__(self, fieldname, fielddata, parent=None):
        super(editableListWidget, self).__init__(parent)
        # This will either be a simple list of names, or a list of dictionaries
        # The list of dictionaries will have dict_keys(['name', 'character'])
        # For the dictionary entries, we'll have to use a custom QListWidgetItem thats two text entries separated by the word 'as'
        self.fielddata = fielddata
        self.fieldname = fieldname

        # This is the start of the output from pyuic5. If updating this widget, paste the edited code from setupUi() to here.
        self.setObjectName("editableListWidget")
        self.resize(400, 220)
        self.setWindowTitle("")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.listWidget = QtWidgets.QListWidget(self)
        self.listWidget.setProperty("showDropIndicator", False)
        self.listWidget.setDefaultDropAction(QtCore.Qt.IgnoreAction)
        self.listWidget.setAlternatingRowColors(False)
        self.listWidget.setObjectName("listWidget")
        self.horizontalLayout.addWidget(self.listWidget)
        self.verticalLayoutForButtons = QtWidgets.QVBoxLayout()
        self.verticalLayoutForButtons.setObjectName("verticalLayoutForButtons")
        self.addButton = QtWidgets.QPushButton(self)
        self.addButton.setMaximumSize(QtCore.QSize(24, 24))
        self.addButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(".\\../icons/plus-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.addButton.setIcon(icon)
        self.addButton.setObjectName("addButton")
        self.verticalLayoutForButtons.addWidget(self.addButton)
        self.addCharButton = QtWidgets.QPushButton(self)
        self.addCharButton.setMaximumSize(QtCore.QSize(24, 24))
        self.addCharButton.setText("")
        self.addCharButton.hide() # This is only shown for actor lists
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(".\\../icons/plus-icon-blue.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.addCharButton.setIcon(icon1)
        self.addCharButton.setObjectName("addCharButton")
        self.verticalLayoutForButtons.addWidget(self.addCharButton)
        spacerItem = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayoutForButtons.addItem(spacerItem)
        self.removeButton = QtWidgets.QPushButton(self)
        self.removeButton.setMaximumSize(QtCore.QSize(24, 24))
        self.removeButton.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(".\\../icons/delete-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.removeButton.setIcon(icon2)
        self.removeButton.setObjectName("removeButton")
        self.verticalLayoutForButtons.addWidget(self.removeButton)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayoutForButtons.addItem(spacerItem1)
        self.horizontalLayout.addLayout(self.verticalLayoutForButtons)

        # End of pyuic5 paste code section

        self.listWidget.setSortingEnabled(False)

        # Heres how to add a special widget
        """
        item = QtWidgets.QListWidgetItem()
        specwidget = specialCharacterListItem("ACTOR_NAME", "CHAR_NAME")
        self.listWidget.addItem(item)
        item.setSizeHint(specwidget.sizeHint())
        self.listWidget.setItemWidget(item, specwidget)
        """

        self.addButton.clicked.connect(self.addButtonClicked)
        self.addCharButton.clicked.connect(self.addCharButtonClicked)
        self.removeButton.clicked.connect(self.removeButtonClicked)

        self.setupData()

    def setupData(self):
        # If our field name is actors we have to unhide the special button to add characters
        if self.fieldname == "actors":
            self.addCharButton.show()

        if isinstance(self.fielddata[0], str):
            for f in self.fielddata:
                self.addNormalItem(f)
        elif isinstance(self.fielddata[0], dict):
            for d in self.fielddata:
                if isinstance(d, dict):
                    self.addSpecWidget(d["name"], d["character"])
                elif isinstance(d, str):
                    self.addNormalItem(d)
                else:
                    raise(Exception(f"Unexpected type for field (got a {type(d)} for {self.fieldname})"))
        else:
            print("WAT")
            print(type(self.fielddata[0]))

        self.listWidget.clearSelection()

    def addSpecWidget(self, actor_name, char_name, button=False):
        item = QtWidgets.QListWidgetItem()
        specwidget = specialCharacterListItem(actor_name, char_name)
        self.listWidget.addItem(item)
        item.setSizeHint(specwidget.sizeHint())
        self.listWidget.setItemWidget(item, specwidget)
        if button:
            self.listWidget.setCurrentItem(item)
            specwidget.actorname_input.setFocus()
            specwidget.actorname_input.selectAll()

    def addNormalItem(self, data, button=False):
        item = QtWidgets.QListWidgetItem(str(data))
        item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEditable|QtCore.Qt.ItemIsEnabled)
        self.listWidget.addItem(item)
        if button:
            self.listWidget.setCurrentItem(item)
            self.listWidget.editItem(item)

    def addButtonClicked(self):
        self.addNormalItem("", button=True)

    def addCharButtonClicked(self):
        self.addSpecWidget("Actor Name", "Character Name", button=True)

    def removeButtonClicked(self):
        self.listWidget.takeItem(self.listWidget.currentRow())
