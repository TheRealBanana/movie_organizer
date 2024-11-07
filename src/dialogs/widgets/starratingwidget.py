from PyQt5 import QtCore, QtGui, QtWidgets

class StarButton(QtWidgets.QPushButton):
    starClicked = QtCore.pyqtSignal(int)
    def __init__(self, parent=None, starnum=None):
        super(StarButton, self).__init__(parent)
        self.starnum = starnum
        self.clicked.connect(self.starclick)
    def starclick(self):
        self.starClicked.emit(self.starnum)

class starRatingWidget(QtWidgets.QWidget):
    starRatingChanged = QtCore.pyqtSignal(int)
    def __init__(self, parent=None):
        super(starRatingWidget, self).__init__(parent)
        self.currentRating = 0
        self.yellowStar = QtGui.QIcon()
        self.yellowStar.addPixmap(QtGui.QPixmap("../icons/yellow_star.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.greyStar = QtGui.QIcon()
        self.greyStar.addPixmap(QtGui.QPixmap("../icons/grey_star.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setObjectName("starRatingWidget")
        self.resize(140, 28)
        self.setMinimumSize(QtCore.QSize(140, 28))
        self.setMaximumSize(QtCore.QSize(140, 28))
        self.setWindowTitle("")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.ratingStar_1 = StarButton(self, 1)
        self.ratingStar_1.setMinimumSize(QtCore.QSize(24, 24))
        self.ratingStar_1.setMaximumSize(QtCore.QSize(24, 24))
        self.ratingStar_1.setStyleSheet("border: none;")
        self.ratingStar_1.setText("")
        self.ratingStar_1.setIcon(self.greyStar)
        self.ratingStar_1.setIconSize(QtCore.QSize(24, 24))
        self.ratingStar_1.setCheckable(False)
        self.ratingStar_1.setChecked(False)
        self.ratingStar_1.setAutoDefault(False)
        self.ratingStar_1.setDefault(False)
        self.ratingStar_1.setFlat(True)
        self.ratingStar_1.setObjectName("ratingStar_1")
        self.horizontalLayout.addWidget(self.ratingStar_1)
        self.ratingStar_2 = StarButton(self, 2)
        self.ratingStar_2.setMinimumSize(QtCore.QSize(24, 24))
        self.ratingStar_2.setMaximumSize(QtCore.QSize(24, 24))
        self.ratingStar_2.setStyleSheet("border: none;")
        self.ratingStar_2.setText("")
        self.ratingStar_2.setIcon(self.greyStar)
        self.ratingStar_2.setIconSize(QtCore.QSize(24, 24))
        self.ratingStar_2.setCheckable(False)
        self.ratingStar_2.setChecked(False)
        self.ratingStar_2.setAutoDefault(False)
        self.ratingStar_2.setDefault(False)
        self.ratingStar_2.setFlat(True)
        self.ratingStar_2.setObjectName("ratingStar_2")
        self.horizontalLayout.addWidget(self.ratingStar_2)
        self.ratingStar_3 = StarButton(self, 3)
        self.ratingStar_3.setMinimumSize(QtCore.QSize(24, 24))
        self.ratingStar_3.setMaximumSize(QtCore.QSize(24, 24))
        self.ratingStar_3.setStyleSheet("border: none;")
        self.ratingStar_3.setText("")
        self.ratingStar_3.setIcon(self.greyStar)
        self.ratingStar_3.setIconSize(QtCore.QSize(24, 24))
        self.ratingStar_3.setCheckable(False)
        self.ratingStar_3.setChecked(False)
        self.ratingStar_3.setAutoDefault(False)
        self.ratingStar_3.setDefault(False)
        self.ratingStar_3.setFlat(True)
        self.ratingStar_3.setObjectName("ratingStar_3")
        self.horizontalLayout.addWidget(self.ratingStar_3)
        self.ratingStar_4 = StarButton(self, 4)
        self.ratingStar_4.setMinimumSize(QtCore.QSize(24, 24))
        self.ratingStar_4.setMaximumSize(QtCore.QSize(24, 24))
        self.ratingStar_4.setStyleSheet("border: none;")
        self.ratingStar_4.setText("")
        self.ratingStar_4.setIcon(self.greyStar)
        self.ratingStar_4.setIconSize(QtCore.QSize(24, 24))
        self.ratingStar_4.setCheckable(False)
        self.ratingStar_4.setChecked(False)
        self.ratingStar_4.setAutoDefault(False)
        self.ratingStar_4.setDefault(False)
        self.ratingStar_4.setFlat(True)
        self.ratingStar_4.setObjectName("ratingStar_4")
        self.horizontalLayout.addWidget(self.ratingStar_4)
        self.ratingStar_5 = StarButton(self, 5)
        self.ratingStar_5.setMinimumSize(QtCore.QSize(24, 24))
        self.ratingStar_5.setMaximumSize(QtCore.QSize(24, 24))
        self.ratingStar_5.setStyleSheet("border: none;")
        self.ratingStar_5.setText("")
        self.ratingStar_5.setIcon(self.greyStar)
        self.ratingStar_5.setIconSize(QtCore.QSize(24, 24))
        self.ratingStar_5.setCheckable(False)
        self.ratingStar_5.setChecked(False)
        self.ratingStar_5.setAutoDefault(False)
        self.ratingStar_5.setDefault(False)
        self.ratingStar_5.setFlat(True)
        self.ratingStar_5.setObjectName("ratingStar_5")
        self.horizontalLayout.addWidget(self.ratingStar_5)
        self.starlist = [self.ratingStar_1, self.ratingStar_2, self.ratingStar_3, self.ratingStar_4, self.ratingStar_5]
        #Connect slots
        self.ratingStar_1.starClicked.connect(self.starClickedUpdate)
        self.ratingStar_2.starClicked.connect(self.starClickedUpdate)
        self.ratingStar_3.starClicked.connect(self.starClickedUpdate)
        self.ratingStar_4.starClicked.connect(self.starClickedUpdate)
        self.ratingStar_5.starClicked.connect(self.starClickedUpdate)

    def starClickedUpdate(self, staridx, emit=True):
        try:
            staridx = int(staridx)
        except:
            raise(Exception(f"Got a weird result for staridx: {type(staridx)}"))
        #Clicking the current star rating allows you to unrate a movie
        if self.currentRating == staridx and emit:
            staridx = 0
        #Turn all stars before this to yellow
        for s in self.starlist[:staridx]:
            s.setIcon(self.yellowStar)
        #and all stars after to grey
        for s in self.starlist[staridx:]:
            s.setIcon(self.greyStar)
        self.currentRating = staridx
        #emit a signal for this change so the database can be updated
        if emit: self.starRatingChanged.emit(staridx)
