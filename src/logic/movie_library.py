import sqlite3
import os
import re
from collections import OrderedDict as OD
from ast import literal_eval

DATABASE_PATH = "./movielibrary.db"


def fixDbData(data, fieldlist):
    returndata = {}
    #Fix the data
    for d in data:
        newd = []
        for s in d:
            if isinstance(s, str) and len(s) > 0 and s[0] == "[":
                s = literal_eval(s)
            newd.append(s)
        returndata[d[0]] = OD(zip(fieldlist, newd))
    return returndata

#helper objects
# TODO We should update this to make use of the proper 'with threading.Lock():'
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


# TODO We should update this to make use of the proper 'with threading.Lock():
class getDbCursor(object):
    def __init__(self, dbpath, dbmutex, contype='r'):
        #We can either wait for it or just error out. Since I don't know if this will ever be called Its better to error.
        #At least then I know it happened.
        if dbmutex is True:
            #TODO Maybe we just wait for the mutex to become available and only raise an exception after a set time
            raise(Exception("Given database mutex is already in-use."))
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
        self.fieldlist = []
        self.checkForMoviesDb()

    @checkDbOpen
    def checkForMoviesDb(self):
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
                #set the list of columns and then return true
                self.fieldlist = self.getFieldList()
                return True

        else:
            # No database file exists so we are going to create it.
            with getDbCursor(self.dbpath, self.dbmutex, 'w') as dbcursor:
                #Lyrics table
                dbcursor.execute("CREATE TABLE movie_data ("
                                 "title TEXT NOT NULL PRIMARY KEY,"
                                 "directors TEXT,"
                                 "writers TEXT,"
                                 "producers TEXT,"
                                 "actors TEXT,"
                                 "composers TEXT,"
                                 "genres TEXT,"
                                 "runtime INTEGER,"
                                 "cover_url TEXT,"
                                 "playcount INTEGER,"
                                 "lastplay TEXT,"
                                 "filename TEXT,"
                                 "filelocation TEXT,"
                                 "imdb_id TEXT,"
                                 "imdb_rating TEXT,"
                                 "rating INTEGER,"
                                 "year INTEGER,"
                                 "extra1 TEXT,"
                                 "extra2 TEXT"
                                 ")")
            print("Created new movie database file at: \n%s." % self.dbpath)
            return True

    @checkDbOpen
    def addMovie(self, moviedata):
        if not self.checkForTitle(moviedata["title"]):
            with getDbCursor(self.dbpath, self.dbmutex, "w") as dbcursor:
                # Using dict unpacking with an asterisk ONLY WORKS WITH ORDERED DICTS!
                # If you use a normal dictionary it will add the values in the incorrect order.
                # With normal dicts we have to specify each value separately (which is a lot of bleh code).
                checktype(moviedata)
                #dbcursor.execute("INSERT INTO movie_data VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (*moviedata.values(),))
                dbcursor.execute("INSERT INTO movie_data VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                 (moviedata["title"],
                                  str(moviedata["directors"]),
                                  str(moviedata["writers"]),
                                  str(moviedata["producers"]),
                                  str(moviedata["actors"]),
                                  str(moviedata["composers"]),
                                  str(moviedata["genres"]),
                                  moviedata["runtime"],
                                  moviedata["coverurl"],
                                  moviedata["playcount"],
                                  moviedata["lastplay"],
                                  moviedata["filename"],
                                  moviedata["filelocation"],
                                  moviedata["imdb_id"],
                                  moviedata["imdb_rating"],
                                  moviedata["rating"],
                                  moviedata["year"],
                                  moviedata["extra1"],
                                  moviedata["extra2"]))

                self.librarydict[moviedata["title"]] = moviedata

    @checkDbOpen
    def delMovie(self, movietitle):
        if self.checkForTitle(movietitle):
            with getDbCursor(self.dbpath, self.dbmutex, "w") as dbcursor:
                dbcursor.execute("DELETE FROM movie_data WHERE title=?", (movietitle,))
            del(self.librarydict[movietitle])

    @checkDbOpen
    def checkForTitle(self, movietitle):
        if len(movietitle) == 0 or not isinstance(movietitle, str): return False
        with getDbCursor(self.dbpath, self.dbmutex) as dbcursor:
            data = dbcursor.execute("SELECT COUNT(1) FROM movie_data WHERE title=?", (movietitle,)).fetchone()
        return bool(data[0])

    @checkDbOpen
    def getFullDatabase(self):
        if self.librarydict is not None:
            return self.librarydict
        with getDbCursor(self.dbpath, self.dbmutex) as dbcursor:
            alldata = dbcursor.execute("SELECT * FROM movie_data").fetchall()
        returndata = fixDbData(alldata, self.fieldlist)
        self.librarydict = returndata
        return returndata

    @checkDbOpen
    def getGenreList(self):
        tmplist = []
        with getDbCursor(self.dbpath, self.dbmutex) as dbcursor:
            data = dbcursor.execute("SELECT genres FROM movie_data").fetchall()
            for d in data:
                #Just be sure we've got a list.
                if d[0] == "[":
                    tmplist.append(literal_eval(d))
        #Remove dupes. This works because dictionary keys must be unique
        tmplist = list(dict.fromkeys(tmplist))
        tmplist.sort()
        return tmplist

    @checkDbOpen
    def getFieldList(self):
        with getDbCursor(self.dbpath, self.dbmutex) as dbcursor:
            data = dbcursor.execute("PRAGMA table_info(movie_data)").fetchall()
        fieldlist = []
        for c in data:
            fieldlist.append(c[1])
        return fieldlist

    @checkDbOpen
    def updateMovieStarRating(self, movietitle, starcount):
        if self.checkForTitle(movietitle):
            with getDbCursor(self.dbpath, self.dbmutex, "w") as dbcursor:
                dbcursor.execute("UPDATE movie_data set rating=? WHERE title=?", (starcount, movietitle))

    @checkDbOpen
    def updatePlayCount(self, movietitle, curdate):
        if self.checkForTitle(movietitle):
            with getDbCursor(self.dbpath, self.dbmutex, "w") as dbcursor:
                count = dbcursor.execute("SELECT playcount from movie_data where title=?", (movietitle,)).fetchone()[0]
                dbcursor.execute("UPDATE movie_data set playcount=? where title=?", (count+1, movietitle))
                dbcursor.execute("UPDATE movie_data set lastplay=? where title=?", (curdate, movietitle))
            return count+1

    #This function builds up our SQL query and then passes that onto _SEARCH
    def search(self, querydata, andorstate):
        if not isinstance(querydata, dict):
            return []
        #Build up our query
        #For when we highlight results later
        hlsections = {}
        #Get a list of search parameters
        sep = " AND "
        params = ["SELECT * FROM movie_data WHERE "]
        for field, value in querydata.items():
            if len(value) == 0:
                continue
            if field not in hlsections:
                hlsections[field] = []
            #Eventually I think I will make it possible to handle multiple query fields of the same field type
            #For now an easy solution is to use a special character to delineate multiple vales for a single field
            #TODO Using both a value range and multiple values separated with a ; doesn't work at all
            valuesplit = [v.strip() for v in re.split(";", value)]
            if len(valuesplit) > 1: #Multiple values for this field
                hlsections[field] += valuesplit
                querystr = "(%s LIKE '%%%s%%'" % (field, valuesplit[0])
                for w in valuesplit[1:]:
                    querystr += " %s %s LIKE '%%%s%%'" % (andorstate[field], field, w)
                querystr += ") "
            else:
                #Treat integers differently
                if field in "year runtime playcount rating imdb_rating":
                    valuerangereg = re.search("([0-9]+(?:\.[0-9]+)?)[\s]*-[\s]*([0-9]+(?:\.[0-9]+)?)", value.strip())
                    if valuerangereg is not None:
                        valuerange = [float(valuerangereg.group(1)), float(valuerangereg.group(2))]
                        #Corrections for weirdness.

                        if valuerange[0] > valuerange[1]: #Start of the range higher than the end
                            valuerange.reverse()
                        querystr = "CAST(%s as %s) BETWEEN %s AND %s" % (field, "REAL" if field == "imdb_rating" else "INTEGER", valuerange[0], valuerange[1])
                        hlsections[field] += [valuerange[0], valuerange[1]]
                    else:
                        #Not a number range
                        #Make sure we're just getting numbers
                        cleanvalreg = re.search("([0-9]+)", value)
                        if cleanvalreg is None: #Not a number at all, fallback to LIKE query
                            cleanval = value.strip()
                            querystr = "%s LIKE '%%%s%%'" % (field, cleanval)
                        else:
                            cleanval = cleanvalreg.group(1)
                            querystr = "(%s == %s) or (%s == %s)" % (field, cleanval, field, float(cleanval))
                        hlsections[field] = [cleanval]
                else:
                    querystr = "%s LIKE '%%%s%%'" % (field, value if value is not None else "9999") #Safe fail if the regex isnt set
                    #Save this for highlighting later
                    hlsections[field].append(value)
            if len(params) > 1:
                querystr = sep + querystr
            params.append(querystr)
        results = self._SEARCH("".join(params))
        results["hlsections"] = hlsections
        print("".join(params))
        return results

    @checkDbOpen
    def _SEARCH(self, querystr):
        with getDbCursor(self.dbpath, self.dbmutex) as dbcursor:
            return fixDbData(dbcursor.execute(querystr).fetchall(), self.fieldlist)

