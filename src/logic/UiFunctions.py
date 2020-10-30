class UIFunctions:
    def __init__(self, uiref, MainWindow):
        self.uiref = uiref
        self.MainWindow = MainWindow
        #initialize our application
        self.setupConnections()
        print("Doing stuff, important stuff")

    def setupConnections(self):
        self.uiref.actionScan_Media_Collection.triggered.connect(self.MainWindow.close)
    
    def quitApp(self):
        #Do quitting stuff thats important
        print("YOU KNOW I CANT QUIT YOU")