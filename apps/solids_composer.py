import sys
import os
import random
import matplotlib
# Make sure that we are using QT5
matplotlib.use('Qt5Agg')
from PyQt5 import QtCore, QtWidgets

from numpy import arange, sin, pi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

__app__ = "Solids Composer"
__version__ = "0.1"


class Canvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, axis, width=5, height=4, dpi=100, parent=None):
        self.axis = axis
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.axes.set_title("%s axis" % ['x', 'y', 'z'][self.axis])

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.solids = {}

    def add_solids(self, key, solids):
        self.solids[key] = solids

    def update_figure(self):
        # Build a list of 4 random integers between 0 and 10 (both inclusive)
        l = [random.randint(0, 10) for i in range(4)]
        self.axes.cla()
        self.axes.plot([0, 1, 2, 3], l, 'r')
        self.draw()


class ApplicationWindow(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("%s (v%s)" % (__app__, __version__))

        self.menu_bar = QtWidgets.QMenuBar()
        self.createMenus()

        self.main_widget = QtWidgets.QWidget(self)

        layout = QtWidgets.QHBoxLayout(self.main_widget)
        x_canvas = Canvas(0, width=4, height=4, dpi=100, parent=self.main_widget)
        y_canvas = Canvas(1, width=4, height=4, dpi=100, parent=self.main_widget)
        z_canvas = Canvas(2, width=4, height=4, dpi=100, parent=self.main_widget)

        layout.addWidget(x_canvas)
        layout.addWidget(y_canvas)
        layout.addWidget(z_canvas)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

    def importSolids(self):
        self.statusBar().showMessage("Importing solids", 2000)

    def fileQuit(self):
        self.close()

    def closeEvent(self, event):
        self.fileQuit()

    def about(self):
        QtWidgets.QMessageBox.about(self, "About", " ")

    def createMenus(self):
        import_act = QtWidgets.QAction("&Import", self)
        import_act.triggered.connect(self.importSolids)

        file_menu = self.menu_bar.addMenu("&File")
        file_menu.addAction(import_act)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    aw = ApplicationWindow()
    aw.show()

    sys.exit(app.exec_())
