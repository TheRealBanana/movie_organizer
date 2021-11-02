#All the subtitle related code here
import json
import re
from subprocess import Popen, PIPE
import subprocess
from base64 import urlsafe_b64encode
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QVariant
from .movie_library import checkDbOpen, getDbCursor, fixDbData
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
        self.fieldlist = self.getFieldList()

    @checkDbOpen
    def getFieldList(self):
        with getDbCursor(self.dbpath, self.dbmutex) as dbcursor:
            data = dbcursor.execute("PRAGMA table_info(subtitle_data)").fetchall()
        fieldlist = []
        for c in data:
            fieldlist.append(c[1])
        return fieldlist


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
        if len(movietitle) == 0 or not isinstance(movietitle, str):
            return False
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

    #Simple search, just returning subdata for whatever movies are in movielist
    def search(self, movielist):
        if len(movielist) == 0: return
        #Subtitles are stored in their raw srt format so we can't use the SQL query to search for the
        #dialogstr with any actual reliability. Have to get all the subs first, then search.
        querystr = "SELECT * FROM subtitle_data WHERE title=\"%s\"" % movielist[0]
        for m in movielist[1:]:
            querystr += " OR title=\"%s\"" % m
        returndata = self._SEARCH(querystr)
        if len(returndata) == 0:
            print("No subtitles in the database for: \n%s" % ", ".join(movielist))
            return {}
        #Now we can convert the raw srt format into a single corpus we can search more easily.
        #We still want to be able to reference the timecode our dialog match came from so
        #as we build our corpus we will keep track of what index each timecode's dialog is
        #added at. Later we can reference the index of the dialog to find the timecode again.
        for subdata in returndata.values():
            #All the srt files I have seen so far delineate separate pieces of dialog by an empty line.
            splitsubs = re.split(r"\n^$\n", subdata["subtitles"], flags=re.MULTILINE)
            subcorpus = ""
            timecodes = {} # key=index , val = timecode
            for line in splitsubs:
                if len(line.strip()) == 0:
                    continue
                srtregex = r"([0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}\s*-->\s*[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3})(.*)"
                tcmatch = re.search(srtregex, line, flags=re.MULTILINE|re.DOTALL)
                if tcmatch is None:
                    print("Found an invalid line in file %s. Is this a valid srt format?" % subdata["filename"])
                    continue
                timecode = tcmatch.group(1)
                dialog = tcmatch.group(2).strip()
                #Some srt files include html tags so we'll remove those as well.
                #I havent seen any complicated tags yet so for now a regex is fine.
                dialog = re.sub(r"<[\s\w/]+?>", "", dialog, flags=re.M)
                #Also remove any newlines
                dialog = re.sub(r"\n", " ", dialog, flags=re.M)
                index = len(subcorpus)
                subcorpus += dialog + " "
                timecodes[index] = timecode
            subdata["subtitles"] = {"timecodes": timecodes, "corpus": subcorpus}
        return returndata

    @checkDbOpen
    def _SEARCH(self, querystr):
        with getDbCursor(self.dbpath, self.dbmutex) as dbcursor:
            return fixDbData(dbcursor.execute(querystr).fetchall(), self.fieldlist)



class SubtitleExtractor(QObject):
    newSubtitles = pyqtSignal(QVariant)
    threadFinished = pyqtSignal(QVariant)

    def __init__(self, moviedata, parent=None):
        super(SubtitleExtractor, self).__init__(parent)
        self.moviedata = moviedata
        self.cmd = None
        self.stopping = False

    def getSubs(self):
        if "substmp" not in os.listdir():
            os.mkdir("substmp")
        #Get track id, extract track to file, read file data into dict, emit data
        vidpath = self.moviedata["filelocation"].replace(r"\\", r"\\") + "\\" + self.moviedata["filename"].replace(r"\\", r"\\")
        trackid = self.getSubtitleTrackIds(vidpath)
        if self.stopping: return
        if trackid is None or len(trackid) == 0: #Didnt find subs
            self.threadFinished.emit(self)
            print("NOFINDSUBS")
            return
        trackid = trackid[0]
        rawsubs = self.extractSubtitlesFromVideo(vidpath, trackid, self.moviedata["title"])
        if self.stopping: return
        #Emitdata is just the data we need for addSubs()
        emitdata = {
            "title": self.moviedata["title"],
            "filename": self.moviedata["filename"],
            "filelocation": self.moviedata["filelocation"],
            "subtitles": rawsubs,
            "extra1": ""
        }
        self.newSubtitles.emit(emitdata)
        self.threadFinished.emit(self)

    def getSubtitleTrackIds(self, vidpath):
        #Using mkvmerge's json output we can look for the exact track we want and then extract it
        cmd = "mkvmerge --identification-format json --identify \"%s\"" % vidpath
        self.cmd = Popen(cmd, stdout=PIPE)
        rawout, errors = self.cmd.communicate()
        if self.stopping: return
        videodata = json.loads(rawout)
        goodsubids = []
        if "tracks" not in videodata: #Something bigly wrong
            return None
        for s in videodata["tracks"]:
            if "codec_id" not in s["properties"]:
                continue
            if s["type"] == "subtitles" and s["properties"]["language"] == SUBLANG and \
                    (s["properties"]["forced_track"] is False if "forced_track" in s["properties"] else True) and \
                    "S_TEXT" in s["properties"]["codec_id"] and ("SDH" not in s["properties"]["track_name"].upper() if "track_name" in s["properties"] else True):
                goodsubids.append(s["id"])

        #At this point its hoped that there is only one track
        #If theres more we'll investigate later
        if len(goodsubids) > 1:
            print("Got more than 1 good track for %s" % vidpath)
        return goodsubids


    #It seems that practically speaking you have to read the entire file to
    #extract any given subtitle track. So don't run this over slow network paths.
    def extractSubtitlesFromVideo(self, vidpath, trackid, movietitle):
        subsfilename = "./substmp/%s.txt" % urlsafe_b64encode(movietitle.encode("utf-8")).decode("utf-8")
        cmd = "mkvextract tracks \"%s\" %s:%s" % (vidpath, trackid, subsfilename)
        self.cmd = Popen(cmd, stdout=PIPE)
        out, err = self.cmd.communicate()
        if self.stopping: return
        with open(subsfilename, "r", encoding="utf8") as subsfile:
            subtitles = subsfile.read()
        os.remove(subsfilename)
        return subtitles

#Ignoring our setting for now, just for testing
MAX_THREADS = 2

class SubtitleDownloader(QObject):
    def __init__(self, movieslib, subdbref, parent=None):
        super(SubtitleDownloader, self).__init__(parent)
        self.subdbref = subdbref
        self.movieslib = movieslib
        self.threadlist = {}
        self.moviequeue = []
        self.addedsubs = 0
        self.stopping = False
        self.progressbar = None

    def goodSubsCallback(self, subsdata):
        #Ignore any sub callbacks if we are stopping as its probably incomplete
        if self.stopping is True:
            return
        self.subdbref.addSubs(subsdata)
        msg = "Got good subtitles for %s. Adding to database..." % subsdata["title"]
        self.progressbar.updateDetailsText(msg)
        print(msg)
        self.addedsubs += 1
        self.progressbar.progressLabel.setText("Extracted %s subtitles" % self.addedsubs)

    def threadFinishedCallback(self, thread):
        self.progressbar.updateDetailsText("Thread (%s) for %s has finished" % (hex(id(thread)), thread.moviedata["title"]))
        thread.threadref.quit()
        thread.threadref.wait()
        thread.threadref.deleteLater()
        del(self.threadlist[hex(id(thread))])
        self.progressbar.progressBar.setValue(self.progressbar.progressBar.value()+1)
        #Create a new thread if we have any left in the queue and we arent stopping
        if len(self.moviequeue) > 0 and self.stopping is False:
            self.createExtractionThread()
        else:
            s = "Movie queue is empty or stop called, done extracting."
            print(s)
            self.progressbar.setFinished(s)

    def stopUpdate(self):
        endmsg = "Cancel called, killing subprocesses and waiting for threads to finish"
        print(endmsg)
        self.progressbar.updateDetailsText(endmsg)
        self.progressbar.closableDialogClosing.disconnect(self.stopUpdate)
        self.progressbar.closableDialogClosing.connect(self.progressbar.accept)
        self.stopping = True
        for t in self.threadlist.values():
            t.stopping = True
            _ = subprocess.Popen("taskkill /F /T /PID %s" % t.cmd.pid, stdout=PIPE)
            t.threadref.quit()
        self.progressbar.setFinished()

    def updateSubsCache(self):
        #Spin up our progress bar, go through library and spin off threads for extract operations
        #Create our progress bar
        self.progressbar = genericProgressDialog()
        self.progressbar.closableDialogClosing.connect(self.stopUpdate)
        self.progressbar.progressBar.setMaximum(len(self.movieslib))
        self.progressbar.progressBar.setMinimum(0)
        self.progressbar.progressBar.setValue(0)
        self.progressbar.progressLabel.setText("Extracted 0 subtitles")
        self.progressbar.show()
        self.addedsubs = 0
        self.moviequeue = list(self.movieslib.keys()) # list of titles still needing extraction threads run on them
        # spun up MAX_THREADS number of threads to start
        for _ in range(MAX_THREADS):
            self.createExtractionThread()

    def createExtractionThread(self):
        if len(self.moviequeue) == 0:
            return
        title = self.moviequeue.pop(0)
        moviedata = self.movieslib[title]
        while self.subdbref.checkForSubs(title) is True: #Keep popping new titles until we get one we need to create a thread for
            #Just return if there's nothing left in the queue
            if len(self.moviequeue) == 0:
                return
            #update the progressbar
            self.progressbar.progressBar.setValue(self.progressbar.progressBar.value()+1)
            title = self.moviequeue.pop(0)
            moviedata = self.movieslib[title]

        newthread = QThread()
        newthread.setTerminationEnabled(True)
        xtr = SubtitleExtractor(moviedata)
        xtr.threadref = newthread
        xtr.moveToThread(newthread)
        newthread.started.connect(xtr.getSubs)
        xtr.newSubtitles.connect(self.goodSubsCallback)
        xtr.threadFinished.connect(self.threadFinishedCallback)
        self.threadlist[hex(id(xtr))] = xtr
        updatemsg = "Created new extraction thread (%s) for movie %s" % (hex(id(xtr)), title)
        print(updatemsg)
        self.progressbar.updateDetailsText(updatemsg)
        newthread.start()
        #xtr.getSubs()






    #In addition to time codes there are many subtitles are are representative of actions and not dialog.
    #This function aims to remove actions and possibly ascribe dialog to individual characters.
    #Some subtitles seem to contain information about the speaker but this may not be universal.
    #For now just returning dialog alone is sufficient for our needs.
    def filterDialogFromSubs(self, subtitles):
        pass