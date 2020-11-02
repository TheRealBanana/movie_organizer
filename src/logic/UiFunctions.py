from .movie_library import MovieLibrary
from .library_scanner import LibraryScanner

class UIFunctions:
    def __init__(self, uiref, MainWindow):
        self.uiref = uiref
        self.MainWindow = MainWindow
        self.movieLibrary = MovieLibrary()
        #initialize our application
        self.setupConnections()
        print("Doing stuff, important stuff")

    def setupConnections(self):
        self.uiref.actionScan_Media_Collection.triggered.connect(self.startLibraryScan)

    def startLibraryScan(self):
        #Make a progress dialog and stuff
        scansettings = {}
        ls = LibraryScanner(self.movieLibrary, scansettings)
        ls.startScan()

    def quitApp(self):
        #Do quitting stuff thats important
        print("YOU KNOW I CANT QUIT YOU")