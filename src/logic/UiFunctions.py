import re

import imdb.Person
from PyQt5 import QtWidgets, QtCore
from collections import OrderedDict
from .movie_library import MovieLibrary
from .library_scanner import LibraryScanner
from .options_dialog_functions import OptionsDialogFunctions
from dialogs.options_dialog import Ui_OptionsDialog
from dialogs.widgets.searchParameterWidget import SearchParameterWidget
from dialogs.widgets.movielibraryinfowidget import movieLibraryInfoWidget

#Change the way we highlight results
START_HIGHLIGHT = '<span style="background-color: #FFFF00">'
END_HIGHLIGHT = "</span>"
HIGHLIGHT_SUB_REGEX = START_HIGHLIGHT + r"\1" + END_HIGHLIGHT

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
        #initialize our application
        self.setupConnections()
        self.settings = self.loadSettings()
        #self.fieldlist = OrderedDict.fromkeys(self.movieLibrary.getFieldList(), True)
        self.fieldlist = None
        self.loadLibraryIntoGui()
        self.guimods()

    def setupConnections(self):
        self.uiref.actionScan_Media_Collection.triggered.connect(self.startLibraryScan)
        self.uiref.actionSettings.triggered.connect(self.openOptionsDialog)
        self.uiref.movieLibraryInfoWidget.movieSelectionChanged.connect(self.updateLibraryDisplay)
        self.uiref.newSearchParameterButton.clicked.connect(self.newSearchParameterButtonPressed)
        self.uiref.searchButton.clicked.connect(self.searchButtonPressed)
        self.uiref.searchTabWidget.tabCloseRequested['int'].connect(self.closeSearchTabPressed)
        self.uiref.movieLibraryInfoWidget.libraryStarRating.starRatingChanged['int'].connect(self.starRatingChanged)

    #A place for any dynamic modifications of the GUI.
    def guimods(self):
        #Remove close button from main search tab
        self.uiref.searchTabWidget.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).resize(0,0)


    def starRatingChanged(self, rating):
        curitem = self.uiref.movieLibraryInfoWidget.movieLibraryList.currentItem()
        if curitem is None:
            return
        curmoviedata = curitem.data(QtCore.Qt.UserRole)
        curmoviedata["rating"] = rating
        self.movieLibrary.updateMovieStarRating(curmoviedata["title"], rating)
        curitem.setData(QtCore.Qt.UserRole, curmoviedata)


    def closeSearchTabPressed(self, idx):
        self.uiref.searchTabWidget.removeTab(idx)

    def searchButtonPressed(self):
        #Get our search parameters
        querydata = {}
        for w in self.uiref.scrollAreaWidgetContents.findChildren(SearchParameterWidget):
            fielddata = w.returnData()
            if len(fielddata) == 0:
                continue
            querydata[w.currentfield] = fielddata

        results = self.movieLibrary.search(querydata)
        hlsections = results.pop("hlsections")
        #Now create a new search query tab and populate the results
        movieinfowidget = movieLibraryInfoWidget(self.uiref.searchTabWidget)
        movieinfowidget.movieSelectionChanged.connect(self.updateLibraryDisplay)
        #Go through our results and highlight any sections we searched with
        for k, rdata in sorted(results.items(), key=lambda t: t[0].lower()):
            listitem = QtWidgets.QListWidgetItem(rdata["title"])
            #Highlight whatever matched
            for section in hlsections:
                #Handle years differently
                if section == "year":
                    print(hlsections[section])
                    if rdata[section] in hlsections[section]:
                        rdata["year"] = START_HIGHLIGHT + str(rdata["year"]) + END_HIGHLIGHT

                elif isinstance(rdata[section], str):
                    rgx = "(%s)" % "|".join([re.escape(x) for x in hlsections[section]])
                    rdata[section] = re.sub(rgx, HIGHLIGHT_SUB_REGEX, rdata[section], flags=re.IGNORECASE|re.MULTILINE)
                elif isinstance(rdata[section], list):
                    for idx, string in enumerate(rdata[section]):
                        #List could be people or genres
                        #TODO We can match character names too. Will probably use a separate search tag for that.
                        rgx = "(%s)" % "|".join([re.escape(x) for x in hlsections[section]])
                        checkstr = string["name"] + " " + string["character"] if isinstance(string, dict) else string
                        namematch = re.search(rgx, checkstr, flags=re.I)
                        if namematch is not None:
                            if isinstance(string, dict):
                                string["name"] = re.sub("(%s)" % re.escape(namematch.group(1)), HIGHLIGHT_SUB_REGEX, string["name"], flags=re.I)
                                #Highlight character names too
                                charmatch = re.search("(%s)" % "|".join([re.escape(x) for x in hlsections[section]]), string["character"], flags=re.I)
                                if charmatch is not None:
                                    string["character"] = re.sub("(%s)" % re.escape(charmatch.group(1)), HIGHLIGHT_SUB_REGEX, string["character"], flags=re.I)
                            else:
                                rdata[section][idx] = re.sub("(%s)" % re.escape(namematch.group(1)), HIGHLIGHT_SUB_REGEX, string, flags=re.I)

                #print("%s - %s" % (section, type(d[section])))
            listitem.setData(QtCore.Qt.UserRole, rdata)
            listitem.setToolTip(str(rdata["filename"]))
            movieinfowidget.movieLibraryList.addItem(listitem)
        self.uiref.searchTabWidget.addTab(movieinfowidget, "SEARCH RESULTS (%d)" % len(results))
        self.uiref.searchTabWidget.setCurrentWidget(movieinfowidget)


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
        #8,dbdata["coverurl"]
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
        displaytext = """SELECTED_MOVIE_DATA: <br><br>

<b><h2>TITLE:</h2></b>  <h1>%s</h1> <br><br>
<b>DIRECTORS:</b>  %s<br><br>
<b>WRITERS:</b>  %s<br><br>
<b>PRODUCERS:</b>  %s<br><br>
<b>ACTORS:</b>  %s<br><br>
<b>COMPOSERS:</b>  %s<br><br>
<b>GENRES:</b>  %s<br><br>
<b>RUNTIME:</b>  %s<br><br>
<b>COVER_URL:</b>  %s<br><br>
<b>PLAYCOUNT:</b>  %s<br><br>
<b>LASTPLAY:</b>  %s<br><br>
<b>FILENAME:</b>  %s<br><br>
<b>FILELOCATION:</b>  %s<br><br>
<b>IMDB_ID:</b>  %s<br><br>
<b>IMDB_RATING:</b>  %s<br><br>
<b>RATING:</b>  %s<br><br>
<b>YEAR:</b>  %s<br><br>
<b>EXTRA1:</b>  %s<br><br>
<b>EXTRA2:</b>  %s<br><br>
""" % (*listdata,)
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
        print("AFTERSTART")

    def quitApp(self):
        self.saveSettings()
        #Do quitting stuff thats important
        print("YOU KNOW I CANT QUIT YOU")
