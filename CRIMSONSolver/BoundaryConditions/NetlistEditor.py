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
        CircuitDescriptionDat = 1
        DynamicAdjustmentPython = 2
        AdditionalData = 3

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

            self.netlistLoadAdditionalDatFileButton = self.ui.findChild(PythonQt.QtCore.QObject, "NetlistAdditionalDataLoaderWidget")
            self.netlistLoadAdditionalDatFileButton.connect('clicked(bool)', self.netlistLoadAdditionalDatFileButtonPressed)

            self.fileContentsViewer = self.ui.findChild(PythonQt.QtCore.QObject, "NetlistLoadedFileInfo")
            self.fileContentsViewer.setText('Loaded configuration will be displayed here.')

            self.recreateSavedState()

        def getEditorWidget(self):
            return self.ui

        def netlistLoadFileButtonPressed(self):
            fileName = self.getDatFileName("Load Netlist circuit description")
            if not fileName:
                return
            success = self.loadNetlistFile(fileName)
            if success:
                self.assimilateCircuitDescriptionFile(fileName)

        def assimilateCircuitDescriptionFile(self, fileName):
            removerButtonTrigger = self.addLoadedFileInfoToGui(fileName, NetlistFileTypes.CircuitDescriptionDat)
            self.Netlist.setCircuitDescriptionFileRemover(removerButtonTrigger)

        def netlistLoadDynamicAdjusterScriptButtonPressed(self):
            fileName = self.getPyFileName()
            if not fileName:
                return
            nowAddFileToGui = self.loadNetlistDynamicAdjusterFile(fileName)
            if nowAddFileToGui:
                self.addLoadedFileInfoToGui(fileName, NetlistFileTypes.DynamicAdjustmentPython)

        def netlistLoadAdditionalDatFileButtonPressed(self):
            fileName = self.getAdditionalDatFileName()
            if not fileName:
                return
            nowAddFileToGui = self.loadNetlistAdditionalDatFile(fileName)
            if nowAddFileToGui:
                self.addLoadedFileInfoToGui(fileName, NetlistFileTypes.AdditionalData)

        def netlistEditorLaunchButtonPressed(self):
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

        def loadNetlistFile(self, fileName):
            success = False
            with open(fileName, 'r') as inputFile:
                netlistSurfacesDat = inputFile.read()
                self.Netlist.addCircuitFile(fileName, netlistSurfacesDat)
                self.fileContentsViewer.setText(netlistSurfacesDat)
                success = True

            return success

        def loadNetlistDynamicAdjusterFile(self, fileName):
            nowAddFileToGui = False
            with open(fileName, 'r') as inputFile:
                dynamicAdjusterScriptContents = inputFile.read()
                overwroteFileInternally = self.Netlist.addDynamicAdjusterFile(fileName, dynamicAdjusterScriptContents)
                self.fileContentsViewer.setText(dynamicAdjusterScriptContents)
                nowAddFileToGui = not overwroteFileInternally
            return nowAddFileToGui

        def loadNetlistAdditionalDatFile(self, fileName):
            nowAddFileToGui = False
            with open(fileName, 'r') as inputFile:
                additionalDatFileContents = inputFile.read()
                overwroteFileInternally = self.Netlist.addAdditionalDataFile(fileName, additionalDatFileContents)
                self.fileContentsViewer.setText(additionalDatFileContents)
                nowAddFileToGui = not overwroteFileInternally
            return nowAddFileToGui

        def addLoadedFileInfoToGui(self, fileName, fileType):
            horizontalLayout = QtGui.QHBoxLayout()
            # self.ui.layout().addWidget()
            viewLoadedFileButton = QtGui.QPushButton(fileName)

            displayFileContents = lambda : self.fileContentsViewer.setText(self.Netlist.getFile(fileName))
            viewLoadedFileButton.connect('clicked(bool)', displayFileContents)
            viewLoadedFileButton.setToolTip('Click to view this file')
            viewLoadedFileButton.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
            horizontalLayout.addWidget(viewLoadedFileButton)

            removerButton = SiblingAndParentLayoutDeletingButton('Remove', viewLoadedFileButton)
            removerButton.connect('clicked(bool)', self.clearFileContentsViewer)
            removerButton.connect('clicked(bool)', lambda : self.Netlist.removeFile(fileName))

            horizontalLayout.addWidget(removerButton)

            if fileType == NetlistFileTypes.CircuitDescriptionDat:
                parentLayoutForFileInfo = self.ui.findChild(PythonQt.QtCore.QObject, "LayoutCircuitDescription")
            elif fileType == NetlistFileTypes.DynamicAdjustmentPython:
                parentLayoutForFileInfo = self.ui.findChild(PythonQt.QtCore.QObject, "LayoutPythonScripts")
            elif fileType == NetlistFileTypes.AdditionalData:
                parentLayoutForFileInfo = self.ui.findChild(PythonQt.QtCore.QObject, "LayoutDataFiles")
            else:
                Utils.logWarning('Unknown NetlistFileType \'{0}\'. Skipping.'.format(fileType))
                parentLayoutForFileInfo = self.ui.layout()

            parentLayoutForFileInfo.addLayout(horizontalLayout)

            removerButtonProgramaticTrigger = lambda : removerButton.click()
            return removerButtonProgramaticTrigger

        def getDatFileName(self, dialogTitle):
            return PythonQt.QtGui.QFileDialog.getOpenFileName(self.ui, dialogTitle, "",
                                                                  "Netlist Circuit Description (*.dat);; All files (*.*)")

        def getPyFileName(self):
            fileName =  PythonQt.QtGui.QFileDialog.getOpenFileName(self.ui, "Load dynamic adjustment Python script", "",
                                                              "Dynamic Adjustment Script (*.py);; All files (*.*)")
            if self.Netlist.getCircuitDynamicAdjustmentFiles().__contains__(fileName):
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
            if self.Netlist.getCircuitAdditionalDataFiles().__contains__(fileName):
                dialogResult = PythonQt.QtGui.QMessageBox.warning(self.ui, "File Already Loaded", "This file has already been loaded. Overwrite?", PythonQt.QtGui.QMessageBox.Ok, PythonQt.QtGui.QMessageBox.Cancel)
                if dialogResult == PythonQt.QtGui.QMessageBox.Cancel:
                    return None
            return fileName

        def clearFileContentsViewer(self):
            self.fileContentsViewer.setText('')

        def recreateSavedState(self):
            if self.Netlist.getNetlistCircuitFileName() != '':
                self.assimilateCircuitDescriptionFile(self.Netlist.getNetlistCircuitFileName())
            for dynamicAdjustmentFileName in self.Netlist.getCircuitDynamicAdjustmentFiles():
                self.addLoadedFileInfoToGui(dynamicAdjustmentFileName, NetlistFileTypes.DynamicAdjustmentPython)
            for additionalDatFile in self.Netlist.getCircuitAdditionalDataFiles():
                self.addLoadedFileInfoToGui(additionalDatFile, NetlistFileTypes.AdditionalData)