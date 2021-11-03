from PyQt5.QtCore import QThread, QObject, pyqtSignal, QVariant, Qt
from PyQt5.QtWidgets import QListWidgetItem
import re

#Change the way we highlight results
START_HIGHLIGHT = '<span style="background-color: #FFFF00">'
END_HIGHLIGHT = "</span>"
HIGHLIGHT_SUB_REGEX = START_HIGHLIGHT + r"\1" + END_HIGHLIGHT

class dialogSearchJob(QObject):
    searchProgressUpdate = pyqtSignal(int) # General progress - how many have been processed/how many total
    newSearchResult = pyqtSignal(QVariant)
    searchJobFinished = pyqtSignal()

    def __init__(self, libraryinfowidgetref, querydata, movielibref, sublibref, parent=None):
        super(dialogSearchJob, self).__init__(parent)
        self.libinfowidget = libraryinfowidgetref
        self.querydata = querydata
        self.movieLibrary = movielibref
        self.subtitleLibrary = sublibref
        self.stopping = False

    def startSearch(self):
        #Do we need to search subtitles for dialog?
        andorstate = self.querydata.pop("andorstate")
        dlgsearch = self.querydata.pop("dlgsearch")

        if len(self.querydata) == 0: #No search parameters
            if dlgsearch is None:
                return #Nothing entered
            else: #Just a piece of dialog, this means we have to search the entire database
                results = self.movieLibrary.search({"title": "%"}, {})
        else:
            results = self.movieLibrary.search(self.querydata, andorstate)
        hlsections = results.pop("hlsections")
        if len(results.keys()) == 0:
            print("No movie found in movies db for query")

        matcheddlg = {}
        if dlgsearch is not None:
            #Remove any weird characters or punctuation
            dlgsearch = re.sub(r"[^\w\s]", "", dlgsearch)
            dlgresults = self.subtitleLibrary.search(list(results.keys()))

            for k, r in dlgresults.items():
                #Just placeholder matching. This is both exact and terrible, better matching later
                if dlgsearch.lower() in r["subtitles"]["corpus"].lower():
                    matcheddlg[k] = {}
                    matcheddlg[k]["result"] = r
                    #Figure out the timecode by using the timecode dict and the index of our match
                    matchidx = r["subtitles"]["corpus"].lower().index(dlgsearch.lower())
                    lasti = 0
                    for i in r["subtitles"]["timecodes"]:
                        if i < matchidx:
                            lasti = i
                            continue
                        break
                    #TODO This is just placeholder stuffs removeme
                    #convert timecode to seconds
                    tc, _ = re.split("\s*-->\s*", r["subtitles"]["timecodes"][lasti])
                    hours, minutes, seconds = re.match("([0-9]{2}):([0-9]{2}):([0-9]{2}),[0-9]{3}", tc).groups()
                    #TODO One idea here is to maybe subtrack a few seconds off the timecode so that its queued up
                    #at a point just BEFORE the quote, so you have time to get into the scene before its said.
                    #Trying 10 seconds for now
                    timecodeseconds = (int(hours)*60*60) + (int(minutes)*60) + int(seconds) - 5
                    vlcpath = r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
                    #TODO Maybe we should print a couple timecodes worth of subs
                    #Or at least get the length of this particular sub bit and print it completely
                    print("FOUND FOR QUERY %s at index %s" % (dlgsearch, matchidx))
                    print("TIMECODE AT  %s" % r["subtitles"]["timecodes"][lasti])
                    #Find the index of lasti so we can pull in the next few lines too
                    indexlist = list(r["subtitles"]["timecodes"].keys())
                    timecodeidx = indexlist.index(lasti)
                    movielink = "%s --network-caching=15000 --start-time %s \"%s\"" % (vlcpath, timecodeseconds, r["filelocation"] + "\\" + r["filename"])
                    #We removed punctuation earlier to make matching easier but now it looks goofy
                    #Separating lines by a newline makes it look a bit better
                    #nicequote = r["subtitles"]["corpus"][indexlist[timecodeidx-1]:lasti] + "\n" # Grab one line before
                    nicequote = ""
                    for n in range(1,5): #How many lines ahead to grab?
                        #Ran out of lines?
                        if timecodeidx+n > len(indexlist)-1:
                            break
                        nicequote += r["subtitles"]["corpus"][lasti:indexlist[timecodeidx+n]] + "\n"
                        lasti = indexlist[timecodeidx+n]
                    matcheddlg[k]["movielink"] = movielink
                    matcheddlg[k]["nicequote"] = nicequote
                    print("FOR DIALOG:\n%s" % nicequote)
                    print("Link to play movie at that time: \n")
                    print(movielink)
                    print("\n")

        #If we have any results from the dialog search, we can filter our any movies that didnt match from our main results
        #Not sure if it copies the dict to memory first or if it does it in place. Just to be safe...
        if dlgsearch is not None and len(dlgsearch) > 0:
            tmpresults = {key: results[key] for key in matcheddlg.keys()}
            results = tmpresults

        #Now create a new search query tab and populate the results

        #Go through our results and highlight any sections we searched with
        for k, rdata in sorted(results.items(), key=lambda t: t[0].lower()):
            #preserve the title name for later stuffs
            rdata["cleantitle"] = rdata["title"]
            listitem = QListWidgetItem(rdata["title"])
            #Highlight whatever matched
            for section in hlsections:
                #Handle years differently
                if section == "year":
                    if rdata[section] in hlsections[section]:
                        rdata["year"] = START_HIGHLIGHT + str(rdata["year"]) + END_HIGHLIGHT

                elif isinstance(rdata[section], str):
                    rgx = "(%s)" % "|".join([re.escape(str(x)) for x in hlsections[section]])
                    rdata[section] = re.sub(rgx, HIGHLIGHT_SUB_REGEX, rdata[section], flags=re.IGNORECASE|re.MULTILINE)
                elif isinstance(rdata[section], list):
                    for idx, string in enumerate(rdata[section]):
                        #List could be people or genres
                        #TODO We can match character names too. Will probably use a separate search tag for that.
                        rgx = "(%s)" % "|".join([re.escape(str(x)) for x in hlsections[section]])
                        checkstr = string["name"] + " " + string["character"] if isinstance(string, dict) else string
                        namematch = re.search(rgx, checkstr, flags=re.I)
                        if namematch is not None:
                            if isinstance(string, dict):
                                string["name"] = re.sub("(%s)" % re.escape(namematch.group(1)), HIGHLIGHT_SUB_REGEX, string["name"], flags=re.I)
                                #Highlight character names too
                                charmatch = re.search("(%s)" % "|".join([re.escape(str(x)) for x in hlsections[section]]), string["character"], flags=re.I)
                                if charmatch is not None:
                                    string["character"] = re.sub("(%s)" % re.escape(charmatch.group(1)), HIGHLIGHT_SUB_REGEX, string["character"], flags=re.I)
                            else:
                                rdata[section][idx] = re.sub("(%s)" % re.escape(namematch.group(1)), HIGHLIGHT_SUB_REGEX, string, flags=re.I)

                #print("%s - %s" % (section, type(d[section])))
            #Add dialog match data if we have it
            if k in matcheddlg:
                rdata["dialogmatch"] = matcheddlg[k]
            listitem.setData(Qt.UserRole, rdata)
            listitem.setToolTip(str(rdata["filename"]))
            self.libinfowidget.movieLibraryList.addItem(listitem)

class SearchManager(QObject):
    def __init__(self, movielibref, subtitlelibref, parent=None):
        super(SearchManager, self).__init__(parent)
        self.movielibref = movielibref
        self.subtitlelibref = subtitlelibref

    def newSearchJob(self, searchparams, listwidgetref):
        #Placeholder, will do threading and stuffs after but for now this is just to get things back working
        newjob = dialogSearchJob(listwidgetref, searchparams, self.movielibref, self.subtitlelibref)
        newjob.startSearch()