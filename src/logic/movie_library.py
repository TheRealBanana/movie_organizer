import sqlite3
import os
import os.path
from collections import OrderedDict as OD

DATABASE_PATH = "./movielibrary.db"

#helper objects
def checkDbOpen(func):
    def dec(*args, **kwargs):
        if args[0].dbmutex is True:
            return False
        else:
            return func(*args, **kwargs)
    return dec

def checktype(obj):
    if not isinstance(obj, OD):
        raise(Exception("addMovie: Encountered wrong dictionary type, expected OrderedDict."))

class getDbCursor(object):
    def __init__(self, dbpath, dbmutex, contype='r'):
        self.dbpath = dbpath
        self.dbmutex = dbmutex
        self.contype = contype
        self.dbhandle = None
        self.dbcursor = None
    def __enter__(self):
        self.dbmutex = True
        self.dbhandle = sqlite3.connect(self.dbpath)
        self.dbcursor = self.dbhandle.cursor()
        return self.dbcursor
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.contype == 'w':
            self.dbhandle.commit()
        self.dbhandle.close()
        self.dbmutex = False


class MovieLibrary:
    def __init__(self, DBPATH=DATABASE_PATH):
        self.dbmutex = False
        self.librarydict = None
        self.dbpath = DBPATH
        self.checkForLyricsDb()

    @checkDbOpen
    def checkForLyricsDb(self):
        #Now see if we have a database file and if not create a new one
        if os.access(self.dbpath, os.W_OK):
            with getDbCursor(self.dbpath, self.dbmutex) as dbcursor:
                try:
                    table_list = dbcursor.execute("SELECT name FROM sqlite_master where type='table' ORDER BY name").fetchone()
                except sqlite3.DatabaseError:
                    return False
            #Make sure this is our database
            if table_list is None or table_list[0] != "movie_data":
                return False
            else:
                return True

        else:
            # No database file exists so we are going to create it.
            with getDbCursor(self.dbpath, self.dbmutex, 'w') as dbcursor:
                #Lyrics table
                dbcursor.execute("CREATE TABLE movie_data ("
                                 "title TEXT NOT NULL PRIMARY KEY,"
                                 "director TEXT,"
                                 "writer TEXT,"
                                 "producer TEXT,"
                                 "genre TEXT,"
                                 "playcount INTEGER,"
                                 "lastplay TEXT,"
                                 "filelocation TEXT,"
                                 "imdb_id TEXT,"
                                 "rating INTEGER,"
                                 "extra1 TEXT,"
                                 "extra2 TEXT"
                                 ")")
            print("Created new movie database file at: \n%s." % self.dbpath)
            return True

    @checkDbOpen
    def addMovie(self, moviedata):
        if not self.checkForTitle(moviedata["title"]):
            with getDbCursor(self.dbpath, self.dbmutex) as dbcursor:
                # Using dict unpacking with an asterisk ONLY WORKS WITH ORDERED DICTS!
                # If you use a normal dictionary it will add the values in the incorrect order.
                # With normal dicts we have to specify each value separately (which is a lot of bleh code).
                checktype(moviedata)
                dbcursor.execute("INSERT INTO movie_data VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", *moviedata)
                self.librarydict[moviedata["title"]] = moviedata

    @checkDbOpen
    def delMovie(self, movietitle):
        if self.checkForTitle(movietitle):
            with getDbCursor(self.dbpath, self.dbmutex) as dbcursor:
                dbcursor.execute("DELETE FROM movie_data WHERE title=?", movietitle)
            del(self.librarydict[movietitle])

    @checkDbOpen
    def checkForTitle(self, movietitle):
        with getDbCursor(self.dbpath, self.dbmutex) as dbcursor:
            data = dbcursor.execute("SELECT COUNT(1) FROM movie_data WHERE title=?", movietitle).fetchone()
        return bool(data[0])


    def _SEARCH(self): pass #TODO

