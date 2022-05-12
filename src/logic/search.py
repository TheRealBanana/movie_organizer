from PyQt5.QtCore import QThread, QObject, pyqtSignal, QVariant, Qt
from PyQt5.QtWidgets import QListWidgetItem
from difflib import SequenceMatcher
import re

#Change the way we highlight results
START_HIGHLIGHT = '<span style="background-color: #FFFF00">'
END_HIGHLIGHT = "</span>"
HIGHLIGHT_SUB_REGEX = START_HIGHLIGHT + r"\1" + END_HIGHLIGHT

class movieSearchJob(QObject):
    searchProgressUpdate = pyqtSignal(int) # General progress - how many have been processed/how many total
    newSearchResult = pyqtSignal(QVariant)
    searchJobFinished = pyqtSignal()
    threadFinished = pyqtSignal(QVariant)
    countUpdate = pyqtSignal(int)

    def __init__(self, libraryinfowidgetref, querydata, movielibref, sublibref, parent=None):
        super(movieSearchJob, self).__init__(parent)
        self.libinfowidget = libraryinfowidgetref
        self.querydata = querydata
        self.movieLibrary = movielibref
        self.subtitleLibrary = sublibref
        self.stopping = False
        #Not pretty but I think later it will smooth out
        self.movieresults = {}
        self.subtitleresults = {}
        self.andorstate = self.querydata.pop("andorstate")
        self.dlgsearch = self.querydata.pop("dlgsearch")
        self.resultcount = []
        self.matcheddlg = {}

    def startSearch(self):
        #Make sure we have search parameters
        if len(self.querydata) == 0:
            if self.dlgsearch is None:
                return #Nothing entered
            else: #Just a piece of dialog, this means we have to search the entire database
                self.querydata = {"title": "%"}

        #Get a subset of movies to search through and pass that to our subtitle search if there is a dialog search parameter
        self.movieresults = self.movieLibrary.search(self.querydata, self.andorstate)
        self.hlsections = self.movieresults.pop("hlsections")
        if len(self.movieresults.keys()) == 0:
            print("No movie found in movies db for query")

        if self.dlgsearch is not None:
            self.dlgsearch = re.sub(r"[^\w\s]", "", self.dlgsearch) #Remove any weird characters or punctuation from our search string
            #Get the subtitles for every movie in our initial search results
            self.subtitleresults = self.subtitleLibrary.search(list(self.movieresults.keys()))

        #Filter down the remaining results and highlight anything we find
        movietitles = list(self.movieresults.keys()) if self.dlgsearch is None else list(self.subtitleresults.keys())
        for k in movietitles:
            #Search for our quote in this movie
            if self.dlgsearch is not None and k in self.subtitleresults:
                dialogmatch = self.findAllQuotes(self.subtitleresults[k])
                if dialogmatch is not None:
                    self.matcheddlg[k] = dialogmatch
                else: #We didn't find the dialog in this movie, so don't include it in our results
                    del(self.movieresults[k])
                    continue

            self.movieresults[k] = self.highlightResults(k, self.movieresults[k])
            listitem = QListWidgetItem("(%s)        %s" % (self.movieresults[k]["cleanyear"], self.movieresults[k]["cleantitle"]))
            listitem.setData(Qt.UserRole, self.movieresults[k])
            listitem.setToolTip(str(self.movieresults[k]["filename"]))
            #Keep the results in alphabetical order
            self.resultcount.append(k)
            self.resultcount.sort()
            self.libinfowidget.movieLibraryList.insertItem(self.resultcount.index(k), listitem)
            self.countUpdate.emit(len(self.resultcount))

        self.threadFinished.emit(self)
        print("THREAD FINISHED")

    def highlightResults(self, k, rdata):
        #Go through our results and highlight any sections we searched with
        #preserve the title name for later stuffs
        rdata["cleantitle"] = rdata["title"]
        #I gotta figure out a better system than this. This is just dumb.
        rdata["cleanyear"] = rdata["year"]
        #Highlight whatever matched
        for section in self.hlsections:
            #Handle years differently
            if section == "year":
                if rdata[section] in self.hlsections[section]:
                    rdata["year"] = START_HIGHLIGHT + str(rdata["year"]) + END_HIGHLIGHT

            elif isinstance(rdata[section], str):
                rgx = "(%s)" % "|".join([re.escape(str(x)) for x in self.hlsections[section]])
                rdata[section] = re.sub(rgx, HIGHLIGHT_SUB_REGEX, rdata[section], flags=re.IGNORECASE|re.MULTILINE)
            elif isinstance(rdata[section], list):
                for idx, string in enumerate(rdata[section]):
                    #List could be people or genres
                    #TODO We can match character names too. Will probably use a separate search tag for that.
                    rgx = "(%s)" % "|".join([re.escape(str(x)) for x in self.hlsections[section]])
                    checkstr = string["name"] + " " + string["character"] if isinstance(string, dict) else string
                    namematch = re.search(rgx, checkstr, flags=re.I)
                    if namematch is not None:
                        if isinstance(string, dict):
                            string["name"] = re.sub("(%s)" % re.escape(namematch.group(1)), HIGHLIGHT_SUB_REGEX, string["name"], flags=re.I)
                            #Highlight character names too
                            charmatch = re.search("(%s)" % "|".join([re.escape(str(x)) for x in self.hlsections[section]]), string["character"], flags=re.I)
                            if charmatch is not None:
                                string["character"] = re.sub("(%s)" % re.escape(charmatch.group(1)), HIGHLIGHT_SUB_REGEX, string["character"], flags=re.I)
                        else:
                            rdata[section][idx] = re.sub("(%s)" % re.escape(namematch.group(1)), HIGHLIGHT_SUB_REGEX, string, flags=re.I)

            #Add dialog match data if we have it
            if k in self.matcheddlg:
                rdata["dialogmatch"] = self.matcheddlg[k]

            return rdata

    def findAllQuotes(self, r):
        #z = get_best_match(self.dlgsearch, r["subtitles"]["corpus"])
        #print(z)
        return self.dialogSearch(r)

    def dialogSearch(self, result):
        #Just placeholder matching. This is both exact and terrible, better matching later
        retdata = None
        if self.dlgsearch.lower() in result["subtitles"]["corpus"].lower():
            retdata = {}
            retdata["result"] = result
            #Figure out the timecode by using the timecode dict and the index of our match
            matchidx = result["subtitles"]["corpus"].lower().index(self.dlgsearch.lower())
            lasti = 0
            for tcindex in result["subtitles"]["timecodes"]:
                if tcindex < matchidx:
                    lasti = tcindex
                    continue
                break
            #TODO This is just placeholder stuffs removeme
            #convert timecode to seconds
            hours, minutes, seconds = re.match(r"([0-9]{1,2}):([0-9]{2}):([0-9]{2})(?:,[0-9]{3}|\.[0-9]{2})", result["subtitles"]["timecodes"][lasti]).groups()
            #TODO One idea here is to maybe subtrack a few seconds off the timecode so that its queued up
            #at a point just BEFORE the quote, so you have time to get into the scene before its said.
            timecodeseconds = (int(hours)*60*60) + (int(minutes)*60) + int(seconds) - 2
            print(timecodeseconds)
            vlcpath = r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
            #TODO Maybe we should print a couple timecodes worth of subs
            #Or at least get the length of this particular sub bit and print it completely
            print("FOUND FOR QUERY %s at index %s" % (self.dlgsearch, matchidx))
            print("TIMECODE AT  %s" % result["subtitles"]["timecodes"][lasti])
            #Find the index of lasti so we can pull in the next few lines too
            indexlist = list(result["subtitles"]["timecodes"].keys())
            timecodeidx = indexlist.index(lasti)
            movielink = "%s --network-caching=15000 --start-time %s \"%s\"" % (vlcpath, timecodeseconds, result["filelocation"] + "\\" + result["filename"])
            #We removed punctuation earlier to make matching easier but now it looks goofy
            #Separating lines by a newline makes it look a bit better
            nicequote = result["subtitles"]["corpus"][indexlist[timecodeidx-1]:lasti] + "\n" # Grab one line before
            #nicequote = ""
            for n in range(1,5): #How many lines ahead to grab?
                #Ran out of lines?
                if timecodeidx+n > len(indexlist)-1:
                    break
                nicequote += result["subtitles"]["corpus"][lasti:indexlist[timecodeidx + n]] + "\n"
                lasti = indexlist[timecodeidx+n]
            retdata["movielink"] = movielink
            retdata["nicequote"] = nicequote
            print("FOR DIALOG:\n%s" % nicequote)
            print("Link to play movie at that time: \n")
            print(movielink)
            print("\n")

        return retdata

class SearchManager(QObject):
    def __init__(self, movielibref, subtitlelibref, searchtabref, parent=None):
        super(SearchManager, self).__init__(parent)
        self.movielibref = movielibref
        self.subtitlelibref = subtitlelibref
        self.activeSearchJobs = {}
        self.searchtabref = searchtabref

    def threadFinishedCallback(self, searchJob):
        searchJob.threadref.quit()
        searchJob.threadref.wait()
        searchJob.threadref.deleteLater()
        del(self.activeSearchJobs[hex(id(searchJob))])
        senderobj = self.sender()
        if senderobj is None: #Not sure how this happens
            return
        idx = self.searchtabref.indexOf(senderobj.libinfowidget)
        oldtext = self.searchtabref.tabText(idx)
        self.searchtabref.setTabText(idx, oldtext[2:-2]) #Cutting off the first and last 2 chars. TODO WIP ETA TBD

    def updateTabCount(self, count):
        senderobj = self.sender()
        if senderobj is None: #Not sure how this happens
            return
        idx = self.searchtabref.indexOf(senderobj.libinfowidget)
        self.searchtabref.setTabText(idx, "~ SEARCH RESULTS (%s) ~" % count)

    def newSearchJob(self, searchparams, listwidgetref):
        newjob = movieSearchJob(listwidgetref, searchparams, self.movielibref, self.subtitlelibref)
        #newjob.startSearch()
        newthread = QThread()
        newthread.setTerminationEnabled(True)
        newjob.threadref = newthread
        newjob.moveToThread(newthread)
        newthread.started.connect(newjob.startSearch)
        newjob.threadFinished.connect(self.threadFinishedCallback)
        newjob.countUpdate.connect(self.updateTabCount)
        self.activeSearchJobs[hex(id(newjob))] = newjob
        #updatemsg = "Created new search job thread (%s)" % hex(id(newjob))
        #print(updatemsg)
        newthread.start()

#This function is just superb and I know I couldn't do any better.
#Thanks so much to Ulf Aslak for this
#https://stackoverflow.com/questions/36013295/find-best-substring-match/36132391#36132391
def get_best_match(query, corpus, step=4, flex=3, case_sensitive=False, verbose=False):
    """Return best matching substring of corpus.
    Parameters
    ----------
    query : str
    corpus : str
    step : int
        Step size of first match-value scan through corpus. Can be thought of
        as a sort of "scan resolution". Should not exceed length of query.
    flex : int
        Max. left/right substring position adjustment value. Should not
        exceed length of query / 2.
    Outputs
    -------
    output0 : str
        Best matching substring.
    output1 : float
        Match ratio of best matching substring. 1 is perfect match.
    """

    def _match(a, b):
        """Compact alias for SequenceMatcher."""
        return SequenceMatcher(None, a, b).ratio()

    def scan_corpus(step):
        """Return list of match values from corpus-wide scan."""
        match_values = []

        m = 0
        while m + qlen - step <= len(corpus):
            match_values.append(_match(query, corpus[m : m-1+qlen]))
            if verbose:
                print(query, "-", corpus[m: m + qlen], _match(query, corpus[m: m + qlen]))
            m += step

        return match_values

    def index_max(v):
        """Return index of max value."""
        return max(range(len(v)), key=v.__getitem__)

    def adjust_left_right_positions():
        """Return left/right positions for best string match."""
        # bp_* is synonym for 'Best Position Left/Right' and are adjusted
        # to optimize bmv_*
        p_l, bp_l = [pos] * 2
        p_r, bp_r = [pos + qlen] * 2

        # bmv_* are declared here in case they are untouched in optimization
        bmv_l = match_values[int(p_l / step)]
        bmv_r = match_values[int(p_l / step)]

        for f in range(flex):
            ll = _match(query, corpus[p_l - f: p_r])
            if ll > bmv_l:
                bmv_l = ll
                bp_l = p_l - f

            lr = _match(query, corpus[p_l + f: p_r])
            if lr > bmv_l:
                bmv_l = lr
                bp_l = p_l + f

            rl = _match(query, corpus[p_l: p_r - f])
            if rl > bmv_r:
                bmv_r = rl
                bp_r = p_r - f

            rr = _match(query, corpus[p_l: p_r + f])
            if rr > bmv_r:
                bmv_r = rr
                bp_r = p_r + f

        return bp_l, bp_r, _match(query, corpus[bp_l : bp_r])

    if not case_sensitive:
        query = query.lower()
        corpus = corpus.lower()

    qlen = len(query)

    match_values = scan_corpus(step)
    if len(match_values) == 0:
        return 0, 0, 0.0
    pos = index_max(match_values) * step

    pos_left, pos_right, match_value = adjust_left_right_positions()

    return corpus[pos_left: pos_right].strip(), match_value