#All the subtitle related code here
import json
import re
from subprocess import Popen, PIPE
from collections import OrderedDict
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
                #Subtitles table
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
            #SubStation Alpha format only separates sections by a newline and by standard we should have 3 sections
            subdata["subtitles"] = re.sub(r"\r", "", str(subdata["subtitles"]), flags=re.MULTILINE) # Fix line endings
            splitsubs = re.split(r"\n^$\n", str(subdata["subtitles"]), flags=re.MULTILINE)

            if len(splitsubs) == 3: #Probably SSA sub format
                subregex = r"Dialogue:\w*(?:[^,]*),([^,]*),([^,]*),(?:[^,]*),(?:[^,]*),(?:[^,]*),(?:[^,]*),(?:[^,]*),(?:[^,]*),(.*)"
                splitsubs = re.split(r"\n", splitsubs[2])
                ssa = True
            else:
                subregex = r"([0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3})\s*-->\s*([0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3})(.*)"
                ssa = False

            subcorpus = ""
            timecodes = OrderedDict() # key=index , val = timecode
            for line in splitsubs:
                if len(line.strip()) == 0:
                    continue

                tcmatch = re.search(subregex, line, flags=re.MULTILINE|re.DOTALL)
                if tcmatch is None:
                    #print("Found an invalid line in file %s. Is this a valid srt or ssa format?" % subdata["filename"])
                    continue
                timecode = tcmatch.group(1)
                dialog = tcmatch.group(3).strip()
                #Some srt files include html tags so we'll remove those as well.
                #I havent seen any complicated tags yet so for now a regex is fine.
                #Also handles SSA formatters e.g. {\i1}
                dialog = re.sub(r"[<{][\\\s\w/0-9]+?[>}]", "", dialog, flags=re.M)
                #SSA format needs to have the newlines fixed
                if ssa: dialog = re.sub(r"\\N", r"\n", dialog)
                #Also remove any newlines
                #TODO leaving in newlines makes the outlook look nicer and we can search over newlines using re anyway
                #Future searching shouldnt need this filter
                dialog = re.sub(r"\n", " ", dialog, flags=re.M)
                #Finally any punctuation that could also cause issues matching
                #This makes the matched quote look weird, it would be nice to preserve punctuation without it causing issues
                dialog = re.sub(r"[^\w\s]", "", dialog, flags=re.M)
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
        trackids = self.getSubtitleTrackIds(vidpath)
        if self.stopping: return
        if trackids is None or len(trackids) == 0: #Didnt find subs
            self.threadFinished.emit(self)
            #print("NOFINDSUBS")
            return
        rawsubs = None
        #Try all the track ids we got but reject any subs that are less than 4k characters.
        for tid in trackids:
            if self.stopping: return
            rawsubs = self.extractSubtitlesFromVideo(vidpath, tid, self.moviedata["title"])
            if rawsubs is not None and len(rawsubs) > 4000:
                break
            else:
                #print("TOOSHORT")
                continue
        #Did we actually get anything?
        if rawsubs is None or len(rawsubs) < 4000:
            #print("TOOSHORT THREADQUIT")
            self.threadFinished.emit(self)
            return
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
            if s["type"] == "subtitles" and s["properties"]["language"] == SUBLANG:
                if "forced_track" not in ["properties"] or s["properties"]["forced_track"] is False:
                    if "S_TEXT" in s["properties"]["codec_id"]: # S_TEXT alone will pick up both SRT and SSA sub formats
                        if "track_name" not in s["properties"]:
                            s["properties"]["track_name"] = ""
                        if "commentary" not in s["properties"]["track_name"].lower():
                            print(s["properties"]["track_name"])
                            goodsubids.append(s)

        #At this point its hoped that there is only one track
        #If theres more than one we'll try and take the largest one and hope for the best ¯\_(ツ)_/¯
        if len(goodsubids) > 1:
            print("Got more than 1 good track for %s" % vidpath)
        #Because we made sure each one had a title before, we can sort by the length of the title itself.
        #The hope is that a longer track name for any subtitle is because its describing something specific about the track
        #E.g. in The Legend of Ron Burgundy one of the subtitle tracks is titled "English subs for foreign dialogue (e.g. animals speaking)"
        goodsubids = sorted(goodsubids, key=lambda r: len(r["properties"]["track_name"]))
        return [s["id"] for s in goodsubids]


    #It seems that practically speaking you have to read the entire file to
    #extract any given subtitle track. So don't run this over slow network paths.
    def extractSubtitlesFromVideo(self, vidpath, trackid, movietitle):
        subsfilename = "./substmp/%s.txt" % urlsafe_b64encode(movietitle.encode("utf-8")).decode("utf-8")
        cmd = "mkvextract tracks \"%s\" %s:%s" % (vidpath, trackid, subsfilename)
        print(cmd)
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
        self.addedsubs = []
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
        self.addedsubs.append(subsdata["title"])
        self.progressbar.progressLabel.setText("Extracted %s subtitles" % len(self.addedsubs))

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
            if len(self.addedsubs) > 0:
                s += " Added the following subtitles to the database:\n"
                for t in self.addedsubs: s+= "\n%s" % t
            print(s)
            self.progressbar.setFinished(s)
            try:
                self.progressbar.closableDialogClosing.disconnect(self.stopUpdate)
                self.progressbar.closableDialogClosing.connect(self.progressbar.accept)
            except:
                pass

    def stopUpdate(self):
        endmsg = "Cancel called, killing subprocesses and waiting for threads to finish"
        print(endmsg)
        self.progressbar.updateDetailsText(endmsg)
        self.progressbar.closableDialogClosing.disconnect(self.stopUpdate)
        self.progressbar.closableDialogClosing.connect(self.progressbar.accept)
        self.stopping = True
        for t in self.threadlist.values():
            t.stopping = True
            _ = Popen("taskkill /F /T /PID %s" % t.cmd.pid, stdout=PIPE)
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
        self.addedsubs = []
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
        #print(updatemsg)
        self.progressbar.updateDetailsText(updatemsg)
        newthread.start()
