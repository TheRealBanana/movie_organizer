# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MainWindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(891, 551)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidgetGridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.centralwidgetGridLayout.setObjectName("centralwidgetGridLayout")
        self.mainTabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.mainTabWidget.setObjectName("mainTabWidget")
        self.movieLibraryTab = QtWidgets.QWidget()
        self.movieLibraryTab.setObjectName("movieLibraryTab")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.movieLibraryTab)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.movieLibraryInfoWidget = movieLibraryInfoWidget(self.movieLibraryTab)
        self.movieLibraryInfoWidget.setObjectName("movieLibraryInfoWidget")
        self.horizontalLayout.addWidget(self.movieLibraryInfoWidget)
        self.mainTabWidget.addTab(self.movieLibraryTab, "")
        self.mainSearchTab = QtWidgets.QWidget()
        self.mainSearchTab.setObjectName("mainSearchTab")
        self.mainSearchTabGridLayout = QtWidgets.QGridLayout(self.mainSearchTab)
        self.mainSearchTabGridLayout.setObjectName("mainSearchTabGridLayout")
        self.searchTabWidget = QtWidgets.QTabWidget(self.mainSearchTab)
        self.searchTabWidget.setTabsClosable(True)
        self.searchTabWidget.setObjectName("searchTabWidget")
        self.searchParametersTab = QtWidgets.QWidget()
        self.searchParametersTab.setObjectName("searchParametersTab")
        self.searchParametersTabVLayout = QtWidgets.QVBoxLayout(self.searchParametersTab)
        self.searchParametersTabVLayout.setObjectName("searchParametersTabVLayout")
        self.parametersFrame = QtWidgets.QScrollArea(self.searchParametersTab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.parametersFrame.sizePolicy().hasHeightForWidth())
        self.parametersFrame.setSizePolicy(sizePolicy)
        self.parametersFrame.setFrameShape(QtWidgets.QFrame.Box)
        self.parametersFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.parametersFrame.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.parametersFrame.setWidgetResizable(True)
        self.parametersFrame.setObjectName("parametersFrame")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 821, 43))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollAreaWidgetContents.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents.setSizePolicy(sizePolicy)
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.parametersFrameVLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.parametersFrameVLayout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.parametersFrameVLayout.setSpacing(0)
        self.parametersFrameVLayout.setObjectName("parametersFrameVLayout")
        self.newSearchParameterContainerHLayout = QtWidgets.QHBoxLayout()
        self.newSearchParameterContainerHLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.newSearchParameterContainerHLayout.setSpacing(0)
        self.newSearchParameterContainerHLayout.setObjectName("newSearchParameterContainerHLayout")
        spacerItem = QtWidgets.QSpacerItem(37, 17, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.newSearchParameterContainerHLayout.addItem(spacerItem)
        self.newSearchParameterButton = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.newSearchParameterButton.setObjectName("newSearchParameterButton")
        self.newSearchParameterContainerHLayout.addWidget(self.newSearchParameterButton)
        spacerItem1 = QtWidgets.QSpacerItem(37, 17, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.newSearchParameterContainerHLayout.addItem(spacerItem1)
        self.parametersFrameVLayout.addLayout(self.newSearchParameterContainerHLayout)
        self.parametersFrame.setWidget(self.scrollAreaWidgetContents)
        self.searchParametersTabVLayout.addWidget(self.parametersFrame)
        self.searchButtonContainerHLayout = QtWidgets.QHBoxLayout()
        self.searchButtonContainerHLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.searchButtonContainerHLayout.setObjectName("searchButtonContainerHLayout")
        spacerItem2 = QtWidgets.QSpacerItem(351, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.searchButtonContainerHLayout.addItem(spacerItem2)
        self.searchButton = QtWidgets.QPushButton(self.searchParametersTab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.searchButton.sizePolicy().hasHeightForWidth())
        self.searchButton.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.searchButton.setFont(font)
        self.searchButton.setObjectName("searchButton")
        self.searchButtonContainerHLayout.addWidget(self.searchButton)
        spacerItem3 = QtWidgets.QSpacerItem(351, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.searchButtonContainerHLayout.addItem(spacerItem3)
        self.searchParametersTabVLayout.addLayout(self.searchButtonContainerHLayout)
        self.searchTabWidget.addTab(self.searchParametersTab, "")
        self.mainSearchTabGridLayout.addWidget(self.searchTabWidget, 0, 0, 1, 1)
        self.mainTabWidget.addTab(self.mainSearchTab, "")
        self.centralwidgetGridLayout.addWidget(self.mainTabWidget, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 891, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuOptions = QtWidgets.QMenu(self.menubar)
        self.menuOptions.setObjectName("menuOptions")
        MainWindow.setMenuBar(self.menubar)
        self.actionSettings = QtWidgets.QAction(MainWindow)
        self.actionSettings.setObjectName("actionSettings")
        self.actionScan_Media_Collection = QtWidgets.QAction(MainWindow)
        self.actionScan_Media_Collection.setObjectName("actionScan_Media_Collection")
        self.menuFile.addAction(self.actionScan_Media_Collection)
        self.menuOptions.addAction(self.actionSettings)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuOptions.menuAction())

        self.retranslateUi(MainWindow)
        self.mainTabWidget.setCurrentIndex(0)
        self.searchTabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.movieLibraryTab), _translate("MainWindow", "Movie Library"))
        self.newSearchParameterButton.setText(_translate("MainWindow", "      New Search Parameter      "))
        self.searchButton.setText(_translate("MainWindow", "     Search     "))
        self.searchTabWidget.setTabText(self.searchTabWidget.indexOf(self.searchParametersTab), _translate("MainWindow", "Search Options"))
        self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.mainSearchTab), _translate("MainWindow", "Search"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuOptions.setTitle(_translate("MainWindow", "Settings"))
        self.actionSettings.setText(_translate("MainWindow", "Preferences..."))
        self.actionScan_Media_Collection.setText(_translate("MainWindow", "Scan Media Collection"))
from .widgets.movielibraryinfowidget import movieLibraryInfoWidget
