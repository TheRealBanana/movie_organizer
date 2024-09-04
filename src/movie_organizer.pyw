from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from logic.UiFunctions import UIFunctions
from dialogs.MainWindow import Ui_MainWindow
import sys
import traceback


'''
COVER THE BELOW CODE WITH QUOTES TO DISABLE EXCEPTION HANDLING
This is very useful while debugging but probably a bad idea for the final app running under normal conditions.
If we run into an exception we probably don't want to continue operation without restarting into a known good config.
On the other hand trying to debug python exceptions inside of QThreads is annoying to say the least, this makes it so much easier.
'''
def exception_hook(exc_type, exc_value, exc_traceback):
    error_message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"Unhandled exception: {error_message}")
    # Optionally, you can show this in a QMessageBox or log it to a file
sys.excepthook = exception_hook
'''
Just remember to disable this easy mode code when we're done.
'''

class ClosableMainWindow(QtWidgets.QMainWindow):
    MainWindowClose = pyqtSignal()
    def __init__(self, parent=None):
        super(ClosableMainWindow, self).__init__(parent)

    def closeEvent(self, closeEvent):
        self.MainWindowClose.emit()
        closeEvent.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = ClosableMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    uifuncts = UIFunctions(ui, MainWindow)
    # Hook into the app's quiting sequence so it saves our settings before it quits
    MainWindow.MainWindowClose.connect(uifuncts.quitApp)

    #Now that we have the Ui set up, lets finish the initiation process
    #uifuncts.appInit()
    MainWindow.show()
    app.exec_()