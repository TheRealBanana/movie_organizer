#All the subtitle related code here
import json
from subprocess import check_output
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


#This probably should be threaded but Im lazy and just want it working
class SubtitleDownloader:
    def __init__(self, libraryref):
        self.libraryref = libraryref


    def updateCache(self):
        print("YEAH NO")

    def getSubsFromFile(self):
        # pymediainfo.MediaInfo.parse()
        # Go over our library and check for entries that don't have any subs in the subtitles db
        # Then use pymediainfo to check for subs and determine the correct one to pull

        pass

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
            print("God more than 1 good track for %s" % vidpath)
        return goodsubids


    #It seems that practically speaking you have to read the entire file to
    #extract any given subtitle track. So don't run this over slow network paths.
    def extractSubtitlesFromVideo(self, vidpath, trackid):
        cmd = "mkvextract tracks %s %s:subsout.txt" % (vidpath, trackid)
        os.system(cmd)
        with open("subsout.txt", "r") as subsfile:
            subtitles = subsfile.read()
        return subtitles


    #In addition to time codes there are many subtitles are are representative of actions and not dialog.
    #This function aims to remove actions and possibly ascribe dialog to individual characters.
    #Some subtitles seem to contain information about the speaker but this may not be universal.
    #For now just returning dialog alone is sufficient for our needs.
    def filterDialogFromSubs(self, subtitles):
        pass
