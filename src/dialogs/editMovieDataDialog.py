# Same as editableListWidget, this is loosely based on the ui file.


from PyQt5 import QtCore, QtGui, QtWidgets
from .widgets.editableListWidget import editableListWidget

DO_NOT_ALLOW_EDITING = ["runtime",
                        "cover_url",
                        "playcount",
                        "lastplay",
                        "imdb_id",
                        "imdb_rating"]

class unacceptableDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(unacceptableDialog, self).__init__(parent)
    # Stops the enter key from triggering the dialog's accept() slot. Kind of annoying.
    def keyPressEvent(self, event):
        if event.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
            event.ignore()
        else:
            super().keyPressEvent(event)

class Ui_editMovieDataDialogBase(object):
    def __init__(self):
        self.movietitle = None
        self.moviedata = None

    def setupData(self, movietitle, moviedata):
        self.movietitle = movietitle
        self.moviedata = moviedata
        self.movieTitleLabel.setText(movietitle)
        # Dont use the movie title, we already have that
        _ = self.moviedata.pop("title")
        # Populate our scroll area with all the data from moviedata
        # If the data type is a list we use editableListWidget and let it figure out which widget to use
        # If the data is a simple string we'll just make a QLineEdit
        for key, value in self.moviedata.items():
            # Need a group widget to contain the widget
            # The annoying thing is, I'd like to use a nice string for the group title but I don't have that.
            # All I have are the data keys, which are descriptive but not nice to look at. Eh, for now I don't care.
            # We could always create a dictionary to map the key names to proper strings.
            groupbox = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
            font = QtGui.QFont()
            font.setPointSize(15)
            groupbox.setFont(font)
            #TODO If you want to use nice key names for the title heres the place to change it
            # Would be easiest to just use a dictionary to map the keys to nice names
            groupbox.setTitle(key)
            groupbox.setAlignment(QtCore.Qt.AlignCenter)
            groupbox.setObjectName(f"groupbox--{key}")
            horizontalLayout = QtWidgets.QHBoxLayout(groupbox)
            if isinstance(value, list):
                datawidget = editableListWidget(key, value, parent=groupbox)
                groupbox.setMinimumSize(320,230)
            elif isinstance(value, (int, str)):
                datawidget = QtWidgets.QLineEdit(parent=groupbox)
                datawidget.setText(str(value))
                groupbox.setMinimumSize(320,100)
                # Some of these fields we don't want to allow editing, so if the key is in our disallow list we set readonly
                if key in DO_NOT_ALLOW_EDITING:
                    datawidget.setReadOnly(True)
                    datawidget.setStyleSheet("QLineEdit:read-only { background-color: lightgrey; }");
            else:
                raise(Exception(f"Got unexpected field type: {type(value)}"))
            datawidget.setObjectName(f"datawidget--{key}")
            horizontalLayout.addWidget(datawidget)
            self.verticalLayout_2.addWidget(groupbox)

    def setupUi(self, editMovieDataDialogBase):
        editMovieDataDialogBase.setObjectName("editMovieDataDialogBase")
        editMovieDataDialogBase.resize(475, 650)
        editMovieDataDialogBase.setMinimumSize(QtCore.QSize(350, 500))
        self.verticalLayout = QtWidgets.QVBoxLayout(editMovieDataDialogBase)
        self.verticalLayout.setObjectName("verticalLayout")
        self.movieTitleHLayout = QtWidgets.QHBoxLayout()
        self.movieTitleHLayout.setObjectName("movieTitleHLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.movieTitleHLayout.addItem(spacerItem)
        self.movieTitleLabel = QtWidgets.QLabel(editMovieDataDialogBase)
        font = QtGui.QFont()
        font.setPointSize(26)
        self.movieTitleLabel.setFont(font)
        self.movieTitleLabel.setObjectName("movieTitleLabel")
        self.movieTitleHLayout.addWidget(self.movieTitleLabel)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.movieTitleHLayout.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.movieTitleHLayout)
        self.scrollArea = QtWidgets.QScrollArea(editMovieDataDialogBase)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 430, 549))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        # TODO PULLED GROUP BOX FROM HERE
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem2)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.buttonAreaHLayout = QtWidgets.QHBoxLayout()
        self.buttonAreaHLayout.setObjectName("buttonAreaHLayout")
        spacerItem3 = QtWidgets.QSpacerItem(60, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.buttonAreaHLayout.addItem(spacerItem3)
        self.saveButton = QtWidgets.QPushButton(editMovieDataDialogBase)
        self.saveButton.setObjectName("saveButton")
        self.buttonAreaHLayout.addWidget(self.saveButton)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.buttonAreaHLayout.addItem(spacerItem4)
        self.cancelButton = QtWidgets.QPushButton(editMovieDataDialogBase)
        self.cancelButton.setObjectName("cancelButton")
        self.buttonAreaHLayout.addWidget(self.cancelButton)
        spacerItem5 = QtWidgets.QSpacerItem(60, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.buttonAreaHLayout.addItem(spacerItem5)
        self.verticalLayout.addLayout(self.buttonAreaHLayout)

        self.retranslateUi(editMovieDataDialogBase)
        self.saveButton.clicked.connect(editMovieDataDialogBase.accept) # type: ignore
        self.cancelButton.clicked.connect(editMovieDataDialogBase.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(editMovieDataDialogBase)

    def retranslateUi(self, editMovieDataDialogBase):
        _translate = QtCore.QCoreApplication.translate
        editMovieDataDialogBase.setWindowTitle(_translate("editMovieDataDialogBase", "Edit Movie Data"))
        self.movieTitleLabel.setText(_translate("editMovieDataDialogBase", "MOVIE_TITLE"))
        self.saveButton.setText(_translate("editMovieDataDialogBase", "Save"))
        self.cancelButton.setText(_translate("editMovieDataDialogBase", "Cancel"))

