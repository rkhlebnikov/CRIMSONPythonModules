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

    class NetlistFileTypes(object):
        CircuitDescriptionDat = 'Netlist circuit'
        DynamicAdjustmentPython = 'Dynamic adjustment script'
        AdditionalData = 'Additional data'


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
        def __init__(self, netlistBC):
            self.netlistBC = netlistBC

            uiPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")
            uiFileName = os.path.join(uiPath, "NetlistBCEditorWidget.ui")

            l = QtUiTools.QUiLoader()
            l.setWorkingDirectory(QtCore.QDir(uiPath))
            self.ui = l.load(QtCore.QFile(str(uiFileName)))

            netlistEditorLaunchButton = self.ui.findChild(PythonQt.QtCore.QObject, "launchEditorButton")
            netlistEditorLaunchButton.connect('clicked(bool)', self.launchEditor)

            netlistLoadFileButton = self.ui.findChild(PythonQt.QtCore.QObject, "loadCircuitButton")
            netlistLoadFileButton.connect('clicked(bool)', self.loadCircuit)

            netlistLoadScriptButton = self.ui.findChild(PythonQt.QtCore.QObject, "loadAdjustmentScriptButton")
            netlistLoadScriptButton.connect('clicked(bool)', self.loadAdjustmentScript)

            netlistLoadAdditionalDatFileButton = self.ui.findChild(PythonQt.QtCore.QObject, "loadDataFileButton")
            netlistLoadAdditionalDatFileButton.connect('clicked(bool)', self.loadAdditionalDatFile)

            removeButton = self.ui.findChild(PythonQt.QtCore.QObject, "removeButton")
            removeButton.connect('clicked(bool)', self.removeSelected)

            self.fileContentsViewer = self.ui.findChild(PythonQt.QtCore.QObject, "scriptContestTextEdit")
            self.scriptListTable = self.ui.findChild(PythonQt.QtCore.QObject, "scriptListTable")
            self.scriptListTable.connect('currentCellChanged(int, int, int, int)', self.showContents)

            self.recreateSavedState()

        def getEditorWidget(self):
            return self.ui

        def launchEditor(self):
            # netlistEditorExecutablePathWithoutExtension = PythonQt.Qt.QApplication.applicationDirPath() + '\\CRIMSONBCT'
            # # for different operating systems:
            # if os.path.isfile(netlistEditorExecutablePathWithoutExtension):
            #     executablePathToRun = netlistEditorExecutablePathWithoutExtension
            # else:
            #     executablePathToRun = netlistEditorExecutablePathWithoutExtension + '.exe'
            # print executablePathToRun
            # subprocess.call([executablePathToRun])
            subprocess.call(['D:\\Dev\\QSapecNG-CrimsonBCT-Git\\CrimsonBctGit\\bin\\Debug\\RUN_CRIMSONBCT.bat'])
            print "WARNING TO DEVS - call to CRIMSON Netlist Editor is in debug mode!"

        def loadCircuit(self):
            fileName = self.getDatFileName("Load Netlist circuit description")
            if not fileName:
                return
            if self.loadNetlistFile(fileName):
                # Find the netlist description file row in the table
                for row in xrange(self.scriptListTable.rowCount):
                    if self.scriptListTable.item(row, 0).text() == NetlistFileTypes.CircuitDescriptionDat:
                        self.scriptListTable.removeRow(row)
                        break
                self.addLoadedFileInfoToTable(fileName, NetlistFileTypes.CircuitDescriptionDat)

        def loadAdjustmentScript(self):
            fileName = self.getPyFileName()
            if not fileName:
                return
            nowAddFileToGui = self.loadNetlistDynamicAdjusterFile(fileName)
            if nowAddFileToGui:
                self.addLoadedFileInfoToTable(fileName, NetlistFileTypes.DynamicAdjustmentPython)

        def loadAdditionalDatFile(self):
            fileName = self.getAdditionalDatFileName()
            if not fileName:
                return
            if self.loadNetlistAdditionalDatFile(fileName):
                self.addLoadedFileInfoToTable(fileName, NetlistFileTypes.AdditionalData)

        def loadNetlistFile(self, fileName):
            try:
                with open(fileName, 'r') as inputFile:
                    netlistSurfacesDat = inputFile.read()
                    self.netlistBC.addCircuitFile(fileName, netlistSurfacesDat)
                    return True
            except:
                return False

        def loadNetlistDynamicAdjusterFile(self, fileName):
            try:
                with open(fileName, 'r') as inputFile:
                    dynamicAdjusterScriptContents = inputFile.read()
                    overwroteFileInternally = self.netlistBC.addDynamicAdjusterFile(fileName,
                                                                                    dynamicAdjusterScriptContents)
                    return not overwroteFileInternally
            except:
                return False

        def loadNetlistAdditionalDatFile(self, fileName):
            try:
                with open(fileName, 'r') as inputFile:
                    additionalDatFileContents = inputFile.read()
                    overwroteFileInternally = self.netlistBC.addAdditionalDataFile(fileName, additionalDatFileContents)
                    return not overwroteFileInternally
            except:
                return False

        def addLoadedFileInfoToTable(self, fileName, scriptType, selectNewRow = True):
            self.scriptListTable.setSortingEnabled(False)
            row = self.scriptListTable.rowCount
            self.scriptListTable.insertRow(row)
            self.scriptListTable.setItem(row, 0, PythonQt.QtGui.QTableWidgetItem(scriptType))
            self.scriptListTable.setItem(row, 1, PythonQt.QtGui.QTableWidgetItem(fileName))
            if selectNewRow:
                self.scriptListTable.selectRow(row)
                self.scriptListTable.setCurrentCell(row, 0)
                self.showContents(row) # Force update
            self.scriptListTable.setSortingEnabled(True)

        def getDatFileName(self, dialogTitle):
            return PythonQt.QtGui.QFileDialog.getOpenFileName(self.ui, dialogTitle, "",
                                                              "Netlist Circuit Description (*.dat);; All files (*.*)")

        def getPyFileName(self):
            fileName = PythonQt.QtGui.QFileDialog.getOpenFileName(self.ui, "Load dynamic adjustment Python script", "",
                                                                  "Dynamic Adjustment Script (*.py);; All files (*.*)")
            if self.netlistBC.getCircuitDynamicAdjustmentFiles().__contains__(fileName):
                dialogResult = PythonQt.QtGui.QMessageBox.warning(self.ui, "File Already Loaded",
                                                                  "This file has already been loaded. Overwrite?",
                                                                  PythonQt.QtGui.QMessageBox.Ok,
                                                                  PythonQt.QtGui.QMessageBox.Cancel)
                if dialogResult == PythonQt.QtGui.QMessageBox.Cancel:
                    return None
            return fileName

        def getAdditionalDatFileName(self):
            fileName = PythonQt.QtGui.QFileDialog.getOpenFileName(self.ui, "Load additional data file", "",
                                                                  "Additional Data File (*.dat);; All files (*.*)")
            if self.netlistBC.getCircuitAdditionalDataFiles().__contains__(fileName):
                dialogResult = PythonQt.QtGui.QMessageBox.warning(self.ui, "File Already Loaded",
                                                                  "This file has already been loaded. Overwrite?",
                                                                  PythonQt.QtGui.QMessageBox.Ok,
                                                                  PythonQt.QtGui.QMessageBox.Cancel)
                if dialogResult == PythonQt.QtGui.QMessageBox.Cancel:
                    return None
            return fileName

        def showContents(self, row):
            if row >= 0:
                self.fileContentsViewer.setText(self.netlistBC.getFile(self.scriptListTable.item(row, 1).text()))
            else:
                self.fileContentsViewer.setText('')

        def removeSelected(self):
            persistentIndices = [PythonQt.QtCore.QPersistentModelIndex(x) for x in self.scriptListTable.selectionModel().selectedRows()]
            for index in persistentIndices:
                self.netlistBC.removeFile(self.scriptListTable.item(index.row(), 1).text())
                self.scriptListTable.removeRow(index.row())

        def recreateSavedState(self):
            if self.netlistBC.getNetlistCircuitFileName():
               self.addLoadedFileInfoToTable(self.netlistBC.getNetlistCircuitFileName(), NetlistFileTypes.CircuitDescriptionDat, False)
            for dynamicAdjustmentFileName in self.netlistBC.getCircuitDynamicAdjustmentFiles():
               self.addLoadedFileInfoToTable(dynamicAdjustmentFileName, NetlistFileTypes.DynamicAdjustmentPython, False)
            for additionalDatFile in self.netlistBC.getCircuitAdditionalDataFiles():
               self.addLoadedFileInfoToTable(additionalDatFile, NetlistFileTypes.AdditionalData, False)
