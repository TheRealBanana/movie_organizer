from PyQt5 import QtCore, QtWidgets


#Too many lines of detail in the progressbar will crash the app. You have been warned.
MAX_SCROLL_LINES = 100000

class genericProgressDialog(QtWidgets.QDialog):
    closableDialogClosing = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(genericProgressDialog, self).__init__(parent)
        self.setObjectName("genericProgressDialog")
        self.resize(500, 123)
        self.setModal(True)
        self.setWindowTitle("Discovering files...")
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(298, 123))
        self.setMaximumSize(QtCore.QSize(16777215, 123))
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.setTextVisible(False)
        self.progressBar.setFormat("%p%")
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout.addWidget(self.progressBar)
        self.progressLabel = QtWidgets.QLabel(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.progressLabel.sizePolicy().hasHeightForWidth())
        self.progressLabel.setSizePolicy(sizePolicy)
        self.progressLabel.setMinimumSize(QtCore.QSize(280, 0))
        self.progressLabel.setMaximumSize(QtCore.QSize(1500, 16777215))
        self.progressLabel.setTextFormat(QtCore.Qt.PlainText)
        self.progressLabel.setObjectName("progressLabel")
        self.verticalLayout.addWidget(self.progressLabel)
        self.centeredCancelButton = QtWidgets.QFrame(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centeredCancelButton.sizePolicy().hasHeightForWidth())
        self.centeredCancelButton.setSizePolicy(sizePolicy)
        self.centeredCancelButton.setMinimumSize(QtCore.QSize(205, 40))
        self.centeredCancelButton.setMaximumSize(QtCore.QSize(16777215, 40))
        self.centeredCancelButton.setObjectName("centeredCancelButton")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centeredCancelButton)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(50, 20, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.cancelButton = QtWidgets.QPushButton(self.centeredCancelButton)
        self.cancelButton.setMinimumSize(QtCore.QSize(75, 22))
        self.cancelButton.setMaximumSize(QtCore.QSize(75, 22))
        self.cancelButton.setObjectName("cancelButton")
        self.cancelButton.clicked.connect(lambda: self.closableDialogClosing.emit())
        self.horizontalLayout.addWidget(self.cancelButton)
        spacerItem1 = QtWidgets.QSpacerItem(50, 20, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout.addWidget(self.centeredCancelButton)
        self.cancelButton.setText("Cancel")
        QtCore.QMetaObject.connectSlotsByName(self)
        #For details pullout. Won't add to layout until details button is pressed.
        self.detailsButton = QtWidgets.QPushButton(self.centeredCancelButton)
        self.detailsButton.setText("Details >>")
        self.detailsButton.setObjectName(u"detailsButton")
        self.horizontalLayout.addWidget(self.detailsButton)
        self.detailsButton.pressed.connect(self.detailsButtonPressed)
        #self.detailsTextOutput = None
        self.detailsTextOutput = QtWidgets.QTextBrowser(self)
        self.detailsTextOutput.setObjectName(u"detailsTextOutput")
        self.detailsTextOutput.document().setMaximumBlockCount(MAX_SCROLL_LINES)
        self.detailsTextOutput.hide()
        self.verticalLayout.addWidget(self.detailsTextOutput)
        self.showingDetails = False

    def updateDetailsText(self, text):
        #Preserve current scrollbar/cursor state
        vscrollbar = self.detailsTextOutput.verticalScrollBar()
        vscrollmax = vscrollbar.maximum()
        vscrollval = vscrollbar.value()
        cursor = self.detailsTextOutput.textCursor()
        cursorstart = cursor.selectionStart()
        cursorend = cursor.selectionEnd()

        #Insert new text
        cursor.movePosition(cursor.End)
        cursor.insertText(text + "\n")

        #Restore any selected text
        if cursorstart != cursorend:
            cursor.setPosition(cursorstart, cursor.MoveAnchor)
            cursor.setPosition(cursorend, cursor.KeepAnchor)
            self.detailsTextOutput.setTextCursor(cursor)

        #If we were within 5 lines from the bottom, keep scrolling
        if vscrollmax - vscrollval < 5:
            newvscrollmax = self.detailsTextOutput.verticalScrollBar().maximum()
            self.detailsTextOutput.verticalScrollBar().setSliderPosition(newvscrollmax)
        elif vscrollval != 0:
            vscrollbar.setSliderPosition(vscrollval)

        #Just constantly keep scrolling to the bottom
        #print("VMAX: %s" % self.detailsTextOutput.document().blockCount())
        #self.detailsTextOutput.verticalScrollBar().setSliderPosition(self.detailsTextOutput.verticalScrollBar().maximum())
        QtWidgets.QApplication.processEvents()


    def detailsButtonPressed(self):
        #print("DETAILSBUTTON")
        if self.showingDetails is False:
            self.detailsTextOutput.show()
            #Resize our progressbar dialog to accommodate the details output widget
            self.setMaximumSize(QtCore.QSize(16777215, 325))
            self.resize(self.width(), 325)
            #Modify the details button to change things back
            self.detailsButton.setText("Details <<")
            self.showingDetails = True
            QtWidgets.QApplication.processEvents()
        else:
            #Hide the details.
            self.detailsTextOutput.hide()
            self.setMaximumSize(QtCore.QSize(16777215, 123))
            self.resize(self.width(), 123)
            #Reset the button
            self.detailsButton.setText("Details >>")
            self.showingDetails = False
            QtWidgets.QApplication.processEvents()

    def setFinished(self, finalmessage=""):
        self.updateDetailsText(finalmessage)
        self.progressBar.setValue(100)
        self.cancelButton.setText("Close")

    def closeEvent(self, QCloseEvent):
        #print("CLOSEEVENT")
        self.closableDialogClosing.emit()
        QCloseEvent.accept()
