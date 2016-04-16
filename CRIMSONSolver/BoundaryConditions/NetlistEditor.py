try:
    import os
    import subprocess

    import PythonQt

    PythonQt.QtCore.QObject = PythonQt.private.QObject

    from PythonQt import QtGui, QtCore, QtUiTools
    from PythonQt.CRIMSON import Utils

except:
    class NetlistEditor(object):
        pass

else:

    class SiblingAndParentLayoutDeletingButton(QtGui.QPushButton):
        def __init__(self, buttonText, sibling):
            super(QtGui.QPushButton, self).__init__(buttonText)
            self.sibling = sibling
            # Note that multiple calls to connect just add additional callbacks, so other actions can be connected too.
            self.connect('clicked(bool)', self.deleteParentAndSibling)
            self.setToolTip('Remove this file from scene')
            self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
            # width = self.fontMetrics().boundingRectangle(buttonText).width() + 10
            # self.setMaximumWidth(width)
            # minimum, preferred, expanding
        def deleteParentAndSibling(self):
            self.sibling.setParent(None)
            self.parent().layout().removeItem(self.parent().layout())
            self.setParent(None)




    class NetlistEditor(object):
        def __init__(self, Netlist):
            self.Netlist = Netlist
            uiFileName = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "ui", "WOW.ui")

            self.ui = QtUiTools.QUiLoader().load(QtCore.QFile(str(uiFileName)))

            self.netlistEditorLaunchButton = self.ui.findChild(PythonQt.QtCore.QObject, "NetlistEditorLaunchWidget")
            self.netlistEditorLaunchButton.connect('clicked(bool)', self.netlistEditorLaunchButtonPressed)

            self.netlistLoadFileButton = self.ui.findChild(PythonQt.QtCore.QObject, "NetlistDescriptionLoaderWidget")
            self.netlistLoadFileButton.connect('clicked(bool)', self.netlistLoadFileButtonPressed)

            self.netlistLoadScriptButton = self.ui.findChild(PythonQt.QtCore.QObject, "NetlistDynamicAdjustmentLoaderWidget")
            self.netlistLoadScriptButton.connect('clicked(bool)', self.netlistLoadDynamicAdjusterScriptButtonPressed)

            self.fileContentsViewer = self.ui.findChild(PythonQt.QtCore.QObject, "NetlistLoadedFileInfo")
            self.fileContentsViewer.setText('Loaded configuration will be displayed here.')

            self.recreateSavedState()

        def getEditorWidget(self):
            return self.ui

        def netlistLoadFileButtonPressed(self):
            fileName = self.getFileName()
            if not fileName:
                return
            success = self.loadNetlistFile(fileName)
            if success:
                self.assimilateCircuitDescriptionFile(fileName)

        def assimilateCircuitDescriptionFile(self, fileName):
            removerButtonTrigger = self.addLoadedFileInfoToGui(fileName, "Circuit Specification: ")
            self.Netlist.setCircuitDescriptionFileRemover(removerButtonTrigger)

        def netlistLoadDynamicAdjusterScriptButtonPressed(self):
            fileName = self.getFileName()
            if not fileName:
                return
            success = self.loadNetlistDynamicAdjusterFile(fileName)
            if success:
                self.addLoadedFileInfoToGui(fileName, "Adjuster Script: ")

        def netlistEditorLaunchButtonPressed(self):
            netlistEditorExecutablePathWithoutExtension = PythonQt.Qt.QApplication.applicationDirPath() + '\\CRIMSONBCT'
            # for different operating systems:
            if os.path.isfile(netlistEditorExecutablePathWithoutExtension):
                executablePathToRun = netlistEditorExecutablePathWithoutExtension
            else:
                executablePathToRun = netlistEditorExecutablePathWithoutExtension + '.exe'
            print executablePathToRun
            subprocess.call([executablePathToRun])
            # subprocess.call(['D:\\Dev\\QSapecNG-CrimsonBCT-Git\\CrimsonBctGit\\bin\\Debug\\RUN_CRIMSONBCT.bat'])
            # print "WARNING TO DEVS - call to CRIMSON Netlist Editor is in debug mode!"

        def loadNetlistFile(self, fileName):
            success = False
            with open(fileName, 'r') as inputFile:
                netlistSurfacesDat = inputFile.read()
                self.Netlist.addCircuitFile(fileName, netlistSurfacesDat)
                self.fileContentsViewer.setText(netlistSurfacesDat)
                success = True

            return success

        def loadNetlistDynamicAdjusterFile(self, fileName):
            success = False
            with open(fileName, 'r') as inputFile:
                dynamicAdjusterScriptContents = inputFile.read()
                self.Netlist.addDynamicAdjusterFile(fileName, dynamicAdjusterScriptContents)
                self.fileContentsViewer.setText(dynamicAdjusterScriptContents)
                success = True
            return success

        def addLoadedFileInfoToGui(self, fileName, fileDescription):
            horizontalLayout = QtGui.QHBoxLayout()
            # self.ui.layout().addWidget()
            viewLoadedFileButton = QtGui.QPushButton(fileDescription + ' ' + fileName)

            displayFileContents = lambda : self.fileContentsViewer.setText(self.Netlist.getFile(fileName))
            viewLoadedFileButton.connect('clicked(bool)', displayFileContents)
            viewLoadedFileButton.setToolTip('Click to view this file')
            viewLoadedFileButton.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
            horizontalLayout.addWidget(viewLoadedFileButton)

            removerButton = SiblingAndParentLayoutDeletingButton('Remove', viewLoadedFileButton)
            removerButton.connect('clicked(bool)', self.clearFileContentsViewer)
            removerButton.connect('clicked(bool)', lambda : self.Netlist.removeFile(fileName))

            horizontalLayout.addWidget(removerButton)
            self.ui.layout().addLayout(horizontalLayout)

            removerButtonProgramaticTrigger = lambda : removerButton.click()
            return removerButtonProgramaticTrigger

        def getFileName(self):
            return PythonQt.QtGui.QFileDialog.getOpenFileName(self.ui, "Load netlist_surfaces", "",
                                                                  "Netlist Boundary Conditions (*.dat);; All files (*.*)")

        def clearFileContentsViewer(self):
            self.fileContentsViewer.setText('')

        def recreateSavedState(self):
            if self.Netlist.getNetlistCircuitFileName() != '':
                self.assimilateCircuitDescriptionFile(self.Netlist.getNetlistCircuitFileName())
            for dynamicAdjustmentFileName in self.Netlist.getCircuitDynamicAdjustmentFiles():
                self.addLoadedFileInfoToGui(dynamicAdjustmentFileName, "Adjuster Script: ")