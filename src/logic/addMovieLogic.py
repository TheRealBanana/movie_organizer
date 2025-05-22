from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QFileDialog, QDialog
from dialogs.addMovieDialog import Ui_addMovieDialog
from dialogs.editMovieDataDialog import Ui_editMovieDataDialogBase, unacceptableDialog
from .library_scanner import get_person_names
from .library_scanner import S3DATASET_LOCATION
from collections import OrderedDict as OD
import imdb, sys, os.path

class AddMovieDialogFunctions(QObject):
    def __init__(self, movie_library_ref, update_library_view_callback, parent=None):
        super(AddMovieDialogFunctions, self).__init__(parent)
        self.dialog = QDialog(parent)
        self.ui = Ui_addMovieDialog()
        self.idCheckGood = False
        self.movie_data = None
        self.movie_library_ref = movie_library_ref
        self.update_library_view_callback = update_library_view_callback

    def showAddMovieDialog(self):
        self.setupDialog()
        self.setupConnections()

        returnstatus = bool(self.dialog.exec_())
        if returnstatus is True:
            print("DIALOGSETUP")
            self.wrapMovieData()

    def setupDialog(self):
        self.ui.setupUi(self.dialog)

    def setupConnections(self):
        self.ui.browseButton.clicked.connect(self.showFileBrowseDialog)
        self.ui.checkIdButton.clicked.connect(self.checkIMDBid)


    #Bleh, I dont like this method. Lots of code reuse, that weird return in weird places. The fact that every time we
    #set the idCheckGood we also have to run checkIfEnabledSave() and theres like 4 spots that happens is annoying.
    #Need to rewrite this without so much if/else and code reuse. Is critical to do however, since you don't want the
    #ui to become out of sync and allow a manual addition to continue when the ID or file path is incorrect.
    def checkIMDBid(self):
        print(sys.version)
        rawid = str(self.ui.imdbidLineEdit.text())
        if rawid.isdigit() is True:
            imdbid = int(rawid)
            self.idCheckGood = True
            self.checkIfEnableSave()
            print("GUT")
        else:
            print("BAD")
            self.idCheckGood = False
            self.checkIfEnableSave()
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
        #Since we're sure this is the correct IMDB id, we'll now do an online check.
        #Only doing it after the offline check since thats how the other bits of code do it, but im not convinced.
        #I think we could probably just run an online only check, but eh whatever. It feels better this way, you don't
        #get the app freezing when you click the "check" button. You just get a slight delay between clicking 'save'
        #and the edit movie dialog appearing (which is where the online check is performed). Doing just the online
        #check would be very annoying, having the whole UI freeze for 5-10 seconds while it downloaded the data.
        ib = imdb.IMDb() # Online check
        self.movie_data = ib.get_movie(self.movie_data.movieID)
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

        dbdata["genres"] = movie_data["genres"]
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
        if returnstatus:
            returndata = ui.getData()
            # Two things we need to do, we need to add the new data to the database and then request a refresh of the
            # library display to add the new movie data to the GUI.
            self.movie_library_ref.addMovie(returndata) # Not passing title because its pulled from the data, does look weird tho.
            self.update_library_view_callback()





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