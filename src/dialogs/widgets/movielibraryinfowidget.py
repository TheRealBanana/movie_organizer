from PyQt5 import QtCore, QtWidgets, QtGui
from subprocess import Popen, PIPE
from .starratingwidget import starRatingWidget

class movieLibraryInfoWidget(QtWidgets.QWidget):
    updatePlayCount = QtCore.pyqtSignal(str)
    movieSelectionChanged = QtCore.pyqtSignal(QtCore.QVariant, QtCore.QVariant, QtCore.QVariant)

    def __init__(self, parent=None):
        super(movieLibraryInfoWidget, self).__init__(parent=parent)
        self.setupWidget()

    def setupWidget(self):
        self.setObjectName("movieLibraryInfoWidget")
        #self.resize(808, 532)
        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.leftSideContainer = QtWidgets.QWidget(self)
        self.leftSideContainer.setMinimumSize(QtCore.QSize(400, 0))
        self.leftSideContainer.setObjectName("leftSideContainer")
        self.gridLayout = QtWidgets.QGridLayout(self.leftSideContainer)
        self.gridLayout.setContentsMargins(3, 3, 3, 3)
        self.gridLayout.setSpacing(3)
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 3, 1, 1)
        self.sortLabel = QtWidgets.QLabel(self.leftSideContainer)
        self.sortLabel.setObjectName("sortLabel")
        self.gridLayout.addWidget(self.sortLabel, 0, 0, 1, 1)
        self.movieLibraryList = QtWidgets.QListWidget(self.leftSideContainer)
        self.movieLibraryList.setObjectName("movieLibraryList")
        self.gridLayout.addWidget(self.movieLibraryList, 2, 0, 1, 4)
        self.sortModeDropdown = QtWidgets.QComboBox(self.leftSideContainer)
        self.sortModeDropdown.setMinimumSize(QtCore.QSize(120, 0))
        self.sortModeDropdown.setObjectName("sortModeDropdown")
        self.sortLabel.setText("Sort:      ")
        self.sortModeDropdown.addItem("Title")
        self.sortModeDropdown.addItem("Year")
        self.sortModeDropdown.addItem("View Count")
        self.sortModeDropdown.addItem("Last View Date")
        self.gridLayout.addWidget(self.sortModeDropdown, 0, 1, 1, 1)
        self.updownsortCheckbox = QtWidgets.QCheckBox(self.leftSideContainer)
        self.updownsortCheckbox.setText("")
        self.updownsortCheckbox.setToolTip("Ascending or Descending sort")
        self.updownsortCheckbox.setObjectName("updownsortCheckbox")
        self.gridLayout.addWidget(self.updownsortCheckbox, 0, 2, 1, 1)
        self.horizontalLayout.addWidget(self.leftSideContainer)
        self.movieLibraryInfoFrame = QtWidgets.QFrame(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.movieLibraryInfoFrame.sizePolicy().hasHeightForWidth())
        self.movieLibraryInfoFrame.setSizePolicy(sizePolicy)
        self.movieLibraryInfoFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.movieLibraryInfoFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.movieLibraryInfoFrame.setObjectName("movieLibraryInfoFrame")
        self.movieLibraryInfoFrameVLayout = QtWidgets.QVBoxLayout(self.movieLibraryInfoFrame)
        self.movieLibraryInfoFrameVLayout.setObjectName("movieLibraryInfoFrameVLayout")
        self.movieInfoDisplay = QtWidgets.QTextBrowser(self.movieLibraryInfoFrame)
        self.movieInfoDisplay.setOpenExternalLinks(False)
        self.movieInfoDisplay.setOpenLinks(False)
        self.movieInfoDisplay.setObjectName("movieInfoDisplay")
        self.movieLibraryInfoFrameVLayout.addWidget(self.movieInfoDisplay)
        self.libraryStarRatingContainerFrame = QtWidgets.QFrame(self.movieLibraryInfoFrame)
        self.libraryStarRatingContainerFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.libraryStarRatingContainerFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.libraryStarRatingContainerFrame.setObjectName("libraryStarRatingContainerFrame")
        self.libraryStarRatingContainerFrameHLayout = QtWidgets.QHBoxLayout(self.libraryStarRatingContainerFrame)
        self.libraryStarRatingContainerFrameHLayout.setContentsMargins(0, 0, 0, 0)
        self.libraryStarRatingContainerFrameHLayout.setSpacing(0)
        self.libraryStarRatingContainerFrameHLayout.setObjectName("libraryStarRatingContainerFrameHLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.libraryStarRatingContainerFrameHLayout.addItem(spacerItem1)
        self.libraryStarRating = starRatingWidget(self.libraryStarRatingContainerFrame)
        self.libraryStarRating.setMinimumSize(QtCore.QSize(140, 28))
        self.libraryStarRating.setMaximumSize(QtCore.QSize(140, 28))
        self.libraryStarRating.setObjectName("libraryStarRating")
        self.libraryStarRatingContainerFrameHLayout.addWidget(self.libraryStarRating)
        spacerItem2 = QtWidgets.QSpacerItem(126, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.libraryStarRatingContainerFrameHLayout.addItem(spacerItem2)
        self.movieLibraryInfoFrameVLayout.addWidget(self.libraryStarRatingContainerFrame)
        self.horizontalLayout.addWidget(self.movieLibraryInfoFrame)

        self.movieLibraryList.currentItemChanged.connect(lambda newitem, olditem: self.movieSelectionChanged.emit(newitem, olditem, self.movieInfoDisplay))
        self.movieInfoDisplay.anchorClicked['QUrl'].connect(self.openfile)
        self.sortModeDropdown.currentTextChanged["QString"].connect(self.sortOptionsUpdate)
        self.updownsortCheckbox.stateChanged['int'].connect(self.sortOptionsUpdate)

    def sortOptionsUpdate(self, _):
        mode = self.sortModeDropdown.currentText().lower()
        order = self.updownsortCheckbox.isChecked()
        oldlist = []
        while self.movieLibraryList.count() > 0:
            olditem = self.movieLibraryList.takeItem(0)
            olddata = olditem.data(QtCore.Qt.UserRole)
            oldlist.append(olddata)
        #Sort list by new sort options
        if mode == "view count": sortkey = "playcount"
        elif mode == "last view date":
            #TODO MAKE LASTPLAY INTO UNIX SECONDS FOR PROPER SORTING
            sortkey = "lastplay"
        elif mode == "personal rating": sortkey = "rating"
        elif mode == "imdb rating": sortkey = "imdb_rating"
        else:
            sortkey = mode

        oldlist.sort(key=lambda r: r[sortkey], reverse=order)
        #if order: oldlist.reverse()

        #Repopulate list
        for item in oldlist:
            #At a certain point the app gets too big, and then you get to some point where you think "I shouldnt do it that way"
            #but by now its far too late to change the way it works and you are stuck with it. Damn.
            if "cleanyear" not in item: item["cleanyear"] = item["year"]
            if "cleantitle" not in item: item["cleantitle"] = item["title"]
            newitem = QtWidgets.QListWidgetItem("(%s)        %s" % (item["cleanyear"], item["cleantitle"]))
            newitem.setData(QtCore.Qt.UserRole, item)
            newitem.setToolTip(str(item["filename"]))
            self.movieLibraryList.addItem(newitem)


    def openfile(self, url):
        #Only update play count when we click the "PLAY FILE LOCALLY" link
        #The other possible link will have the vlc exe in it
        fixedurl = QtCore.QUrl.fromPercentEncoding(bytes(url.toString(), "utf-8"))
        if "network-caching" in fixedurl:
            _ = Popen(fixedurl, stdout=PIPE)
        else:
            fixedurl = QtCore.QUrl.fromPercentEncoding(bytes(url.toString(), "utf-8"))
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(fixedurl))
            currentmovietitle = self.movieLibraryList.currentItem().text()
            self.updatePlayCount.emit(currentmovietitle)

