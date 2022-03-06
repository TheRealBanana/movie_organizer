# Very basic multithreaded crawler that will crawl each drive on a separate thread.
# If you are using SSD's you could probably get away with multiple crawlers per drive
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QVariant
from collections import OrderedDict as OD
from dialogs.widgets.generic_progress_bar import genericProgressDialog
import imdb
import re
import os
import os.path
import unicodedata
from difflib import SequenceMatcher
# Using a rather low match ratio just to weed out the completely wrong results but try to keep partial title matches (might catch on sequels tho)
MASTER_RATIO = 0.85

S3DATASET_LOCATION = "C:\imdb_data\dbout\imdbdataset_Sept.27.2021.sqlite"


IGNORE_FOLDERS = ["ZZZZZZZZZZZZZZZZ"]

VIDEO_EXTENSIONS=["avi", "divx", "amv", "mpg", "mpeg", "mpe", "m1v", "m2v",
                  "mpv2", "mp2v", "m2p", "vob", "evo", "mod", "ts", "m2ts",
                  "m2t", "mts", "pva", "tp", "tpr", "mp4", "m4v", "mp4v",
                  "mpv4", "hdmov", "mov", "3gp", "3gpp", "3g2", "3gp2",
                  "mkv", "webm", "ogm", "ogv", "flv", "f4v", "wmv", "rmvb",
                  "rm", "dv"]

REMOVE_KEYWORDS = ["proper", "repack", "unrated", "part 1", "part 2", "2in1"]

movie_title_regex =        re.compile("^(.*?)[\s\.]?((?:19|20)[0-9]{2}).*?(720|1080|2160)", re.IGNORECASE)
movie_title_regex_noyear = re.compile("^(.*)[\s\.]?((?:19|20)[0-9]{2})?.*?(720|1080|2160)", re.IGNORECASE)
#group 1 = movie title (might have trailing space)
#group 2 = year
#group 3 = resolution
def is_movie_file(filename):
    return True if (movie_title_regex.search(filename) is not None or movie_title_regex_noyear.search(filename) is not None) else False

def is_video_file(filename):
    fileextensionreg = re.match("^.*?\.([a-z0-9]{1,6})$", filename, re.IGNORECASE)
    if fileextensionreg is not None:
        fext = fileextensionreg.group(1)
        if fext in VIDEO_EXTENSIONS:
            # Ignore sample videos and TV shows
            if not re.match("(^.*?sample\.([a-z0-9]{1,6})$|^sample.*$)", filename, re.IGNORECASE) and \
               not re.search("((([se])[0-9]{1,2}){2}|[0-9]{1,2}x[0-9]{1,2})", filename, re.IGNORECASE):
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
        #Is this person playing multiple characters?
        if isinstance(p.currentRole, imdb.utils.RolesList):
            retdata = {}
            retdata["name"] = p.data["name"]
            retdata["character"] = p.currentRole[0]["name"]
            for c in p.currentRole[1:]:
                retdata["character"] += ", " + c["name"]
            namelist.append(retdata)
        elif "name" in p.currentRole.data:
            retdata = {}
            retdata["name"] = p.data["name"]
            retdata["character"] = p.currentRole.data["name"]
            namelist.append(retdata)
        else:
            try:
                namelist.append(p.data["name"])
            except Exception as e:
                print(e)
                print(p.data)
                print(dir(p))
    return namelist

class imdbInfoGrabber(QObject):
    newTitleData = pyqtSignal(dict)
    workFinished = pyqtSignal()
    progressUpdate = pyqtSignal(str)
    processingFile = pyqtSignal()

    def __init__(self, filedata, ithread, checkFunc, parent=None):
        super(imdbInfoGrabber, self).__init__(parent)
        self.setObjectName("Crawler-%s" % ithread.currentThreadId())
        self.filedata = filedata
        self.ithread = ithread
        self.checkexistsfunc = checkFunc
        self.stopping = False

    def stopt(self):
        self.stopping = True
        #Normally this would risk double emiting workFinished which causes all sorts of weird issues
        #We get away with this because its our only thread and we can do special things to mitigate the issue.
        self.workFinished.emit()


    def filterImdbResults(self, ia, results_list, movieyear):
        #Filter out non-movie results and sort by a given data key
        outlist = []
        for result in results_list:
            #Now that we have the title as it appears in the IMDB we can do another check against our own db
            #Some titles change a small amount between the file name and the imdb but the final title in our db
            #comes from the imdb title so this is the best and final check.
            #Check if we already have this movie in the database


            # Allow some fuzz. Some of my collection has the year off by one or two compared to imdb
            # Should prevent the issue I was having with weird same titles from decades later or earlier
            # Sometimes the wrong results are still only a year difference. Just hope the first result is ours. :/
            if ("kind" in result.data and result.data["kind"] != "movie") or \
                    result.movieID is None:
                continue
            result.extradata = ia.get_movie(result.movieID).data
            if "title" not in result.extradata:
                continue
            if self.checkexistsfunc(result.extradata["title"]):
                #self.progressUpdate.emit("Skipping2 %s, already in database" % result.extradata["title"])
                continue
            if "rating" not in result.extradata:
                result.extradata["rating"] = 0
            if "runtimes" not in result.extradata:
                #print("NOTHERE")
                result.extradata["runtimes"] = [0]
            if "year" not in result.extradata:
                if "startYear" in result.data:
                    result.extradata["year"] = result.data["startYear"]
                else:
                    result.extradata["year"] = 0
            if isinstance(result.extradata["year"], str):
                try:
                    result.extradata["year"] = int(result.extradata["year"][:4])
                except:
                    result.extradata["year"] = 0
            if abs(int(result.extradata["year"]) - int(movieyear)) > 1:
                #print("YEARSKIP")
                continue
            else:
                outlist.append(result)
        return sorted(outlist, key=lambda m: m.extradata["rating"], reverse=True)

    def getInfo(self):
        ib = imdb.IMDb() # Online check
        ia = imdb.IMDb("s3", "sqlite:///%s" % S3DATASET_LOCATION)
        #self.filedata[tld] = [ [filename, foldername], ...]
        for tld, files in self.filedata.items():
            self.progressUpdate.emit("Checking TLD: %s" % tld)
            if self.stopping: return

            for finfo in files:
                if self.stopping: return

                #Indicate we are checking another file by updating the progress bar
                self.processingFile.emit()

                fname = finfo[0]
                fpath = finfo[1]
                try:
                    fname2 = re.split(os.sep+os.sep, fpath)[-1] #Get directory name. Needs escaped separator so thats why os.sep+os.sep
                except:
                    fname2 = ""
                freg = movie_title_regex.search(fname)
                freg2 = movie_title_regex.search(fname2)
                #TODO PROPERLY FIXME This is such a bodge
                if freg is None:
                    freg = movie_title_regex_noyear.search(fname)
                if freg2 is None:
                    freg2 = movie_title_regex_noyear.search(fname2)
                movietitle = freg.group(1).replace(".", " ") # Periods mess things up
                if freg2: movietitle2 = freg2.group(1).replace(".", " ") # Periods mess things up
                else: movietitle2 = ""
                movietitle = movietitle.strip()
                movietitle2 = movietitle2.strip()
                for kw in REMOVE_KEYWORDS:
                    movietitle = re.sub(kw, "", movietitle, flags=re.IGNORECASE)
                    if freg2: movietitle2 = re.sub(kw, "", movietitle2, flags=re.IGNORECASE)

                if freg is not None and freg.group(2) is not None:
                    movieyear = freg.group(2)
                elif freg2 is not None and freg2.group(2) is not None:
                    movieyear = freg2.group(2)
                else:
                    movieyear = 0

                #Check if we already have this movie in the database
                if self.checkexistsfunc(movietitle) or (freg2 is not None and self.checkexistsfunc(movietitle2)):
                    self.progressUpdate.emit("Skipping %s, already in database" % movietitle)
                    continue
                #self.progressUpdate.emit("Searching IMDb for '%s %s'" % (movietitle, movieyear))
                #searchdata = ia.search_movie("%s %s" % (movietitle, movieyear))
                self.progressUpdate.emit("Searching IMDb for '%s'" % movietitle)
                searchdata = self.filterImdbResults(ia, ia.search_movie("%s" % movietitle, results=1000), movieyear) # Limit the number of results to 1000
                #searchdata = []
                #sleep(3)
                if len(searchdata) == 0:
                    continue
                #Try and find the one that has a matching year, best we can do to be sure
                for result in searchdata:
                    if self.stopping: return

                    self.progressUpdate.emit("Found IMDb ID for %s:  %s" % (movietitle, result.movieID))
                    movie_data = result.extradata
                    #Do some basic checks to make sure this is the correct release
                    #Check if the name is close, if not dont even bother
                    #Some titles are being filtered because the file name doesnt include the subtitle which is in the imdb data
                    #an example is the file title The.Naked.Gun.1988.1080p.BluRay.X264
                    #but the full title should be The Naked Gun: From the Files of Police Squad!
                    #
                    #Some titles in the IMDb have unicode characters that aren't
                    #suitable for file names so we need to convert those to ascii
                    #Trying both titles in case the folder name is more accurate
                    if SequenceMatcher(None, movietitle.lower(), unicodedata.normalize('NFKD', movie_data["title"].lower())).ratio() < MASTER_RATIO and \
                       SequenceMatcher(None, movietitle2.lower(), unicodedata.normalize('NFKD', movie_data["title"].lower())).ratio() < MASTER_RATIO:
                        #print("SMatcher SKIP %s   %s  -  %s" % (SequenceMatcher(None, movietitle.lower(), movie_data["title"].lower()).ratio(), movietitle.lower(), movie_data["title"].lower()))
                        continue
                    if "director" not in movie_data:
                        continue
                    if "writer" not in movie_data:
                        continue
                    if "cast" not in movie_data:
                        continue
                    #Discard anything less than an hour long.
                    try:
                        movie_data["runtimes"][0] = int(movie_data["runtimes"][0])
                    except:
                        print("RUNTIMES PROB: %s" % movie_data["runtimes"][0])
                    if movie_data["runtimes"][0] < 65:
                        self.progressUpdate.emit("Too short a runtime, skipping id %s" % result.movieID)
                        continue
                    #Now that we're sure, lets pull the data from imdb online. The S3 dataset has lots of problems.
                    movie_data = ib.get_movie(result.movieID).data
                    if "director" not in movie_data:
                        continue
                    if "writer" not in movie_data:
                        continue
                    if "cast" not in movie_data:
                        continue
                    if "year" not in movie_data:
                        continue
                    #Build up our dictionary to emit
                    #IMDB is so annoying with their inconsistent key names.
                    #sometimes its a plural word, sometimes its not. Sometimes its under a completely different name entirely.
                    #Movies with multiple writers still only have one key: writer
                    #on the other hand, producers is always plural even if theres only one.
                    #Now I'm left wondering if there is some movie out there where director has an s at the end
                    #or producers doesn't.
                    dbdata = OD()
                    dbdata["title"] = movie_data["title"]
                    if "director" in movie_data:
                        dbdata["directors"] = str(get_person_names(movie_data["director"]))
                    elif "directors" in movie_data:
                        dbdata["directors"] = str(get_person_names(movie_data["directors"]))
                    else:
                        dbdata["directors"] = "NO_DIRECTOR_FOUND"
                    if "writer" in movie_data:
                        dbdata["writers"] = str(get_person_names(movie_data["writer"]))
                    elif "writers" in movie_data:
                        dbdata["writers"] = str(get_person_names(movie_data["writers"]))
                    else:
                        dbdata["writers"] = "NO_WRITER_FOUND"
                    dbdata["producers"] = str(get_person_names(movie_data["producers"])) if "producers" in movie_data else "NO_PRODUCER_FOUND"

                    #Just to check, I dont want to add if they arent needed but I have no idea
                    if "producer" in movie_data:
                        print("---PRODUCER---  %s" % dbdata["title"])
                    if "composer" in movie_data:
                        print("---COMPOSER---  %s" % dbdata["title"])

                    #Should always have a cast. If we dont this is probably the wrong entry

                    dbdata["actors"] = str(get_person_names(movie_data["cast"]))
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
                    dbdata["imdb_id"] = result.movieID
                    dbdata["imdb_rating"] = movie_data["rating"] if "rating" in movie_data else -1
                    dbdata["rating"] = 0
                    dbdata["year"] = movie_data["year"]
                    dbdata["extra1"] = ""
                    dbdata["extra2"] = ""
                    self.progressUpdate.emit("Found good IMDb data for %s with id %s" % (fname, result.movieID))
                    self.newTitleData.emit(dbdata)
                    break
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
        files = []
        for f in allfiles:
            if self.stopping is True: return None

            #Enabling this one and the "Found video file" emit() causes crashes because they can sometimes emit too close together.
            #self.progressUpdate.emit("Checking if file is a video:  %s" % f)
            if os.path.isfile(os.path.join(directory, f)) is True and is_video_file(f) is True and is_movie_file(f) is True:
                self.progressUpdate.emit("Found a movie video file:  %s" % f)
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
        self.imdbsuccessfuladd = -1
        self.filelist = {}
        self.addedvideos = []
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
        #self.progressbar.cancelButton.clicked.connect(self.stopScan)
        self.progressbar.closableDialogClosing.connect(self.stopScan)
        if len(self.scansettings["library"]) > 1:
            pmax = len(self.scansettings["library"])
        else:
            pmax = 0
        self.progressbar.progressBar.setMaximum(pmax)
        self.progressbar.progressBar.setMinimum(0)
        self.progressbar.progressBar.setValue(0)
        self.progressbar.progressLabel.setText("Found 0 Media Files")
        self.progressbar.show()
        self.spawnCrawlerThreads()

    def spawnCrawlerThreads(self):
        # Keep going until all folders have been scanned and all threads have joined or a stop is called
        while len(self.activecrawlerthreads) < int(self.scansettings["threads"]) and len(self.folderstoscan) > 0 and self.stopping is False:
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
        #print(s)
        self.progressbar.updateDetailsText(s)

    def getProgressBarFilecount(self):
        oldlabel = str(self.progressbar.progressLabel.text())
        oldcount = int(re.search("%\]\s+(-?[0-9]{1,10})\s+", oldlabel).group(1))
        return oldcount

    def updateImdbProgressBar(self):
        oldcount = self.getProgressBarFilecount()
        newcount = oldcount + 1
        perc = newcount/self.filecount * 100
        progresslabel = "[%d%%] %s files processed - %s titles added to database... " % (perc, newcount, self.imdbsuccessfuladd)
        self.progressbar.progressBar.setValue(newcount)
        self.progressbar.progressLabel.setText(progresslabel)


    def totalFileCountUpdate(self, filecount):
        #User to track total files
        self.filecount += filecount
        self.progressbar.progressLabel.setText("Found %s Media Files..." % self.filecount)

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

    def newFileCallback(self, filedata):
        #filedata[files] = [ (filename: fulldirpath), ...]
        tld = filedata["directory"]
        if tld not in self.filelist:
            self.filelist[tld] = []
        self.filelist[tld] += filedata["files"]
        self.totalFileCountUpdate(len(filedata["files"]))

    def startImdbInfoGrab(self):
        if self.imdbworker is not None:
            self.imdbThreadFinishedCallback()
        self.imdbsuccessfuladd = 0
        self.addedvideos = []
        #Create our worker and qthread
        ithread = QThread()
        self.imdbworker = imdbInfoGrabber(self.filelist, ithread, self.libref.checkForTitle)
        # !! IMPORTANT NOTE!
        # This one got me good. For some reason this imdb thread kept blocking the main GUI thread and I couldnt figure it out.
        # I tried having a background loop that runs processEvents() but that was stopped too!
        # Turns out, if you make connections before you moveToThread(), those connections get run in the current context, i.e.
        # the main GUI thread. So if you swap the order and moveToThread() BEFORE making connections, those connections run
        # in the QThread's context. Super easy mistake and not a lot of way to diagnose the issue.
        self.imdbworker.moveToThread(ithread)
        ithread.started.connect(self.imdbworker.getInfo)
        self.imdbworker.newTitleData.connect(self.imdbThreadUpdateCallback)
        self.imdbworker.workFinished.connect(self.imdbThreadFinishedCallback)
        self.imdbworker.progressUpdate.connect(self.updateProgressbarDetails)
        self.imdbworker.processingFile.connect(self.updateImdbProgressBar)
        #ithread.finished.connect(self.imdbThreadFinishedCallback)
        ithread.start()
        #self.updateDisplayRequested.emit()
        #Set up the progress bar for the next step
        self.progressbar.progressBar.setMaximum(self.filecount)
        self.progressbar.progressBar.setValue(0)
        self.progressbar.setWindowTitle("Retrieving IMDB information for found titles...")
        progresslabel = "[%d%%] %s files processed - %s titles added to database... " % (0, 0, 0)
        self.progressbar.progressLabel.setText(progresslabel)


    def imdbThreadUpdateCallback(self, dbdata):
        self.libref.addMovie(dbdata)
        self.addedvideos.append(dbdata["title"])
        #print("UPDATECALL %s " % self.imdbsuccessfuladd)
        self.imdbsuccessfuladd += 1

    def imdbThreadFinishedCallback(self):
        self.imdbworker.stopping = True
        self.imdbworker.ithread.quit()
        self.imdbworker.ithread.wait()
        self.imdbworker = None
        #change the cancel button to close since we are finished now
        finalmessage = "Finished scanning library and updating IMDb information. Added %s titles to the database." % self.imdbsuccessfuladd
        self.progressbar.setFinished(finalmessage)
        count = self.getProgressBarFilecount()
        progresslabel = "[%d%%] %s files processed - %s titles added to database... " % (100, count, self.imdbsuccessfuladd)
        self.progressbar.progressBar.setValue(self.progressbar.progressBar.maximum())
        self.progressbar.progressLabel.setText(progresslabel)
        for m in self.addedvideos:
            self.updateProgressbarDetails(m)


    def stopScan(self):
        #print("STOPCALL")
        self.stopping = True
        for c in self.activecrawlerthreads:
            c.stopt()
        if self.imdbworker is not None:
            self.imdbworker.stopt()
        self.progressbar.close()
        self.updateDisplayRequested.emit()

