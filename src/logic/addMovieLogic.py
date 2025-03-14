from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QFileDialog, QDialog
from dialogs.addMovieDialog import Ui_addMovieDialog
from dialogs.editMovieDataDialog import Ui_editMovieDataDialogBase, unacceptableDialog
from .library_scanner import get_person_names
from .library_scanner import S3DATASET_LOCATION
from collections import OrderedDict as OD
import imdb, sys, os.path

class AddMovieDialogFunctions(QObject):
    def __init__(self, movie_library_ref, parent=None):
        super(AddMovieDialogFunctions, self).__init__(parent)
        self.dialog = QDialog(parent)
        self.ui = Ui_addMovieDialog()
        self.idCheckGood = False
        self.movie_data = None
        self.movie_library_ref = movie_library_ref

    def showAddMovieDialog(self):
        self.setupDialog()
        self.setupConnections()

        returnstatus = bool(self.dialog.exec_())
        print(type((returnstatus)))
        print(returnstatus)
        print("DIALOGSETUP")
        self.wrapMovieData()

    def setupDialog(self):
        self.ui.setupUi(self.dialog)

    def setupConnections(self):
        self.ui.browseButton.clicked.connect(self.showFileBrowseDialog)
        self.ui.checkIdButton.clicked.connect(self.checkIMDBid)

    def checkIMDBid(self):
        print(sys.version)
        rawid = str(self.ui.imdbidLineEdit.text())
        if rawid.isdigit() is True:
            imdbid = int(rawid)
            print("GUT")
        else:
            print("BAD")
            self.idCheckGood = False
            return
        #Was going to reuse my imdb code but its so specific to the threaded scanner, it would be a mess.
        ia = imdb.IMDb("s3", "sqlite:///%s" % S3DATASET_LOCATION)
        movie_data = ia.get_movie(imdbid)
        if "title" in movie_data:
            print(f"Got good movie data from IMDBid {imdbid}")
            print(f"Checking if we have that title already in the database...")
            if self.movie_library_ref.checkForTitle(movie_data["title"]) is True:
                print("Already in our database!")
                self.idCheckGood = False
                return
            else:
                print("NEW MOVIE!")
                self.idCheckGood = True
        self.movie_data = movie_data

    # The data we get from the IMDB database is not suitable for our application and has to be modified a little bit
    def wrapMovieData(self):
        filepath = self.ui.filePathLineEdit.text()
        fpath = os.path.dirname(filepath)   # Get directory path
        fname = os.path.basename(filepath)  # Get file name
        imdbid = self.movie_data.movieID
        movie_data = self.movie_data.data
        dbdata = OD()
        dbdata["title"] = movie_data["title"]
        if "director" in movie_data:
            dbdata["directors"] = get_person_names(movie_data["director"])
        elif "directors" in movie_data:
            dbdata["directors"] = get_person_names(movie_data["directors"])
        else:
            dbdata["directors"] = "NO_DIRECTOR_FOUND"
        if "writer" in movie_data:
            dbdata["writers"] = get_person_names(movie_data["writer"])
        elif "writers" in movie_data:
            dbdata["writers"] = get_person_names(movie_data["writers"])
        else:
            dbdata["writers"] = "NO_WRITER_FOUND"
        dbdata["producers"] = get_person_names(movie_data["producers"]) if "producers" in movie_data else "NO_PRODUCER_FOUND"

        #Just to check, I dont want to add if they arent needed but I have no idea
        if "producer" in movie_data:
            print("---PRODUCER---  %s" % dbdata["title"])
        if "composer" in movie_data:
            print("---COMPOSER---  %s" % dbdata["title"])

        #Should always have a cast. If we dont this is probably the wrong entry

        dbdata["actors"] = get_person_names(movie_data["cast"])
        #Sometimes composers is actually labeled something else so we combine them all
        #Gotta love the inconsistent data in the IMDb
        dbdata["composers"] = []
        if "music department" in movie_data:
            dbdata["composers"] += get_person_names(movie_data["music department"])
        if "composers" in movie_data:
            dbdata["composers"] += get_person_names(movie_data["composers"])
        if "composer" in movie_data:
            dbdata["composers"] += get_person_names(movie_data["composer"])
        if len(dbdata["composers"]) == 0: dbdata["composers"] = "NO_COMPOSER_FOUND"

        dbdata["genres"] = str(movie_data["genres"])
        dbdata["runtime"] = movie_data["runtimes"][0]
        #cover url isnt in the text data files so we wont be using this for now
        #will be easy to get it manually later when we need it
        #sizeindex = movie_data["cover url"].index("@._V1")
        #dbdata["coverurl"] = movie_data["cover url"][:sizeindex] + "@._V1_SX600.jpg" # cover url is small otherwise. Can grab full size by omitting _SX600
        dbdata["coverurl"] = ""
        dbdata["playcount"] = 0
        dbdata["lastplay"] = ""
        dbdata["filename"] = fname
        dbdata["filelocation"] = fpath
        dbdata["imdb_id"] = imdbid
        dbdata["imdb_rating"] = str(movie_data["rating"]) if "rating" in movie_data else "-1"
        dbdata["rating"] = 0
        dbdata["year"] = movie_data["year"]
        dbdata["extra1"] = ""
        dbdata["extra2"] = ""
        self.spawnEditMovieDialog(dbdata)


    def spawnEditMovieDialog(self, movie_data):
        selected_movie_title = movie_data["title"]
        dialog = unacceptableDialog(self.dialog)
        ui = Ui_editMovieDataDialogBase()
        ui.setupUi(dialog)

        ui.setupData(selected_movie_title, movie_data)
        returnstatus = bool(dialog.exec_())
        """
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
        """



    def showFileBrowseDialog(self):
        filedialog = QFileDialog()
        filedialog.setAcceptMode(QFileDialog.AcceptOpen)
        filedialog.setFileMode(QFileDialog.ExistingFile)
        filedialog.setViewMode(QFileDialog.Detail)
        parent = self.dialog
        caption = "Select a media file..."
        selectedfile, _ = filedialog.getOpenFileName(parent, caption)
        self.ui.filePathLineEdit.setText(selectedfile)

        self.checkIfEnableSave()

    #Simple function, check if we should enable the save button. If not disable it.
    def checkIfEnableSave(self):
        if len(self.ui.filePathLineEdit.text()) > 0 and self.idCheckGood is True:
            self.ui.saveButton.setEnabled(True)
        else:
            self.ui.saveButton.setEnabled(False)