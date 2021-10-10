from PyQt5 import QtCore, QtWidgets, QtGui
from .starratingwidget import starRatingWidget

class movieLibraryInfoWidget(QtWidgets.QWidget):
    movieSelectionChanged = QtCore.pyqtSignal(QtCore.QVariant, QtCore.QVariant, QtCore.QVariant)

    def __init__(self, parent=None):
        super(movieLibraryInfoWidget, self).__init__(parent=parent)
        self.setupWidget()

    def setupWidget(self):
        self.setObjectName("movieLibraryInfoWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.movieLibraryList = QtWidgets.QListWidget(self)
        self.movieLibraryList.setObjectName("movieLibraryList")
        self.horizontalLayout.addWidget(self.movieLibraryList)
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
        self.movieInfoDisplay.setObjectName("movieInfoDisplay")
        self.movieInfoDisplay.setOpenExternalLinks(False)
        self.movieInfoDisplay.setOpenLinks(False)
        self.movieLibraryInfoFrameVLayout.addWidget(self.movieInfoDisplay)
        self.libraryStarRatingContainerFrame = QtWidgets.QFrame(self.movieLibraryInfoFrame)
        self.libraryStarRatingContainerFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.libraryStarRatingContainerFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.libraryStarRatingContainerFrame.setObjectName("libraryStarRatingContainerFrame")
        self.libraryStarRatingContainerFrameHLayout = QtWidgets.QHBoxLayout(self.libraryStarRatingContainerFrame)
        self.libraryStarRatingContainerFrameHLayout.setContentsMargins(0, 0, 0, 0)
        self.libraryStarRatingContainerFrameHLayout.setSpacing(0)
        self.libraryStarRatingContainerFrameHLayout.setObjectName("libraryStarRatingContainerFrameHLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.libraryStarRatingContainerFrameHLayout.addItem(spacerItem)
        self.libraryStarRating = starRatingWidget(self.libraryStarRatingContainerFrame)
        self.libraryStarRating.setMinimumSize(QtCore.QSize(140, 28))
        self.libraryStarRating.setMaximumSize(QtCore.QSize(140, 28))
        self.libraryStarRating.setObjectName("libraryStarRating")
        self.libraryStarRatingContainerFrameHLayout.addWidget(self.libraryStarRating)
        spacerItem1 = QtWidgets.QSpacerItem(126, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.libraryStarRatingContainerFrameHLayout.addItem(spacerItem1)
        self.movieLibraryInfoFrameVLayout.addWidget(self.libraryStarRatingContainerFrame)
        self.horizontalLayout.addWidget(self.movieLibraryInfoFrame)
        self.movieLibraryList.currentItemChanged.connect(lambda newitem, olditem: self.movieSelectionChanged.emit(newitem, olditem, self.movieInfoDisplay))
        self.movieInfoDisplay.anchorClicked['QUrl'].connect(self.openfile)

    def openfile(self, url):
        fixedurl = QtCore.QUrl.fromPercentEncoding(bytes(url.toString(), "utf-8"))
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(fixedurl))

