import re
from copy import deepcopy
from os import sep as ossep
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui
from collections import OrderedDict
from .movie_library import MovieLibrary
from .library_scanner import LibraryScanner
from .subtitles import SubtitleDownloader, SubtitleLibrary
from .search import SearchManager
from .options_dialog_functions import OptionsDialogFunctions
from .addMovieLogic import AddMovieDialogFunctions
from dialogs.options_dialog import Ui_OptionsDialog
from dialogs.widgets.searchParameterWidget import SearchParameterWidget
from dialogs.widgets.movielibraryinfowidget import movieLibraryInfoWidget, GOODSUBS_LISTITEM_BG_COLOR, NOSUBS_LISTITEM_BG_COLOR
from dialogs.editSubsDialog import Ui_editsubs_dialog
from dialogs.editMovieDataDialog import Ui_editMovieDataDialogBase, unacceptableDialog


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
        self.guimods()
        self.loadLibraryIntoGui()

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
        #Add context menu to the QListWidget library view
        self.uiref.movieLibraryInfoWidget.movieLibraryList.customContextMenuRequested["QPoint"].connect(self.libraryItemRightClickMenu)

    def libraryItemRightClickMenu(self, qpoint):
        globalclickcoords = self.uiref.movieLibraryInfoWidget.movieLibraryList.mapToGlobal(qpoint)
        editmenu = QtWidgets.QMenu()
        editmovdataaction = QtWidgets.QAction("Edit Movie Data")
        editmovdataaction.triggered.connect(self.editMovieDataDialog)
        editsubsaction = QtWidgets.QAction("Edit Subtitles")
        editsubsaction.triggered.connect(self.editSubtitlesDialog)
        deletemovieaction = QtWidgets.QAction("Delete Movie From Database")
        deletemovieaction.triggered.connect(self.delMovFromDb)
        editmenu.addAction(editmovdataaction)
        editmenu.addAction(editsubsaction)
        editmenu.addSeparator()
        editmenu.addAction(deletemovieaction)
        editmenu.addSeparator()
        #Its risky referencing an object variable thats set somewhere other than init(), but we can be sure that the
        #guimods() function is always called right after the UIFunctions()'s init() function finishes. And since this
        #function is only called on right click, theres never a scenario where we can right click before guimods() runs.
        #So don't worry about it! Also it should still be connected properly.
        editmenu.addAction(self.addmovieaction)
        editmenu.exec_(globalclickcoords)

    def delMovFromDb(self):
        current_item = self.uiref.movieLibraryInfoWidget.movieLibraryList.currentItem()
        selected_movie_data = deepcopy(current_item.data(QtCore.Qt.UserRole))
        selected_movie_title = selected_movie_data["title"]
        # Be double sure the user knows what they're about to do. This is permanent!
        popuptitle = "Permanently delete movie from database?"
        popuptext = (f"Are you sure you want to permanently delete '{selected_movie_title}' from the movie database?\n"
                     f"This will also permanently remove any saved subtitles from the database.\n\nThis cannot be undone.")
        warningpopup = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, popuptitle, popuptext, QtWidgets.QMessageBox.Cancel)
        warningpopup.addButton("Delete", QtWidgets.QMessageBox.AcceptRole)
        ret = warningpopup.exec_()
        if ret == QtWidgets.QMessageBox.AcceptRole:
            print(f"Deleting {selected_movie_title} from the movie database and any associated subtitles.")
            #No need to check if the title exists here for either of these, they check on their own.
            self.movieLibrary.delMovie(selected_movie_title)
            self.subtitleLibrary.delSubs(selected_movie_title)
            row = self.uiref.movieLibraryInfoWidget.movieLibraryList.row(current_item)
            self.uiref.movieLibraryInfoWidget.movieLibraryList.takeItem(row)


    def addMovieDialog(self):
        #Was going to be same as editMovieDataDialot but nah that sounds like a bad plan. Entering every single person
        #one by one sounds like a terrible plan. The best way to handle this, imo, is to require 2 things: Movie file
        #full path and the IMDB ID. Then we just use whatever data that IMDB ID has, and assign it to that file path.
        #Easy peasy no need to manually enter every piece of data by hand.
        #
        # It would be nice though to open up the new movie data in an editMovieDataDialog() at the end to see and edit the data.
        # Maybe in the future.
        addmov = AddMovieDialogFunctions(self.movieLibrary)
        addmov.showAddMovieDialog()

    #TODO
    # Ok, so I kinda forgot that I'm saving the file path in both the movie library database and the subtitle database.
    # Well when I update the file path through the GUI (using the edit movie dialog) and change the file path, it only
    # changes that movie library database. So when you search for dialog and click the play link, it uses the data
    # thats stored in the subtitles database, which has the outdated file path. So we need to update the file path
    # in the subtitle database too, which is slightly more complicated. In the movie database we can easily delete
    # whatever data is there and resave it. With the subtitles we'd have to pull all the data we have in the db
    # for that title, change the file path/name, and then recommit the same data. Not too bad really.
    def editMovieDataDialog(self):
        # So I always thought the data returned from data(QtCore.Qt.UserRole) was just a copy of the actual data, but
        # apparently its a reference to the actual data. I popped the title key from that dictionary it returned in
        # the setupData() function and it caused an exception when I tried to edit the subtitles, because the subs
        # edit code couldnt find the title key.
        # So a deepcopy here avoids the reference issue completely.
        current_item = self.uiref.movieLibraryInfoWidget.movieLibraryList.currentItem()
        selected_movie_data = deepcopy(current_item.data(QtCore.Qt.UserRole))
        selected_movie_title = selected_movie_data["title"]
        dialog = unacceptableDialog(self.MainWindow)
        ui = Ui_editMovieDataDialogBase()
        ui.setupUi(dialog)

        ui.setupData(selected_movie_title, selected_movie_data)
        returnstatus = bool(dialog.exec_())
        if returnstatus:
            returndata = ui.getData()
            # Two things we need to do, we gotta update the main library display, and we need to update the database
            # Library display is easy. No need to deepcopy here, Qt makes a copy on using setData()
            current_item.setData(QtCore.Qt.UserRole, returndata)
            #Also update the right hand display pane to reflect any changes
            self.updateLibraryDisplay(current_item, None, self.uiref.movieLibraryInfoWidget.movieInfoDisplay)
            # Theres no updateData function for the database, there just a delete and add.
            self.movieLibrary.delMovie(selected_movie_title)
            self.movieLibrary.addMovie(returndata) # Not passing title because its pulled from the data, does look weird tho.


    def editSubtitlesDialog(self):
        selected_movie_data = self.uiref.movieLibraryInfoWidget.movieLibraryList.currentItem().data(QtCore.Qt.UserRole)
        selected_movie_title = selected_movie_data["title"]
        dialog = QtWidgets.QDialog(self.MainWindow)
        ui = Ui_editsubs_dialog()
        ui.setupUi(dialog)
        #Setup the dialog with the movie title and any subtitles we currently have
        subdata = ""
        if self.subtitleLibrary.checkForSubs(selected_movie_title):
            subdata = self.subtitleLibrary.getSubs(selected_movie_title)
        ui.setupData(selected_movie_title, subdata, selected_movie_data["filename"])
        returnstatus = dialog.exec_()
        if bool(returnstatus) is True:
            subtitletext = ui.subtitle_text.toPlainText()
            subdata = {
                "title": selected_movie_title,
                "filename":  selected_movie_data["filename"],
                "filelocation": selected_movie_data["filelocation"],
                "subtitles": subtitletext,
                "extra1": ""
            }
            #The delSubs() function does a check to see if the title exists before it runs,
            #and it just returns if the title doesnt exist. So no need to check here.
            self.subtitleLibrary.delSubs(selected_movie_title)
            if len(subtitletext) > 0: self.subtitleLibrary.addSubs(subdata) # Saving an empty page will just delete the subs
            #Tell the user we did it
            infomessage = f"Successfully updated the subtitles database for {selected_movie_title}. \n\nUpdate size: {len(subtitletext)}"
            QtWidgets.QMessageBox.information(self.MainWindow, "Updated subtitles database", infomessage)
            print(infomessage)

    #A place for any dynamic modifications of the GUI.
    def guimods(self):
        #Remove close button from main search tab
        self.uiref.searchTabWidget.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).resize(0,0)
        #Set window title
        self.MainWindow.setWindowTitle("Movie Organizer")
        #Give the movie library info widget the ability to check for subtitles
        self.uiref.movieLibraryInfoWidget.setSubRef(self.subtitleLibrary)
        #Add another main menu option
        #If you don't make the action part of the object they go out of reference at the end of guimods() and the menu
        #option never gets added (or rather it gets added and is then immediately deleted).
        self.addmovieaction = QtWidgets.QAction("Manually Add Movie to Database")
        self.addmovieaction.triggered.connect(self.addMovieDialog)
        self.uiref.menuFile.addAction(self.addmovieaction)

    def updatePlayCount(self, movietitle):
        #Update the database and then update the display search results and main library view
        curdate = datetime.now().strftime('%d/%b/%Y-%I:%M:%S %p')
        count = self.movieLibrary.updatePlayCount(movietitle, curdate)
        self.updateCurrentLibraryItemData("playcount", count)
        self.updateCurrentLibraryItemData("lastplay", curdate)

    def starRatingChanged(self, rating):
        self.updateCurrentLibraryItemData("rating", rating)
        moviedata = self.getCurrentListItem().data(QtCore.Qt.UserRole)
        movietitle = moviedata["title"]
        self.movieLibrary.updateMovieStarRating(movietitle, rating)

    def getCurrentListItem(self):
        if self.uiref.mainTabWidget.currentIndex() == 1: #Came from search tab
            return self.uiref.searchTabWidget.currentWidget().movieLibraryList.currentItem()
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
            #TODO FIXME This is broken because findItems looks at the titles of each which wont work with matchexact.
            libitem = self.uiref.movieLibraryInfoWidget.movieLibraryList.findItems("(%s)        %s" % (searchresultdata["year"], searchresultdata["cleantitle"]), QtCore.Qt.MatchStartsWith)[0]
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
        movieinfowidget.setSubRef(self.subtitleLibrary)
        #Create search results tab
        self.uiref.searchTabWidget.addTab(movieinfowidget, "~ SEARCH RESULTS (0) ~")
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

    def loadLibraryIntoGui(self, sort="title"):
        #Clear out the old list incase this is a reload
        for _ in range(self.uiref.movieLibraryInfoWidget.movieLibraryList.count()):
            self.uiref.movieLibraryInfoWidget.movieLibraryList.takeItem(0)

        r = self.movieLibrary.getFullDatabase()
        keys = list(r.keys())
        keys.sort()
        for k in keys:
            d = r[k]
            listitem = QtWidgets.QListWidgetItem(f'({d["year"]})        {d["title"]}')
            #Check if we have subtitles for this title, if so add an indicator like changing the background
            if not self.subtitleLibrary.checkForSubs(d["title"]):
                bgcolor = QtGui.QColor(*NOSUBS_LISTITEM_BG_COLOR) # Kind of a light green background
                listitem.setBackground(QtGui.QBrush(bgcolor))
            listitem.setData(QtCore.Qt.UserRole, d)
            listitem.setToolTip(str(d["filename"]))
            self.uiref.movieLibraryInfoWidget.movieLibraryList.addItem(listitem)
        #TODO The fieldlist shouldnt ever update dynamically but if we ever decide to this will probably break
        self.fieldlist = OrderedDict.fromkeys(self.movieLibrary.fieldlist, True)
        self.fieldlist["dialog"] = True # Also need to match dialog which isnt a key in our movie library database
        self.fieldlist["All People"] = True # Adding a way to search through every field except title, genre, runtime, etc. Just people fields.
        #Update library tab title to include library size
        self.uiref.mainTabWidget.setTabText(self.uiref.mainTabWidget.indexOf(self.uiref.movieLibraryTab), "Movie Library (%d)" % len(keys))
        #Sort the library list. By default the sorting is based on the QListWidgetItem's text() value, but its case sensitive.
        #To make it not case sensitive requires a custom subclass and __lt__() method. Since we do our own sorting anyway when the user
        #changes the sort key, we just make use of that and make the case sensitive change there. It works, but the only problem
        #is that it only works after you manually select some other sort key and then go back to title. So we'll just resort
        #here right away with the title key and not worry about it.
        self.uiref.movieLibraryInfoWidget.sortOptionsUpdate(None)

    def createNameLinks(self, data):
        #directors, writers, producers, composers, and genres are all simple lists, actors is a list of dictionaries.
        #TODO figure out what href link will work, too tired now

        return data

    def updateLibraryDisplay(self, newitem, _, widget):
        if newitem is None: return #Not sure whats up here
        data = newitem.data(QtCore.Qt.UserRole)
        #Adds links to the names in the library display for quick searching
        data = self.createNameLinks(data)
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
                        #Should only ever be actors that gets formatted here
                        listdata[i] += "<br>%s" % "{name} as {character}".format(**a)
                    else:
                        #This formats data for the keys: directors, writers, producers, composers, genres, and some actors
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
<b><h2>TITLE:</h2></b>  <h1>{title} ({year})</h1> <br><br>
<b>DIRECTORS:</b>  {directors}<br><br>
<b>WRITERS:</b>  {writers}<br><br>
<b>PRODUCERS:</b>  {producers}<br><br>
<b>ACTORS:</b>  {actors}<br><br>
<b>COMPOSERS:</b>  {composers}<br><br>
<b>GENRES:</b>  {genres}<br><br>
<b>RUNTIME:</b>  {runtime}<br><br>
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
