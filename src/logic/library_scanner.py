# Very basic multithreaded crawler that will crawl each drive on a separate thread.
# If you are using SSD's you could probably get away with multiple crawlers per drive
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QVariant
from collections import OrderedDict as OD
from dialogs.widgets.generic_progress_bar import genericProgressDialog
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

class imdbInfoGrabber(QObject):
    newTitleData = pyqtSignal(dict)
    workFinished = pyqtSignal()

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
        while p < 120:
            if self.stopping:
                return
            sleep(0.25)
            QApplication.processEvents()
            p += 1

        for tld, files in self.filedata.items():
            if self.stopping:
                return
            self.newTitleData.emit(files[0])
        self.workFinished.emit()



#Job of the Crawler is just to discover filenames and nothing more
#We will get IMDB info using a separate process
class Crawler(QObject):
    foundNewFiles = pyqtSignal(dict)
    workFinished = pyqtSignal(QVariant)

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
            if os.path.isdir(os.path.join(directory, d)) is True and not re.search("s[0-9]{2}", d, re.IGNORECASE):
                dirs.append(d)
        #Remove excluded dirs
        for d in dirs:
            if self.stopping is True: return None
            for x in IGNORE_FOLDERS:
                if self.stopping is True: return None

                if re.search(x, d, re.IGNORECASE):
                    dirs.remove(d)
                    print("REMOVED: %s" % d)

        # Now that we're down to the bottom of the dir chain, we work our way back through the files
        #files = [f for f in allfiles if os.path.isfile(os.path.join(directory, f)) is True]
        #files = [f for f in allfiles if os.path.isfile(os.path.join(directory, f)) is True and is_video_file(f) is True]
        #files = {f:directory for f in allfiles if os.path.isfile(os.path.join(directory, f)) is True and is_video_file(f) is True}
        files = {}
        for f in allfiles:
            if self.stopping is True: return None
            if os.path.isfile(os.path.join(directory, f)) is True and is_video_file(f) is True:
                files[f] = directory
        # Send out the files we found here
        if len(files) > 0:
            self.foundNewFiles.emit({"files": files, "directory": self.startpath})

        # find more files
        for d in dirs:
            if self.stopping is True: return None
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
        self.progressbar.setModal(True)
        self.progressbar.setWindowTitle("Discovering files...")
        self.progressbar.cancelButton.clicked.connect(self.stopScan)
        self.progressbar.progressBar.setMaximum(len(self.scansettings["library"]))
        self.progressbar.progressBar.setMinimum(0)
        self.progressbar.progressBar.setValue(0)
        self.progressbar.progressLabel.setText("Found 0 Media Files")
        self.progressbar.show()
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
            newthread.start()
            print("New thread %s" % folder)
            self.activecrawlerthreads.append(c)

    def updateImdbThreadProgress(self):
        oldlabel = str(self.progressbar.progressLabel.text())
        print("O: %s" % oldlabel)
        nextidx = float(oldlabel[1:oldlabel.index("%")]) + 1
        perc = float(nextidx)/float(self.filecount) * 100
        progresslabel = "[%.1f%%] %s titles added to database... " % (perc, nextidx)
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
        #filedata[files] = {filename: fulldirpath}
        tld = filedata["directory"]
        if tld not in self.filelist:
            self.filelist[tld] = []
        self.filelist[tld].append(filedata["files"])
        self.totalFileCountUpdate(len(filedata["files"]))
        #Just update count
        pass
        """
        #Add to database, For now we won't worry about the other data.
        dbdata = OD()
        dbdata["title"] = filedata["filename"]
        dbdata["director"] = ""
        dbdata["writer"] = ""
        dbdata["producer"] = ""
        dbdata["genre"] = ""
        dbdata["playcount"] = 1
        dbdata["lastplay"] = ""
        dbdata["filelocation"] = filedata["directory"]
        dbdata["imdb_id"] = ""
        dbdata["rating"] = 0
        dbdata["extra1"] = ""
        dbdata["extra2"] = ""
        self.libref.addMovie(dbdata)
        self.updateImdbThreadProgress()
        #print("Added %s to the database" % filedata)
        """

    def startImdbInfoGrab(self):
        if self.imdbworker is not None:
            self.imdbThreadFinishedCallback()
        #Create our worker and qthread
        ithread = QThread()
        self.imdbworker = imdbInfoGrabber(self.filelist, ithread)
        ithread.started.connect(self.imdbworker.getInfo)
        self.imdbworker.newTitleData.connect(self.imdbThreadUpdateCallback)
        self.imdbworker.workFinished.connect(self.imdbThreadFinishedCallback)
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

    def imdbThreadUpdateCallback(self, newfiledata):
        print("imdbThreadUpdateCallback")
        print(type(newfiledata))
        print(len(newfiledata))
        #print(newfiledata.keys())
        #print(newfiledata.values())
        #self.updateImdbThreadProgress()

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
