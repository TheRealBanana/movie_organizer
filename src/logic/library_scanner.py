# Very basic multithreaded crawler that will crawl each drive on a separate thread.
# If you are using SSD's you could probably get away with multiple crawlers per drive
import threading
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
    def __init__(self):
        self.stopping = False
        pass

    def startScan(self):
        self.stopping = False
        pass

    def stopScan(self):
        self.stopping = True