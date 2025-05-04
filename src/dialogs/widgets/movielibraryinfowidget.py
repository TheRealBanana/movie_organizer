from PyQt5 import QtCore, QtWidgets, QtGui
from subprocess import Popen, PIPE
from .starratingwidget import starRatingWidget
from time import mktime, strptime

# So its slightly easier to change the color of the highlight for titles in the library with subtitle data saved
#GOODSUBS_LISTITEM_BG_COLOR = (150, 255, 140) # More vibrant green
GOODSUBS_LISTITEM_BG_COLOR = (190, 255, 190) # Faint green
NOSUBS_LISTITEM_BG_COLOR = (255, 190, 190) # Faint red

class movieLibraryInfoWidget(QtWidgets.QWidget):
    updatePlayCount = QtCore.pyqtSignal(str)
    movieSelectionChanged = QtCore.pyqtSignal(QtCore.QVariant, QtCore.QVariant, QtCore.QVariant)

    def __init__(self, parent=None):
        super(movieLibraryInfoWidget, self).__init__(parent=parent)
        self.setupWidget()
        self.sublibref = None

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
        self.movieLibraryList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.gridLayout.addWidget(self.movieLibraryList, 2, 0, 1, 4)
        self.sortModeDropdown = QtWidgets.QComboBox(self.leftSideContainer)
        self.sortModeDropdown.setMinimumSize(QtCore.QSize(120, 0))
        self.sortModeDropdown.setObjectName("sortModeDropdown")
        self.sortLabel.setText("Sort:      ")
        self.sortModeDropdown.addItem("Title")
        self.sortModeDropdown.addItem("Year")
        self.sortModeDropdown.addItem("Runtime")
        self.sortModeDropdown.addItem("View Count")
        self.sortModeDropdown.addItem("Last View Date")
        self.sortModeDropdown.addItem("IMDB Rating")
        self.sortModeDropdown.addItem("Personal Rating")
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

    def setSubRef(self, subref):
        self.sublibref = subref

    #TODO This turned out to be not a good idea. On older PCs this takes for ever to sort, like 300-400ms each time.
    # I think the correct solution here is to annotate that data in the movie database. Just use the extra field or something.
    # And we'll just have it be True or False and we can check that parameter.
    # Or we can do this check once when the library view is initially populated, but the search window wont be fixed.
    # Best to update the database with this new info, change the way subtitles are extracted and saved to add this
    # true flag to the database when it successfully adds the subtitles.
    def sortOptionsUpdate(self, _):
        #Clear any selection and temporarily disable the currentItemChanged signal
        #These two are slowing things down when rebuilding the list
        self.movieLibraryList.clearSelection()
        self.movieLibraryList.currentItemChanged.disconnect()
        mode = self.sortModeDropdown.currentText().lower()
        order = self.updownsortCheckbox.isChecked()
        oldlist = []
        while self.movieLibraryList.count() > 0:
            olditem = self.movieLibraryList.takeItem(0)
            olddata = olditem.data(QtCore.Qt.UserRole)
            oldlist.append(olddata)
        #Sort list by new sort options
        if mode == "view count": sortkey = "playcount"
        elif mode == "last view date": sortkey = "lastplay"
        elif mode == "personal rating": sortkey = "rating"
        elif mode == "imdb rating": sortkey = "imdb_rating"
        else: sortkey = mode

        #Reverse sorting order for some fields
        if mode in "last view date view count imdb rating personal rating runtime":
            order = order ^ True

        if sortkey == "lastplay":
            #Need a diff sorting funct
            def sortfunc(s):
                if len(s["lastplay"]) == 0:
                    #Different return value so that when we sort, the movies without a last view date
                    #dont get in the way of the sorting. We always want those results at the bottom.
                    if order:
                        return 0
                    else:
                        return 9999999999
                return mktime(strptime(s["lastplay"], '%d/%b/%Y-%I:%M:%S %p'))
        elif sortkey == "runtime":
            sortfunc = lambda r: int(r[sortkey])
        elif sortkey == "year":
            sortfunc = lambda r: str(r["cleanyear" if "cleanyear" in r else "year"])
        else:
            sortfunc = lambda r: str(r[sortkey]).lower()

        oldlist.sort(key=sortfunc, reverse=order)
        #If we are sorting by something other than the title, put that info after the title.
        if mode != "title":
            extratag = sortkey
        else:
            extratag = None

        #Repopulate list
        for item in oldlist:
            #At a certain point the app gets too big, and then you get to some point where you think "I shouldnt do it that way"
            #but by now its far too late to change the way it works and you are stuck with it. Damn.
            if "cleanyear" not in item: item["cleanyear"] = item["year"]
            if "cleantitle" not in item: item["cleantitle"] = item["title"]
            listitemtitle = "(%s)        %s" % (item["cleanyear"], item["cleantitle"])
            if extratag is not None:
                if extratag == "runtime":
                    hours = item["runtime"]//60
                    minutes = item["runtime"]%60
                    listitemtitle += " [%sh %sm]" % (hours, minutes)
                elif extratag == "year":
                    listitemtitle += " [%s]" % item["cleanyear"]
                else: listitemtitle += " [%s]" % item[extratag]

            newitem = QtWidgets.QListWidgetItem(listitemtitle)
            newitem.setData(QtCore.Qt.UserRole, item)
            newitem.setToolTip(str(item["filename"]))
            #Check if we have subtitles for this title, if so add an indicator like changing the background
            if not self.sublibref.checkForSubs(item["cleantitle"]):
                bgcolor = QtGui.QColor(*NOSUBS_LISTITEM_BG_COLOR)
                newitem.setBackground(QtGui.QBrush(bgcolor))
            self.movieLibraryList.addItem(newitem)

        #Redo old connection
        self.movieLibraryList.currentItemChanged.connect(lambda newitem, olditem: self.movieSelectionChanged.emit(newitem, olditem, self.movieInfoDisplay))

    def openfile(self, url):
        #Only update play count when we click the "PLAY FILE LOCALLY" link
        #The other possible link will have the vlc exe in it
        fixedurl = QtCore.QUrl.fromPercentEncoding(bytes(url.toString(), "utf-8"))
        if "network-caching" in fixedurl:
            _ = Popen(fixedurl, stdout=PIPE)
        else:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(fixedurl))
            moviedata = self.movieLibraryList.currentItem().data(QtCore.Qt.UserRole)
            currentmovietitle = moviedata["title"]
            self.updatePlayCount.emit(currentmovietitle)

