#All the subtitle related code here
import json
from subprocess import check_output
from base64 import urlsafe_b64encode
from time import sleep
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QVariant
from .movie_library import checkDbOpen, getDbCursor
from dialogs.widgets.generic_progress_bar import genericProgressDialog

import os, sqlite3

SUBLANG = "eng"
DATABASE_PATH = "./subtitles.db"

class SubtitleLibrary:
    def __init__(self, DBPATH=DATABASE_PATH):
        self.dbmutex = False
        self.subsdict = {}
        self.dbpath = DBPATH
        self.checkForSubtitleDb()


    @checkDbOpen
    def checkForSubtitleDb(self):
        #Now see if we have a database file and if not create a new one
        if os.access(self.dbpath, os.W_OK):
            with getDbCursor(self.dbpath, self.dbmutex) as dbcursor:
                try:
                    table_list = dbcursor.execute("SELECT name FROM sqlite_master where type='table' ORDER BY name").fetchone()
                except sqlite3.DatabaseError:
                    return False
            #Make sure this is our database
            if table_list is None or table_list[0] != "subtitle_data":
                return False

        else:
            # No database file exists so we are going to create it.
            with getDbCursor(self.dbpath, self.dbmutex, 'w') as dbcursor:
                #Lyrics table
                dbcursor.execute("CREATE TABLE subtitle_data ("
                                 "title TEXT NOT NULL PRIMARY KEY,"
                                 "filename TEXT,"
                                 "filelocation TEXT,"
                                 "subtitles TEXT,"
                                 "extra1 TEXT"
                                 ")")
            print("Created new subtitle database file at: \n%s." % self.dbpath)
            return True

    @checkDbOpen
    def checkForSubs(self, movietitle):
        if len(movietitle) == 0 or not isinstance(movietitle, str): return False
        with getDbCursor(self.dbpath, self.dbmutex) as dbcursor:
            data = dbcursor.execute("SELECT COUNT(1) FROM subtitle_data WHERE title=?", (movietitle,)).fetchone()
        return bool(data[0])

    @checkDbOpen
    def delSubs(self, movietitle):
        if self.checkForSubs(movietitle):
            with getDbCursor(self.dbpath, self.dbmutex, "w") as dbcursor:
                dbcursor.execute("DELETE FROM subtitle_data WHERE title=?", (movietitle,))
            del(self.subsdict[movietitle])

    @checkDbOpen
    def addSubs(self, subsdata):
        if not self.checkForSubs(subsdata["title"]):
            with getDbCursor(self.dbpath, self.dbmutex, "w") as dbcursor:
                dbcursor.execute("INSERT INTO subtitle_data VALUES (?,?,?,?,?)",
                                 (subsdata["title"],
                                  subsdata["filename"],
                                  subsdata["filelocation"],
                                  subsdata["subtitles"],
                                  subsdata["extra1"])
                                 )
            self.subsdict[subsdata["title"]] = subsdata

class SubtitleExtractor(QObject):
    newSubtitles = pyqtSignal(QVariant)
    threadFinished = pyqtSignal(QVariant)

    def __init__(self, moviedata, parent=None):
        super(SubtitleExtractor, self).__init__(parent)
        self.moviedata = moviedata

    def getSubs(self):
        if "substmp" not in os.listdir():
            os.mkdir("substmp")
            print("Created substmp folder")
        #Get track id, extract track to file, read file data into dict, emit data
        vidpath = self.moviedata["filelocation"].replace(r"\\", r"\\") + "\\" + self.moviedata["filename"].replace(r"\\", r"\\")
        try:
            trackid = self.getSubtitleTrackIds(vidpath)
        except Exception as e:
            print("ERROR GETTING TRACKID %s" % self.moviedata["title"])
            print(e)
            return
        if len(trackid) == 0: #Didnt find subs
            self.threadFinished.emit(self)
            return
        trackid = trackid[0]
        try:
            rawsubs = self.extractSubtitlesFromVideo(vidpath, trackid, self.moviedata["title"])
        except Exception as e:
            print("ERROR EXTRACTING SUBS: %s" % self.moviedata["title"])
            print(e)
            return
        #Emitdata is just the data we need for addSubs()
        emitdata = {}
        emitdata["title"] = self.moviedata["title"]
        emitdata["filename"] = self.moviedata["filename"]
        emitdata["filelocation"] = self.moviedata["filelocation"]
        emitdata["subtitles"] = rawsubs
        emitdata["extra1"] = ""
        self.newSubtitles.emit(emitdata)
        self.threadFinished.emit(self)

    def getSubtitleTrackIds(self, vidpath):
        #Using mkvmerge's json output we can look for the exact track we want and then extract it
        cmd = "mkvmerge --identification-format json --identify \"%s\"" % vidpath
        videodata = json.loads(check_output(cmd, shell=True))
        goodsubids = [s["id"] for s in videodata["tracks"] if s["type"] == "subtitles" and \
                      s["properties"]["language"] == SUBLANG and \
                      s["properties"]["forced_track"] is False and \
                      "S_TEXT" in s["properties"]["codec_id"] and \
                      ("SDH" not in s["properties"]["track_name"].upper() if "track_name" in s["properties"] else True)] # Would prefer not to use SDH subs but maybe I can filter out actions
        #At this point its hoped that there is only one track
        #If theres more we'll investigate later
        if len(goodsubids) > 1:
            print("Got more than 1 good track for %s" % vidpath)
        return goodsubids


    #It seems that practically speaking you have to read the entire file to
    #extract any given subtitle track. So don't run this over slow network paths.
    def extractSubtitlesFromVideo(self, vidpath, trackid, movietitle):
        subsfilename = "./substmp/%s.txt" % urlsafe_b64encode(movietitle.encode("utf-8")).decode("utf-8")
        cmd = "mkvextract tracks %s %s:%s" % (vidpath, trackid, subsfilename)
        check_output(cmd, shell=True)
        print(vidpath)
        print(trackid)
        print(movietitle)
        with open(subsfilename, "r") as subsfile:
            subtitles = subsfile.read()
        os.remove(subsfilename)
        return subtitles

#Ignoring our setting for now, just for testing
MAX_THREADS = 5
SLEEP_TIME = 2

class SubtitleDownloader(QObject):
    def __init__(self, movieslib, subdbref, parent=None):
        super(SubtitleDownloader, self).__init__(parent)
        self.subdbref = subdbref
        self.movieslib = movieslib
        self.threadlist = []
        self.stopping = False

    def threadFinishedCallback(self, thread):
        self.threadlist.remove(thread)
        self.progressbar.progressBar.setValue(self.progressbar.progressBar.value()+1)

    def stopUpdate(self):
        print("UHHHHHHH")
        self.stopping = True

    def updateSubsCache(self):
        #Spin up our progress bar, go through library and spin off threads for extract operations
        #Create our progress bar
        self.progressbar = genericProgressDialog()
        #self.progressbar.cancelButton.clicked.connect(self.stopScan)
        self.progressbar.closableDialogClosing.connect(self.stopUpdate)
        self.progressbar.progressBar.setMaximum(len(self.movieslib))
        self.progressbar.progressBar.setMinimum(0)
        self.progressbar.progressBar.setValue(0)
        self.progressbar.progressLabel.setText("Extracted 0 subtitles")
        self.progressbar.show()
        #keep track of what titles we've spun off
        for title, mdata in self.movieslib.items():
            print(title)
            if self.stopping is True:
                return

            if self.subdbref.checkForSubs(title):
                #update the progressbar
                self.progressbar.progressBar.setValue(self.progressbar.progressBar.value()+1)
                continue

            #Wait for a thread to finish if needed
            if len(self.threadlist) == MAX_THREADS:
                while self.threadlist == MAX_THREADS:
                    sleep(SLEEP_TIME) # check every SLEEP_TIME seconds

            #xtr = SubtitleExtractor(mdata)
            #xtr.getSubs()

            #Spin up new thread

            newthread = QThread()
            newthread.setTerminationEnabled(True)
            xtr = SubtitleExtractor(mdata)
            xtr.threadref = newthread
            xtr.moveToThread(newthread)
            newthread.started.connect(xtr.getSubs)
            xtr.newSubtitles.connect(self.subdbref.addSubs)
            xtr.threadFinished.connect(self.threadFinishedCallback)
            newthread.start()
            updatemsg = "Created new extraction thread for movie %s" % title
            print(updatemsg)
            self.progressbar.updateDetailsText(updatemsg)
            self.threadlist.append(xtr)





    #In addition to time codes there are many subtitles are are representative of actions and not dialog.
    #This function aims to remove actions and possibly ascribe dialog to individual characters.
    #Some subtitles seem to contain information about the speaker but this may not be universal.
    #For now just returning dialog alone is sufficient for our needs.
    def filterDialogFromSubs(self, subtitles):
        pass
