from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QFileDialog
from os import getcwd

class OptionsDialogFunctions(QObject):
    saveSettingsRequest = pyqtSignal(dict)

    def __init__(self, widget, ui, settings):
        super(OptionsDialogFunctions, self).__init__(widget.parent())
        self.ui = ui
        self.widget = widget
        self.settings = settings

    def showOptionsDialog(self):
        self.init()
        self.widget.exec_()

    def init(self):
        self.setupConnections()
        self.applySettingsToUi()

    def setupConnections(self):
        self.ui.mainButtonBox.clicked["QAbstractButton*"].connect(self.mainButtonBoxClick)
        self.ui.addFolderButton.clicked.connect(self.addFolderButtonClicked)
        self.ui.deleteFolderButton.clicked.connect(self.deleteFolderButtonClicked)

    def applySettingsToUi(self):
        self.ui.maxThreadsSpinBox.setValue(int(self.settings["threads"]))
        if "library" in self.settings and self.settings["library"] is not None:
            self.ui.folderListWidget.addItems(self.settings["library"])

    def saveNewSettings(self):
        self.settings["threads"] = self.ui.maxThreadsSpinBox.value()
        self.settings["library"] = []
        for x in range(self.ui.folderListWidget.count()):
            self.settings["library"].append(self.ui.folderListWidget.item(x).text())
        self.saveSettingsRequest.emit(self.settings)

    def mainButtonBoxClick(self, button):
        if button.text() == "Save":
            self.saveNewSettings()
            self.widget.accept()
        elif button.text() == "Cancel":
            self.widget.close()
        elif button.text() == "Restore Defaults":
            pass

    def addFolderButtonClicked(self):
        filedialog = QFileDialog()
        filedialog.setAcceptMode(QFileDialog.AcceptOpen)
        filedialog.setFileMode(QFileDialog.DirectoryOnly)
        filedialog.setViewMode(QFileDialog.Detail)
        parent = self.widget
        caption = "Select directory to scan for movies in..."
        startdir = getcwd()
        options = QFileDialog.ShowDirsOnly
        selecteddir = filedialog.getExistingDirectory(parent, caption, startdir, options)
        self.ui.folderListWidget.addItem(selecteddir)



    def deleteFolderButtonClicked(self):
        selected_folder_index = self.ui.folderListWidget.currentRow()
        self.ui.folderListWidget.takeItem(selected_folder_index)

