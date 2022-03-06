import re
from os import sep as ossep
from datetime import datetime
from PyQt5 import QtWidgets, QtCore
from collections import OrderedDict
from .movie_library import MovieLibrary
from .library_scanner import LibraryScanner
from .subtitles import SubtitleDownloader, SubtitleLibrary
from .search import SearchManager
from .options_dialog_functions import OptionsDialogFunctions
from dialogs.options_dialog import Ui_OptionsDialog
from dialogs.widgets.searchParameterWidget import SearchParameterWidget
from dialogs.widgets.movielibraryinfowidget import movieLibraryInfoWidget

def qstringFixer(value):
    if isinstance(value, QtCore.QString):
        value = str(value)
        if value == "true": value = True
        elif value == "false": value = False
    return value
def qtypeFixer(value):
    if type(value) == QtCore.QMetaType.QString:
        value = qstringFixer(value.toPyObject())
    elif type(value) == QtCore.QMetaType.QStringList:
        value = str(value.toPyObject().join(";")).split(";")
        #So a QVariantMap is basically a mangled dict, with all sorts of lame Qt types
    elif type(value) == QtCore.QMetaType.QVariantMap:
        fixeddict = {}
        value = value.toPyObject()
        for key, val in value.items():
            #fix sub-dicts
            if isinstance(val, dict):
                subdict = {}
                for key2, val2 in val.items():
                    subdict[str(key2)] = qtypeFixer(val2)
                val = subdict
            fixeddict[str(key)] = val
        value = fixeddict
    return value



class UIFunctions:
    def __init__(self, uiref, MainWindow):
        self.uiref = uiref
        self.MainWindow = MainWindow
        self.movieLibrary = MovieLibrary()
        self.subtitleLibrary = SubtitleLibrary()
        self.searchManager = SearchManager(self.movieLibrary, self.subtitleLibrary, self.uiref.searchTabWidget)
        #initialize our application
        self.setupConnections()
        self.settings = self.loadSettings()
        #self.fieldlist = OrderedDict.fromkeys(self.movieLibrary.getFieldList(), True)
        self.fieldlist = None
        self.loadLibraryIntoGui()
        self.guimods()

    def setupConnections(self):
        self.uiref.actionScan_Media_Collection.triggered.connect(self.startLibraryScan)
        self.uiref.actionUpdate_Subtitle_Cache.triggered.connect(self.updateSubtitleCache)
        self.uiref.actionSettings.triggered.connect(self.openOptionsDialog)
        self.uiref.movieLibraryInfoWidget.movieSelectionChanged.connect(self.updateLibraryDisplay)
        self.uiref.movieLibraryInfoWidget.updatePlayCount["QString"].connect(self.updatePlayCount)
        self.uiref.movieLibraryInfoWidget.libraryStarRating.starRatingChanged['int'].connect(self.starRatingChanged)
        self.uiref.newSearchParameterButton.clicked.connect(self.newSearchParameterButtonPressed)
        self.uiref.searchButton.clicked.connect(self.searchButtonPressed)
        self.uiref.searchTabWidget.tabCloseRequested['int'].connect(self.closeSearchTabPressed)

    #A place for any dynamic modifications of the GUI.
    def guimods(self):
        #Remove close button from main search tab
        self.uiref.searchTabWidget.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).resize(0,0)

    def updatePlayCount(self, movietitle):
        #Update the database and then update the display search results and main library view
        curdate = datetime.now().strftime('%d/%b/%Y-%I:%M:%S %p')
        count = self.movieLibrary.updatePlayCount(movietitle, curdate)
        self.updateCurrentLibraryItemData("playcount", count)
        self.updateCurrentLibraryItemData("lastplay", curdate)

    def starRatingChanged(self, rating):
        self.updateCurrentLibraryItemData("rating", rating)
        movietitle = self.getCurrentListItem().text()
        self.movieLibrary.updateMovieStarRating(movietitle, rating)

    def getCurrentListItem(self):
        if self.uiref.mainTabWidget.currentIndex() == 1: #Came from search tab
            return self.uiref.searchTabWidget.currentWidget().movieLibraryList.currentItem()
            searchresultdata = searchresultitem.data(QtCore.Qt.UserRole)
        else: #Not from a search tab
            return self.uiref.movieLibraryInfoWidget.movieLibraryList.currentItem()

    def updateCurrentLibraryItemData(self, field, newdata):
        #If we came from a search tab we need to handle updating the main library view differently
        if self.uiref.mainTabWidget.currentIndex() == 1: #Came from search tab
            searchresultitem = self.uiref.searchTabWidget.currentWidget().movieLibraryList.currentItem()
            searchresultdata = searchresultitem.data(QtCore.Qt.UserRole)
            searchresultdata[field] = newdata
            searchresultitem.setData(QtCore.Qt.UserRole, searchresultdata)
            # Alt way to get item from main library view
            libitem = self.uiref.movieLibraryInfoWidget.movieLibraryList.findItems(searchresultdata["cleantitle"], QtCore.Qt.MatchExactly)[0]
        else: #Not from a search tab
            libitem = self.uiref.movieLibraryInfoWidget.movieLibraryList.currentItem()
        #Update main library view
        libdata = libitem.data(QtCore.Qt.UserRole)
        libdata[field] = newdata
        libitem.setData(QtCore.Qt.UserRole, libdata)

    def closeSearchTabPressed(self, idx):
        self.uiref.searchTabWidget.removeTab(idx)

    def searchButtonPressed(self):
        #Get our search parameters
        querydata = {}
        andorstate = {}
        dlgsearch = None # Pull out dialog search queries since they cant be handled by the movie library

        #Collect the search parameters and pass them to the search manager
        for w in self.uiref.scrollAreaWidgetContents.findChildren(SearchParameterWidget):
            fielddata = w.returnData()
            aostate = w.andorState()
            if len(fielddata) == 0:
                continue
            if w.currentfield == "dialog":
                dlgsearch = str(fielddata).strip()
            else:
                querydata[w.currentfield] = str(fielddata).strip()
            andorstate[w.currentfield] = aostate

        #Build up a string with our search parameters to set as a tooltip for this search tab
        tooltipstr = "Search query parameters:\n"
        for fname, fdata in querydata.items():
            tooltipstr += "\n%s%s: %s\n" % (fname, "" if andorstate[fname] == "OR" else " (AND)", fdata)
        if dlgsearch is not None:
            tooltipstr += "\nDialog: %s\n" % dlgsearch

        movieinfowidget = movieLibraryInfoWidget(self.uiref.searchTabWidget)
        movieinfowidget.movieSelectionChanged.connect(self.updateLibraryDisplay)
        movieinfowidget.libraryStarRating.starRatingChanged['int'].connect(self.starRatingChanged)
        movieinfowidget.updatePlayCount["QString"].connect(self.updatePlayCount)
        #Create search results tab
        self.uiref.searchTabWidget.addTab(movieinfowidget, "SEARCH RESULTS (0)")
        tabindex = self.uiref.searchTabWidget.indexOf(movieinfowidget)
        self.uiref.searchTabWidget.setTabToolTip(tabindex, tooltipstr)
        self.uiref.searchTabWidget.setCurrentWidget(movieinfowidget)
        #Create search job
        querydata["andorstate"] = andorstate
        querydata["dlgsearch"] = dlgsearch
        self.searchManager.newSearchJob(querydata, movieinfowidget)




    def newSearchParameterButtonPressed(self):
        #Dont do anything if we dont have any fields left
        if not any(self.fieldlist.values()):
            return
        #Create a new search parameter widget and connect it to our parametersFrame
        newentrywidget = SearchParameterWidget(parent=self.uiref.parametersFrame)
        newentrywidget.searchTemplateEntry.returnPressed.connect(self.searchButtonPressed)
        newentrywidget.removeSelfRequest.connect(self.deleteSearchParameterWidget)
        newentrywidget.searchParamFieldUpdate.connect(self.updateSearchParameterFieldList)
        newentrywidget.updateFieldList(self.fieldlist.copy())
        self.uiref.parametersFrameVLayout.insertWidget(-1, newentrywidget)
        #Disable the button if we are now out of possible options to add.
        #The button does this weird blue blink just before going grey that is super annoying. Its related to the mouse
        #hover state and I don't really want to fix that right now. TODO subclass QButton to allow toggling hover state
        if not any(self.fieldlist.values()):
            self.uiref.newSearchParameterButton.setEnabled(False)

    def updateSearchParameterFieldList(self, oldfield, newfield, ignorewidget):
        #Update our field list tracker
        if len(oldfield) > 0:
            self.fieldlist[oldfield] = True
        self.fieldlist[newfield] = False
        #regenerate our list:
        #Get list of search parameter widgets to update their comboboxes with the new options
        #I was going to use an abstract model but it was removing it from all the widgets, including
        #the widget that had it selected. I didnt know how to exclude widgets and this was just easier.
        for w in self.uiref.scrollAreaWidgetContents.findChildren(SearchParameterWidget):
            if w == ignorewidget:
                continue
            w.updateFieldList(self.fieldlist.copy())

    def deleteSearchParameterWidget(self, w):
        #Make the old field available again
        self.fieldlist[w.currentfield] = True
        self.uiref.parametersFrameVLayout.removeWidget(w)
        w.deleteLater()
        #Reenable the add search parameter button if we have any options left
        if any(self.fieldlist.values()):
            self.uiref.newSearchParameterButton.setEnabled(True)

    def loadSettings(self):
        self.settings = {}
        qs = QtCore.QSettings(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, "Kylesplace.org", "movie_organizer")
        if "AppSettings" in qs.childGroups():
            qs.beginGroup("AppSettings")
            for option in qs.childKeys():
                self.settings[option] = qtypeFixer(qs.value(option))
        else:
            self.settings = {"threads": 1, "library": []}
        # Temporary fix for QTBUG-51237
        if self.settings["library"] is None:
            self.settings["library"] = []

        return self.settings

    def saveSettings(self):
        qs = QtCore.QSettings(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, "Kylesplace.org", "movie_organizer")
        qs.beginGroup("AppSettings")
        for optionname, value in self.settings.items():
            qs.setValue(optionname, value)
        qs.endGroup()
        #qs.sync #shouldnt be needed:

    def loadLibraryIntoGui(self):
        #Clear out the old list incase this is a reload
        for _ in range(self.uiref.movieLibraryInfoWidget.movieLibraryList.count()):
            self.uiref.movieLibraryInfoWidget.movieLibraryList.takeItem(0)

        r = self.movieLibrary.getFullDatabase()
        keys = list(r.keys())
        keys.sort()
        for k in keys:
            d = r[k]
            listitem = QtWidgets.QListWidgetItem(d["title"])
            listitem.setData(QtCore.Qt.UserRole, d)
            listitem.setToolTip(str(d["filename"]))
            self.uiref.movieLibraryInfoWidget.movieLibraryList.addItem(listitem)
        #TODO The fieldlist shouldnt ever update dynamically but if we ever decide to this will probably break
        self.fieldlist = OrderedDict.fromkeys(self.movieLibrary.fieldlist, True)
        self.fieldlist["dialog"] = True # Also need to match dialog which isnt a key in our movie library database
        #Update library tab title to include library size
        self.uiref.mainTabWidget.setTabText(self.uiref.mainTabWidget.indexOf(self.uiref.movieLibraryTab), "Movie Library (%d)" % len(keys))

    def updateLibraryDisplay(self, newitem, _, widget):
        if newitem is None: return #Not sure whats up here
        data = newitem.data(QtCore.Qt.UserRole)
        #0,dbdata["title"]
        #1,dbdata["directors"]
        #2,dbdata["writers"]
        #3,dbdata["producers"]
        #4,dbdata["actors"]
        #5,dbdata["composers"]
        #6,dbdata["genres"]
        #7,dbdata["runtime"]
        #8,dbdata["cover_url"]
        #9,dbdata["playcount"]
        #10,dbdata["lastplay"]
        #11,dbdata["filename"]
        #12,dbdata["filelocation"]
        #13,dbdata["imdb_id"]
        #14,dbdata["imdb_rating"]
        #15,dbdata["rating"]
        #16,dbdata["year"]
        #17,dbdata["extra1"]
        #18,dbdata["extra2"]
        #Update star rating widget
        if self.uiref.mainTabWidget.currentIndex() == 1:
            #Signal came from a search query tab, find the current tab and set our listwidget to its widget
            self.uiref.searchTabWidget.currentWidget().libraryStarRating.starClickedUpdate(data["rating"], emit=False)
        else:
            self.uiref.movieLibraryInfoWidget.libraryStarRating.starClickedUpdate(data["rating"], emit=False)
        #Format data for display:
        #most stuff is ok just the lists need to be adjusted
        listdata = list(data.values())
        #print(data["actors"])
        for i, d in enumerate(listdata):
            if isinstance(d, list) and len(d) > 0:
                #Actors lists need special care
                listdata[i] = ""
                for a in d:
                    if isinstance(a, dict):
                        listdata[i] += "<br>%s" % "{name} as {character}".format(**a)
                    else:
                        listdata[i] += "<br>%s" % a
        data = dict(zip(data.keys(), listdata))
        data["clickableurl"] = data["filelocation"] + ossep + data["filename"]
        if "dialogmatch" in data:
            data["dialogshortcut"] = "\n<br><a href=\'%s\'>PLAY MOVIE AT FOUND QUOTE</a>" % data["dialogmatch"]["movielink"]
        else:
            data["dialogshortcut"] = ""
        displaytext = """SELECTED_MOVIE_DATA: <br><br>
<a href="{clickableurl}">PLAY MOVIE LOCALLY</a>
{dialogshortcut}<br>
<b><h2>TITLE:</h2></b>  <h1>{title}</h1> <br><br>
<b>DIRECTORS:</b>  {directors}<br><br>
<b>WRITERS:</b>  {writers}<br><br>
<b>PRODUCERS:</b>  {producers}<br><br>
<b>ACTORS:</b>  {actors}<br><br>
<b>COMPOSERS:</b>  {composers}<br><br>
<b>GENRES:</b>  {genres}<br><br>
<b>RUNTIME:</b>  {runtime}<br><br>
<b>COVER_URL:</b>  {cover_url}<br><br>
<b>PLAYCOUNT:</b>  {playcount}<br><br>
<b>LASTPLAY:</b>  {lastplay}<br><br>
<b>FILENAME:</b>  {filename}<br><br>
<b>FILELOCATION:</b>  {filelocation}<br><br>
<b>IMDB_ID:</b>  {imdb_id}<br><br>
<b>IMDB_RATING:</b>  {imdb_rating}<br><br>
<b>RATING:</b>  {rating}<br><br>
<b>YEAR:</b>  {year}<br><br>
<b>EXTRA1:</b>  {extra1}<br><br>
<b>EXTRA2:</b>  {extra2}<br><br>
""".format(**data)
        widget.setHtml(displaytext)

    def openOptionsDialog(self):
        dialog = QtWidgets.QDialog(self.MainWindow)
        ui = Ui_OptionsDialog()
        ui.setupUi(dialog)
        optionsfuncs = OptionsDialogFunctions(dialog, ui, self.settings)
        optionsfuncs.saveSettingsRequest.connect(self.optionsDialogReturn)
        optionsfuncs.showOptionsDialog()

    def optionsDialogReturn(self, settings):
        self.settings = settings
        self.saveSettings()

    def startLibraryScan(self):
        #Make a progress dialog and stuff
        self.ls = LibraryScanner(self.movieLibrary, self.settings)
        self.ls.updateDisplayRequested.connect(self.loadLibraryIntoGui)
        self.ls.startScan()

    def updateSubtitleCache(self):
        #do subtitle stuffs
        r = self.movieLibrary.getFullDatabase()
        p = self.movieLibrary._SEARCH("SELECT * FROM movie_data WHERE title LIKE \"%aliens%\"")
        #self.subs = SubtitleDownloader(p, self.subtitleLibrary)
        self.subs = SubtitleDownloader(r, self.subtitleLibrary)
        self.subs.updateSubsCache()

    def quitApp(self):
        self.saveSettings()
