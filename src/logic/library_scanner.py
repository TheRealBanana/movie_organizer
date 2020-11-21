# Very basic multithreaded crawler that will crawl each drive on a separate thread.
# If you are using SSD's you could probably get away with multiple crawlers per drive
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QVariant
from collections import OrderedDict as OD
from dialogs.widgets.generic_progress_bar import genericProgressDialog
import imdb
import pickle
import re
import os
import os.path
from PyQt5.Qt import QApplication

from time import sleep

import traceback
IGNORE_FOLDERS = ["ZZZZZZZZZZZZZZZZ"]

VIDEO_EXTENSIONS=["avi", "divx", "amv", "mpg", "mpeg", "mpe", "m1v", "m2v",
                  "mpv2", "mp2v", "m2p", "vob", "evo", "mod", "ts", "m2ts",
                  "m2t", "mts", "pva", "tp", "tpr", "mp4", "m4v", "mp4v",
                  "mpv4", "hdmov", "mov", "3gp", "3gpp", "3g2", "3gp2",
                  "mkv", "webm", "ogm", "ogv", "flv", "f4v", "wmv", "rmvb",
                  "rm", "dv"]

def is_video_file(filename):
    fileextensionreg = re.match("^.*?\.([a-z0-9]{1,6})$", filename, re.IGNORECASE)
    if fileextensionreg is not None:
        fext = fileextensionreg.group(1)
        if fext in VIDEO_EXTENSIONS:
            # Ignore sample videos and TV shows
            if not re.match("(^.*?sample\.([a-z0-9]{1,6})$|^sample.*$)", fext, re.IGNORECASE) and \
               not re.search("(((s|e)[0-9]{1,2}){2}|[0-9]{1,2}x[0-9]{1,2})", fext, re.IGNORECASE):
                    return True
    return False

#Helper function to just get names from imdb.Person.Person types
#Also detects actor roles and returns a list with the character's name
def get_person_names(personlist):
    if personlist is None or len(personlist) == 0:
        return []
    if not isinstance(personlist, list):
        raise(Exception("Expected list but got %s" % type(personlist)))
    namelist = []
    for p in personlist:
        if not isinstance(p, imdb.Person.Person) or p.personID is None:
            continue
        #Is this person playing a character?
        if "name" in p.currentRole.data:
            retdata = {}
            retdata["name"] = p.data["name"]
            retdata["character"] = p.currentRole.data["name"]
            namelist.append(retdata)
        else:
            namelist.append(p.data["name"])
    return namelist

class imdbInfoGrabber(QObject):
    newTitleData = pyqtSignal(dict)
    workFinished = pyqtSignal()
    progressUpdate = pyqtSignal(str)

    def __init__(self, filedata, ithread, parent=None):
        super(imdbInfoGrabber, self).__init__(parent)
        self.setObjectName("Crawler-%s" % ithread.currentThreadId())
        self.filedata = filedata
        self.ithread = ithread
        self.stopping = False

    def stopt(self):
        self.stopping = True
        #Normally this would risk double emiting workFinished which causes all sorts of weird issues
        #We get away with this because its our only thread and we can do special things to mitigate the issue.
        self.workFinished.emit()

    def getInfo(self):
        #TODO DELETEME
        p = 0
        movie_title_regex =  re.compile("^(.*?)[\s\.]?((?:19|20)[0-9]{2}).*?(720|1080|2160)", re.IGNORECASE)
        #group 1 = movie title (might have trailing space)
        #group 2 = year
        #group 3 = resolution

        ia = imdb.IMDb()
        #self.filedata[tld] = [ [filename, foldername], ...]
        for tld, files in self.filedata.items():
            self.progressUpdate.emit("Checking TLD: %s" % tld)
            if self.stopping: return

            for finfo in files:
                fname = finfo[0]
                fpath = finfo[1]
                self.progressUpdate.emit("Checking if file is a movie: %s" % fname)
                freg = movie_title_regex.search(fname)
                if freg is not None:
                    movietitle = freg.group(1).replace(".", " ") # Periods mess things up
                    movieyear = freg.group(2)
                    self.progressUpdate.emit("Searching IMDb for '%s %s'" % (movietitle, movieyear))
                    searchdata = ia.search_movie("%s %s" % (movietitle, movieyear))
                    #Try and find the one that has a matching year, best we can do to be sure
                    mid = None
                    for result in searchdata:
                        # Allow some fuzz. Some of my collection has the year off by one or two compared to imdb
                        # Should prevent the issue I was having with weird same titles from decades later or earlier
                        # Sometimes the wrong results are still only a year difference. Just hope the first result is ours. :/
                        if abs(int(result.data["year"]) - int(movieyear)) <= 2:
                            mid = result.movieID
                            self.progressUpdate.emit("Found IMDb ID for %s:  %s" % (movietitle, mid))
                            break
                    if mid is not None: # Only check first result and pray
                        self.progressUpdate.emit("Found good IMDb data for %s" % fname)
                        movie_data = ia.get_movie(mid).data
                        #Build up our dictionary to emit
                        dbdata = OD()
                        dbdata["title"] = movie_data["title"]
                        dbdata["directors"] = pickle.dumps(get_person_names(movie_data["directors"]))
                        dbdata["writers"] = pickle.dumps(get_person_names(movie_data["writers"]))
                        dbdata["producers"] = pickle.dumps(get_person_names(movie_data["producers"]))
                        dbdata["actors"] = pickle.dumps(get_person_names(movie_data["cast"]))
                        dbdata["composers"] = pickle.dumps(get_person_names(movie_data["composers"]))
                        dbdata["genres"] = pickle.dumps(movie_data["genres"])
                        dbdata["runtime"] = movie_data["runtimes"][0]
                        sizeindex = movie_data["cover url"].index("@._V1")
                        dbdata["coverurl"] = movie_data["cover url"][:sizeindex] + "@._V1_SX600.jpg" # cover url is small otherwise. Can grab full size by omitting _SX600
                        dbdata["playcount"] = 0
                        dbdata["lastplay"] = ""
                        dbdata["filelocation"] = fpath
                        dbdata["imdb_id"] = mid
                        dbdata["imdb_rating"] = movie_data["rating"]
                        dbdata["rating"] = 0
                        dbdata["extra1"] = ""
                        dbdata["extra2"] = ""
                        self.newTitleData.emit(dbdata)
                    else:
                        self.progressUpdate.emit("Didn't pass year check for %s" % fname)
                        print(type(searchdata[0]))
                else:
                    e = "Encountered error with title:  %s" % fname
                    self.progressUpdate.emit(e)
                    print(e)
            #self.newTitleData.emit(files[0])
        self.workFinished.emit()



#Job of the Crawler is just to discover filenames and nothing more
#We will get IMDB info using a separate process
class Crawler(QObject):
    foundNewFiles = pyqtSignal(dict)
    workFinished = pyqtSignal(QVariant)
    progressUpdate = pyqtSignal(str)

    def __init__(self, startpath, ithread, parent=None):
        super(Crawler, self).__init__(parent)
        self.setObjectName("Crawler-%s" % ithread.currentThreadId())
        self.ithread = ithread
        self.startpath = startpath
        self.stopping = False

    def stopt(self):
        self.stopping = True
        #self.workFinished.emit(self)

    def crawl(self, directory):
        if self.stopping is True: return None

        allfiles = os.listdir(directory)
        #List comprehension looks cool but prevents us from canceling mid-search
        #dirs = [d for d in allfiles if os.path.isdir(os.path.join(directory, d)) is True]
        #dirs = [d for d in allfiles if os.path.isdir(os.path.join(directory, d)) is True and
        #        not re.search("s[0-9]{2}", d, re.IGNORECASE)] #No TV shows dammit
        dirs = []
        for d in allfiles:
            if self.stopping is True:
                return None
            if os.path.isdir(os.path.join(directory, d)) is True and not re.search("s[0-9]{2}", d, re.IGNORECASE): #ignore tv shows
                self.progressUpdate.emit("Found directory: %s" % d)
                dirs.append(d)
        #Remove excluded dirs
        for d in dirs:
            if self.stopping is True: return None
            for x in IGNORE_FOLDERS:
                if self.stopping is True: return None

                if re.search(x, d, re.IGNORECASE):
                    dirs.remove(d)
                    self.progressUpdate.emit("Excluded directory: %s" % d)
                    print("REMOVED: %s" % d)

        # Now that we're down to the bottom of the dir chain, we work our way back through the files
        #files = [f for f in allfiles if os.path.isfile(os.path.join(directory, f)) is True]
        #files = [f for f in allfiles if os.path.isfile(os.path.join(directory, f)) is True and is_video_file(f) is True]
        #files = {f:directory for f in allfiles if os.path.isfile(os.path.join(directory, f)) is True and is_video_file(f) is True}
        files = []
        for f in allfiles:
            if self.stopping is True: return None

            #Enabling this one and the "Found video file" emit() causes crashes because they can sometimes emit too close together.
            #self.progressUpdate.emit("Checking if file is a video:  %s" % f)
            if os.path.isfile(os.path.join(directory, f)) is True and is_video_file(f) is True:
                self.progressUpdate.emit("Found video file:  %s" % f)
                files.append((f, directory))
        # Send out the files we found here
        if len(files) > 0:
            self.foundNewFiles.emit({"files": files, "directory": self.startpath})

        # find more files
        for d in dirs:
            if self.stopping is True: return None
            self.progressUpdate.emit("Crawling to next sub-directory: %s" % d)
            self.crawl(os.path.join(directory, d))

    def doWork(self):
        self.crawl(os.path.realpath(self.startpath))
        print("DONE WITH THREADED STUFFS")
        self.workFinished.emit(self)
        return


class LibraryScanner(QObject):
    updateDisplayRequested = pyqtSignal()

    def __init__(self, libraryref, scansettings):
        super(LibraryScanner, self).__init__()
        self.setObjectName("LibraryScanner")
        self.stopping = False
        self.libref = libraryref
        self.scansettings = scansettings
        self.activecrawlerthreads = []
        self.imdbworker = None
        self.folderstoscan = scansettings["library"].copy()
        self.filecount = -1
        self.filelist = {}
        self.progressbar = None

    def startScan(self):
        #Spin off a crawl processes for each folder
        print("SCAN START")
        print("Max threads: %d" % int(self.scansettings["threads"]))
        print("Top level directories we are scanning:")
        for d in self.scansettings["library"]:
            print(d)
        print("-----------")
        self.stopping = False
        self.filecount = 0
        self.filelist = {}
        #Create our progress bar
        self.progressbar = genericProgressDialog()
        self.progressbar.cancelButton.clicked.connect(self.stopScan)
        self.progressbar.progressBar.setMaximum(len(self.scansettings["library"]))
        self.progressbar.progressBar.setMinimum(0)
        self.progressbar.progressBar.setValue(0)
        self.progressbar.progressLabel.setText("Found 0 Media Files")
        self.progressbar.show()
        QApplication.processEvents()
        self.spawnCrawlerThreads()

    def spawnCrawlerThreads(self):
        # Keep going until all folders have been scanned and all threads have joined
        while len(self.activecrawlerthreads) < int(self.scansettings["threads"]) and len(self.folderstoscan) > 0:
            newthread = QThread()
            newthread.setTerminationEnabled(True) # Can't find documentation on what the default is or how to check what its currently set to.
            folder = self.folderstoscan.pop(-1)
            #c = Crawler(folder, searchparams=None, thread=newthread)
            c = Crawler(folder, newthread)
            c.moveToThread(newthread)
            newthread.started.connect(c.doWork)
            c.workFinished.connect(self.crawlerWorkFinishedCallback)
            c.foundNewFiles.connect(self.newFileCallback)
            c.progressUpdate.connect(self.updateProgressbarDetails)
            newthread.start()
            print("New thread %s" % folder)
            self.activecrawlerthreads.append(c)

    def updateProgressbarDetails(self, s):
        self.progressbar.updateDetailsText(s)

    def updateImdbProgressBar(self):
        oldlabel = str(self.progressbar.progressLabel.text())
        oldcount = int(re.search("%\]\s+([0-9]{1,10})\s+", oldlabel).group(1))
        newcount = oldcount + 1
        perc = float(newcount)/float(self.filecount) * 100
        progresslabel = "[%.1f%%] %s titles added to database... " % (perc, newcount)
        self.progressbar.progressBar.setValue(newcount)
        self.progressbar.progressLabel.setText(progresslabel)
        QApplication.processEvents()


    def totalFileCountUpdate(self, filecount):
        #User to track total files
        self.filecount += filecount
        self.progressbar.progressLabel.setText("Found %s Media Files..." % self.filecount)
        QApplication.processEvents()

    def crawlerWorkFinishedCallback(self, c):
        #Terminate the thread and pop it from our thread list
        c.ithread.quit()
        c.ithread.wait()
        self.activecrawlerthreads.remove(c)
        if self.stopping is True:
            return
        if len(self.folderstoscan) > 0:
            self.spawnCrawlerThreads()
        # FINISHED OUR SCAN
        elif len(self.activecrawlerthreads) == 0:
            self.startImdbInfoGrab()
        self.progressbar.progressBar.setValue(self.progressbar.progressBar.value()+1)
        QApplication.processEvents()

    def newFileCallback(self, filedata):
        #filedata[files] = [ (filename: fulldirpath), ...]
        tld = filedata["directory"]
        if tld not in self.filelist:
            self.filelist[tld] = []
        self.filelist[tld] += filedata["files"]
        self.totalFileCountUpdate(len(filedata["files"]))
        QApplication.processEvents()

    def startImdbInfoGrab(self):
        if self.imdbworker is not None:
            self.imdbThreadFinishedCallback()
        #Create our worker and qthread
        ithread = QThread()
        self.imdbworker = imdbInfoGrabber(self.filelist, ithread)
        ithread.started.connect(self.imdbworker.getInfo)
        self.imdbworker.newTitleData.connect(self.imdbThreadUpdateCallback)
        self.imdbworker.workFinished.connect(self.imdbThreadFinishedCallback)
        self.imdbworker.progressUpdate.connect(self.updateProgressbarDetails)
        #ithread.finished.connect(self.imdbThreadFinishedCallback)
        self.imdbworker.moveToThread(ithread)
        ithread.start()
        #self.updateDisplayRequested.emit()
        #Set up the progress bar for the next step
        self.progressbar.progressBar.setMaximum(self.filecount)
        self.progressbar.progressBar.setValue(0)
        self.progressbar.setWindowTitle("Retrieving IMDB information for found titles...")
        progresslabel = "[%.1f%%] %s titles added to database... " % (0.0, 0)
        self.progressbar.progressLabel.setText(progresslabel)
        QApplication.processEvents()

    def imdbThreadUpdateCallback(self, dbdata):
        self.libref.addMovie(dbdata)
        print("UPDATECALL")
        self.updateImdbProgressBar()
        QApplication.processEvents()

    def imdbThreadFinishedCallback(self):
        self.imdbworker.stopping = True
        self.imdbworker.ithread.quit()
        self.imdbworker.ithread.wait()
        self.imdbworker = None

    def stopScan(self):
        self.stopping = True
        for c in self.activecrawlerthreads:
            c.stopt()
        if self.imdbworker is not None:
            self.imdbworker.stopt()
        self.progressbar.close()
        QApplication.processEvents()

