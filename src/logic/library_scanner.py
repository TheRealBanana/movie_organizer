# Very basic multithreaded crawler that will crawl each drive on a separate thread.
# If you are using SSD's you could probably get away with multiple crawlers per drive
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QVariant
from collections import OrderedDict as OD
import re
import os
import os.path

IGNORE_FOLDERS = [""]

VIDEO_EXTENSIONS=["avi", "divx", "amv", "mpg", "mpeg", "mpe", "m1v", "m2v",
                  "mpv2", "mp2v", "m2p", "vob", "evo", "mod", "ts", "m2ts",
                  "m2t", "mts", "pva", "tp", "tpr", "mp4", "m4v", "mp4v",
                  "mpv4", "hdmov", "mov", "3gp", "3gpp", "3g2", "3gp2",
                  "mkv", "webm", "ogm", "ogv", "flv", "f4v", "wmv", "rmvb",
                  "rm", "dv"]

class Crawler(QObject):
    foundNewFile = pyqtSignal(dict)
    progressUpdate = pyqtSignal(float)
    workFinished = pyqtSignal(QVariant)

    def __init__(self, startpath, searchparams, thread, parent=None):
        super(Crawler, self).__init__(parent)
        self.thread = thread
        self.startpath = startpath
        self.searchparams = searchparams
        self.stopthread = False

    def crawl(self, dir):
        allfiles = os.listdir(dir)
        #dirs = [d for d in allfiles if os.path.isdir(os.path.join(dir, d)) is True]
        dirs = [d for d in allfiles if os.path.isdir(os.path.join(dir, d)) is True and
                not re.search("s[0-9]{2}", d, re.IGNORECASE)] #No TV shows dammit
        #Remove excluded dirs
        for d in dirs:
            for x in IGNORE_FOLDERS:
                if re.search(x, d, re.IGNORECASE):
                    dirs.remove(d)
                    print("REMOVED: %s" % d)
        # Scan the dirs first, then the files
        for d in dirs:
            self.crawl(os.path.join(dir, d))
        #Now that we're down to the bottom of the dir chain, we work our way back through the files
        #files = [f for f in allfiles if os.path.isfile(os.path.join(dir, f)) is True]
        files = [f for f in allfiles if os.path.isfile(os.path.join(dir, f)) is True and
                 re.match("^.*?\.[a-z0-9]{1,6}$", f, re.IGNORECASE) and # Does it have an extension?
                 re.match("^.*?\.([a-z0-9]{1,6})$", f, re.IGNORECASE).group(1) in VIDEO_EXTENSIONS and # Is it a video extension?
                 not re.match("(^.*?sample\.([a-z0-9]{1,6})$|^sample.*$)", f, re.IGNORECASE) and # And its not a sample video?
                 not re.search("(((s|e)[0-9]{1,2}){2}|[0-9]{1,2}x[0-9]{1,2})", f, re.IGNORECASE)] # And we're pretty sure its not a TV show

        for f in files:
            self.foundNewFile.emit({"filename": f, "dir": dir})

    def doWork(self):
#        for x in range(10):
#            self.progressUpdate.emit(float(x))
#            if self.stopthread: break
#            sleep(0.2)
        self.crawl(os.path.realpath(self.startpath))
        print("DONE WITH THREADED STUFFS")
        self.workFinished.emit(self)
        return


class LibraryScanner(QObject):
    updateDisplayRequested = pyqtSignal()

    def __init__(self, libraryref, scansettings):
        super(LibraryScanner, self).__init__()
        self.stopping = False
        self.libref = libraryref
        self.scansettings = scansettings
        self.activethreads = []
        self.folderstoscan = scansettings["library"].copy()

    def startScan(self):
        #Spin off a crawl processes for each folder
        print("SCAN START")
        print("Max threads: %d" % int(self.scansettings["threads"]))
        print("Top level directories we are scanning:")
        for d in self.scansettings["library"]:
            print(d)
        print("-----------")
        self.stopping = False
        self.spawnThreads()

    def spawnThreads(self):
        # Keep going until all folders have been scanned and all threads have joined
        while len(self.activethreads) < int(self.scansettings["threads"]) and len(self.folderstoscan) > 0:
            newthread = QThread()
            newthread.setTerminationEnabled(True) # Can't find documentation on what the default is or how to check what its currently set to.
            folder = self.folderstoscan.pop(-1)
            c = Crawler(folder, searchparams=None, thread=newthread)
            c.moveToThread(newthread)
            newthread.started.connect(c.doWork)
            c.workFinished.connect(self.workFinishedCallback)
            c.foundNewFile.connect(self.newFileCallback)
            #c.progressUpdate.connect(self.pu)
            newthread.start()
            print("New thread %s" % folder)
            self.activethreads.append(c)

    #def pu(self, p): print("Progress: %s" % str(p))

    def workFinishedCallback(self, c):
        #Terminate the thread and pop it from our thread list
        c.thread.terminate()
        c.thread.wait()
        self.activethreads.remove(c)
        if len(self.folderstoscan) > 0:
            self.spawnThreads()
        elif len(self.activethreads) == 0:
            self.updateDisplayRequested.emit()

    def newFileCallback(self, filedata):
        #Add to database, For now we won't worry about the other data.
        dbdata = OD()
        dbdata["title"] = filedata["filename"]
        dbdata["director"] = ""
        dbdata["writer"] = ""
        dbdata["producer"] = ""
        dbdata["genre"] = ""
        dbdata["playcount"] = 1
        dbdata["lastplay"] = ""
        dbdata["filelocation"] = filedata["dir"]
        dbdata["imdb_id"] = ""
        dbdata["rating"] = 0
        dbdata["extra1"] = ""
        dbdata["extra2"] = ""
        self.libref.addMovie(dbdata)
        #print("Added %s to the database" % filedata)

    def stopScan(self):
        self.stopping = True