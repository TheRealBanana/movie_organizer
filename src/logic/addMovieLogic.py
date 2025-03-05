from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QFileDialog, QDialog
from dialogs.addMovieDialog import Ui_addMovieDialog

class AddMovieDialogFunctions(QObject):
    def __init__(self, parent=None):
        super(AddMovieDialogFunctions, self).__init__(parent)
        self.dialog = QDialog(parent)
        self.ui = Ui_addMovieDialog()
        self.idCheckGood = False

    def showAddMovieDialog(self):
        self.setupDialog()
        self.setupConnections()

        returnstatus = bool(self.dialog.exec_())
        print(type((returnstatus)))
        print(returnstatus)
        print("DIALOGSETUP")

    def setupDialog(self):
        self.ui.setupUi(self.dialog)

    def setupConnections(self):
        self.ui.browseButton.clicked.connect(self.showFileBrowseDialog)


    def showFileBrowseDialog(self):
        filedialog = QFileDialog()
        filedialog.setAcceptMode(QFileDialog.AcceptOpen)
        filedialog.setFileMode(QFileDialog.ExistingFile)
        filedialog.setViewMode(QFileDialog.Detail)
        parent = self.dialog
        caption = "Select a media file..."
        selectedfile, _ = filedialog.getOpenFileName(parent, caption)
        self.ui.filePathLineEdit.setText(selectedfile)

        self.checkIfEnableSave()

    #Simple function, check if we should enable the save button. If not disable it.
    def checkIfEnableSave(self):
        if len(self.ui.filePathLineEdit.text()) > 0 and self.idCheckGood is True:
            self.ui.saveButton.setEnabled(True)
        else:
            self.ui.saveButton.setEnabled(False)