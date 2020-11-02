# Very basic multithreaded crawler that will crawl each drive on a separate thread.
# If you are using SSD's you could probably get away with multiple crawlers per drive
import threading
from .movie_library import *
import os
import os.path

class Crawler(threading.Thread):
    def __init__(self, startpath, searchparams):
        super(Crawler, self).__init__()
        self.startpath = startpath
        self.searchparams = searchparams
        self.stopthread = False

    def run(self):
        print("DOIN THREADED STUFFS")
        from time import sleep
        for x in range(10):
            if self.stopthread: break
            sleep(1)
        print("DONE WITH THREADED STUFFS")
        return


class LibraryScanner:
    def __init__(self, libraryref, scansettings):
        self.stopping = False
        self.libref = libraryref
        self.scansettings = scansettings

    def startScan(self):
        #Spin off a crawl processes for each
        print("SCAN START")
        self.stopping = False


    def stopScan(self):
        self.stopping = True