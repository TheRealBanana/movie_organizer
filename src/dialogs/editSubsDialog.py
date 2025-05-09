from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_editsubs_dialog(object):
    def setupUi(self, editsubs_dialog):
        editsubs_dialog.setObjectName("editsubs_dialog")
        editsubs_dialog.resize(601, 700)
        editsubs_dialog.setWindowTitle("Edit Subtitles")
        self.verticalLayout = QtWidgets.QVBoxLayout(editsubs_dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.movie_title_label = QtWidgets.QLabel(editsubs_dialog)
        self.movie_title_label.setText("MOVIE_TITLE")
        font = QtGui.QFont()
        font.setPointSize(22)
        self.movie_title_label.setFont(font)
        self.movie_title_label.setTextFormat(QtCore.Qt.PlainText)
        self.movie_title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.movie_title_label.setObjectName("movie_title_label")
        self.movie_title_label.setToolTip("MOVIE_FILENAME")
        self.verticalLayout.addWidget(self.movie_title_label)
        self.subtitle_text = QtWidgets.QTextEdit(editsubs_dialog)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.subtitle_text.setFont(font)
        self.subtitle_text.setUndoRedoEnabled(True)
        self.subtitle_text.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.subtitle_text.setReadOnly(False)
        self.subtitle_text.setOverwriteMode(False)
        self.subtitle_text.setAcceptRichText(False)
        self.subtitle_text.setObjectName("subtitle_text")
        self.verticalLayout.addWidget(self.subtitle_text)
        self.button_frame = QtWidgets.QFrame(editsubs_dialog)
        self.button_frame.setObjectName("button_frame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.button_frame)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(187, 20, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.save_button = QtWidgets.QPushButton(self.button_frame)
        self.save_button.setObjectName("save_button")
        self.save_button.setText("Save")
        self.horizontalLayout.addWidget(self.save_button)
        spacerItem1 = QtWidgets.QSpacerItem(10, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.cancel_button = QtWidgets.QPushButton(self.button_frame)
        self.cancel_button.setObjectName("cancel_button")
        self.cancel_button.setText("Cancel")
        self.horizontalLayout.addWidget(self.cancel_button)
        spacerItem2 = QtWidgets.QSpacerItem(186, 20, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout.addWidget(self.button_frame)
        # CONNECTIONS HERE
        self.save_button.clicked.connect(editsubs_dialog.accept)
        self.cancel_button.clicked.connect(editsubs_dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(editsubs_dialog)

    def setupData(self, movie_title, subtitles, filename):
        self.movie_title_label.setText(movie_title)
        self.subtitle_text.setPlainText(subtitles)
        self.movie_title_label.setToolTip(filename)
