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

    def setupConnections(self):
        self.uiref.actionScan_Media_Collection.triggered.connect(self.startLibraryScan)
        self.uiref.actionSettings.triggered.connect(self.openOptionsDialog)

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
        self.ls.startScan()
        print("AFTERSTART")

    def quitApp(self):
        self.saveSettings()
        #Do quitting stuff thats important
        print("YOU KNOW I CANT QUIT YOU")