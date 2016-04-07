try:
    import os

    import PythonQt

    PythonQt.QtCore.QObject = PythonQt.private.QObject

    from PythonQt import QtGui, QtCore, QtUiTools
    from PythonQt.CRIMSON import Utils

except:
    class NetlistEditor(object):
        pass

else:

    class NetlistEditor(object):
        def __init__(self, Netlist):
            self.Netlist = Netlist
            uiFileName = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "ui", "WOW.ui")

            self.ui = QtUiTools.QUiLoader().load(QtCore.QFile(str(uiFileName)))
            self.netlistEditor = self.ui.findChild(PythonQt.QtCore.QObject, "WOW")
            self.netlistEditor.connect('clicked(bool)', self.buttonPressed)

        def getEditorWidget(self):
            return self.ui

        def buttonPressed(self):
            fileName = PythonQt.QtGui.QFileDialog.getOpenFileName(self.ui, "Load netlist_surfaces", "",
                                                                  "Netlist Boundary Conditions (*.dat);; All files (*.*)")

            if not fileName:
                return

            self.loadNetlistFile(fileName)

        def loadNetlistFile(self, fileName):
            with open(fileName, 'r') as inputFile:
                self.Netlist.netlistSurfacesDat = inputFile.read()
                print self.Netlist.netlistSurfacesDat