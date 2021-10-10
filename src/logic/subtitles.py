#All the subtitle related code here

import subliminal, babelfish
from .movie_library import checkDbOpen, getDbCursor
from dialogs.widgets.generic_progress_bar import genericProgressDialog

import os, sqlite3

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


class SubtitleDownloader:
    def __init__(self, libraryref):
        self.libraryref = libraryref
        subliminal.region.configure("dogpile.cache.memory")

    def updateCache(self):
        print("YEAH NO")