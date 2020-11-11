from PyQt5 import QtWidgets, QtCore
from .movie_library import MovieLibrary
from .library_scanner import LibraryScanner
from .options_dialog_functions import OptionsDialogFunctions
from dialogs.options_dialog import Ui_OptionsDialog


def qstringFixer(self, value):
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
        self.loadLibraryIntoGui()

    def setupConnections(self):
        self.uiref.actionScan_Media_Collection.triggered.connect(self.startLibraryScan)
        self.uiref.actionSettings.triggered.connect(self.openOptionsDialog)
        self.uiref.movieLibraryList.currentItemChanged.connect(self.updateLibraryDisplay)

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
        #qs.sync #shouldnt be needed

    def loadLibraryIntoGui(self):
        print("LOAD")
        r = self.movieLibrary.getFullDatabase()
        keys = list(r.keys())
        keys.sort()
        for k in keys:
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
            #11,dbdata["filelocation"]
            #12,dbdata["imdb_id"]
            #13,dbdata["imdb_rating"]
            #14,dbdata["rating"]
            #15,dbdata["extra1"]
            #16,dbdata["extra2"]

            d = r[k]
            listitem = QtWidgets.QListWidgetItem(d[0])
            listitem.setData(QtCore.Qt.UserRole, d)
            listitem.setToolTip(str(d[11]))
            self.uiref.movieLibraryList.addItem(listitem)

    def updateLibraryDisplay(self, newitem, _):
        print("CHANGED")
        data = newitem.data(QtCore.Qt.UserRole)
        title = newitem.text()
        path = newitem.toolTip()

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
        #11,dbdata["filelocation"]
        #12,dbdata["imdb_id"]
        #13,dbdata["imdb_rating"]
        #14,dbdata["rating"]
        #15,dbdata["extra1"]
        #16,dbdata["extra2"]
        #Format data for display:
        #most stuff is ok just the lists need to be adjusted
        for i, d in enumerate(data):
            if isinstance(d, list):
                #Actors lists need special care
                if isinstance(d[0], dict):
                    data[i] = "<br>".join(["{name} as {character}".format(**r) for r in d])
                else:
                    data[i] = ", ".join(d)

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
<b>FILELOCATION:</b>  %s<br><br>
<b>IMDB_ID:</b>  %s<br><br>
<b>IMDB_RATING:</b>  %s<br><br>
<b>RATING:</b>  %s<br><br>
<b>EXTRA1:</b>  %s<br><br>
<b>EXTRA2:</b>  %s<br><br>


      
""" % (*data,)
        self.uiref.movieInfoDisplay.setHtml(displaytext)

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