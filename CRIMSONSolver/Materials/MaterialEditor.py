from CRIMSONSolver.Materials.MaterialData import RepresentationType

try:
    import os
    import math
    import numpy

    import PythonQt

    PythonQt.QtCore.QObject = PythonQt.private.QObject

    from PythonQt import QtGui, QtCore, QtUiTools
    from PythonQt.CRIMSON import Utils

    import PythonHighlighter

except:
    class MaterialEditor(object):
        pass

else:
    class SingleMaterialEditor(object):
        def __init__(self, materialData):
            self.materialData = materialData

            uiPath =  os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")
            uiFileName = os.path.join(uiPath, "SingleMaterialEditorWidget.ui")

            l = QtUiTools.QUiLoader()
            l.setWorkingDirectory(QtCore.QDir(uiPath))
            self.ui = l.load(QtCore.QFile(str(uiFileName)))

            findChild = lambda name: self.ui.findChild(PythonQt.QtCore.QObject, name)

            self.scriptTextEditor = findChild("scriptTextEdit")
            self.highlighter = PythonHighlighter.PythonHighlighter(self.scriptTextEditor)
            self.scriptTextEditor.setText(materialData.scriptData)
            self.scriptTextEditor.connect('textChanged()', self.saveScriptText)
            self.helpButton = findChild("helpButton")
            self.helpButton.connect('clicked(bool)', self.showHelpTooltip)

            self.inputVariableComboBox = findChild("inputVariableComboBox")
            self.inputVariableComboBox.setCurrentIndex(self.materialData.tableData.inputVariableType)
            self.inputVariableComboBox.connect('currentIndexChanged(int)', self.setInputVariableType)

            self.representationComboBox = findChild("representationComboBox")
            self.customMaterialFrame = findChild("customMaterialFrame")
            self.overrideCheckBox = findChild("overrideCheckBox")

            if materialData.representation == RepresentationType.Constant:
                self.customMaterialFrame.hide()
            else:
                self.overrideCheckBox.setChecked(True)
                self.representationComboBox.setCurrentIndex(materialData.representation)

            self.overrideCheckBox.connect('toggled(bool)', self.enableRepresentationOverride)
            self.representationComboBox.connect('currentIndexChanged(int)', self.setRepresentationByComboBoxIndex)

            self.materialNameLineEdit = findChild("materialNameLineEdit")
            self.materialNameLineEdit.setText(materialData.name)

            self.tableWidget = findChild("tableWidget")

            findChild("addRowBeforeButton").connect('clicked(bool)', self.addRowBefore)
            findChild("addRowAfterButton").connect('clicked(bool)', self.addRowAfter)
            findChild("removeRowsButton").connect('clicked(bool)', self.removeRows)
            findChild("loadTableButton").connect('clicked(bool)', self.loadTableFromFile)
            findChild("saveTableButton").connect('clicked(bool)', self.saveTableToFile)

            class DoubleValueDelegate(QtGui.QItemDelegate):
                def createEditor(self, parent, option, index):
                    le = QtGui.QLineEdit(parent)
                    le.setValidator(QtGui.QDoubleValidator(le))
                    return le

            self.doubleValueDelegate = DoubleValueDelegate()
            self.tableWidget.setItemDelegate(self.doubleValueDelegate)

            self.fillingTable = False
            self.fillTableFromData()
            self.tableWidget.model().connect('dataChanged(QModelIndex, QModelIndex)', self.fillDataFromTable)
            self.tableWidget.model().connect('rowsRemoved(QModelIndex, int, int)', self.fillDataFromTable)

        def enableRepresentationOverride(self, enable):
            if enable:
                self.materialData.representation = RepresentationType.Table
                self.representationComboBox.setCurrentIndex(RepresentationType.Table)
            else:
                self.materialData.representation = RepresentationType.Constant

        def setRepresentationByComboBoxIndex(self, index):
            self.materialData.representation = index

        ################################################################################
        # Table handling
        ################################################################################
        def fillTableFromData(self):
            self.fillingTable = True
            self.tableWidget.clear()
            self.tableWidget.setColumnCount(self.materialData.nComponents + 1)

            labels = [self.inputVariableComboBox.currentText]
            if self.materialData.nComponents == 1:
                labels.append(self.materialData.name)
            else:
                labels.extend(self.materialData.componentNames)
            self.tableWidget.setHorizontalHeaderLabels(labels)

            tableData = self.materialData.tableData.data

            if tableData is not None:
                self.tableWidget.setRowCount(tableData.shape[1])

                it = numpy.nditer(tableData, flags=['multi_index'])
                while not it.finished:
                    col = it.multi_index[0]
                    row = 0 if len(it.multi_index) == 1 else it.multi_index[1]
                    self.tableWidget.setItem(row, col, QtGui.QTableWidgetItem(str(it[0])))
                    it.iternext()

            self.fillingTable = False

        def fillDataFromTable(self):
            if self.fillingTable:
                return
            self.materialData.tableData.data = numpy.empty((self.tableWidget.columnCount, self.tableWidget.rowCount))
            for row in xrange(self.tableWidget.rowCount):
                for col in xrange(self.tableWidget.columnCount):
                    item = self.tableWidget.item(row, col)
                    self.materialData.tableData.data[col, row] = float(item.text()) if item is not None else 0

        def setInputVariableType(self, type):
            self.materialData.tableData.inputVariableType = type
            self.fillTableFromData()

        def addRowBefore(self):
            curRow = self.tableWidget.currentRow()
            if curRow < 0:
                curRow = 0
            self.tableWidget.insertRow(curRow)
            self.fillRowWithZeroes(curRow)

        def addRowAfter(self):
            curRow = self.tableWidget.currentRow()
            if curRow < 0:
                curRow = self.tableWidget.rowCount
            else:
                curRow += 1
            self.tableWidget.insertRow(curRow)
            self.fillRowWithZeroes(curRow)

        def fillRowWithZeroes(self, row):
            for col in xrange(self.tableWidget.columnCount):
                self.tableWidget.setItem(row, col, QtGui.QTableWidgetItem('0'))

        def removeRows(self):
            rowIndices = [x.row() for x in self.tableWidget.selectionModel().selectedRows()]
            for row in sorted(rowIndices, reverse=True):
                self.tableWidget.removeRow(row)

        def loadTableFromFile(self):
            fileName = QtGui.QFileDialog.getOpenFileName(self.ui, "Load table", "",
                                                         "Text file (*.txt);; All files (*.*)")
            if not fileName:
                return

            try:
                data = numpy.transpose(numpy.loadtxt(fileName))
                if len(data.shape) <= 1:
                    nCols = len(data.shape)
                else:
                    nCols = data.shape[0]

                if nCols != self.materialData.nComponents + 1:
                    raise RuntimeError("Incorrect number of colums - expected {0}, got {1}"
                                       .format(self.materialData.nComponents + 1, nCols))
            except Exception as e:
                QtGui.QMessageBox.critical(None, "Table loading failed",
                                           "Failed to load table data from {0}.\n"
                                           "Reason:\n{1}".format(fileName, str(e)))
                return

            self.materialData.tableData.data = data
            self.fillTableFromData()

        def saveTableToFile(self):
            if self.materialData.tableData is None:
                return

            tableData = self.materialData.tableData.data
            fileName = QtGui.QFileDialog.getSaveFileName(self.ui, "Save table", "",
                                                         "Text file (*.txt);; All files (*.*)")
            if not fileName:
                return

            numpy.savetxt(fileName, numpy.transpose(tableData), fmt='%g', delimiter='\t')

        ################################################################################
        # Script handling
        ################################################################################
        def saveScriptText(self):
            self.materialData.scriptData = self.scriptTextEditor.toPlainText()

        def showHelpTooltip(self):
            QtGui.QToolTip.showText(self.helpButton.mapToGlobal(QtCore.QPoint(0, 0)), self.helpButton.toolTip)

    class MaterialEditor(object):
        def __init__(self, materials):
            self.materials = materials
            uiFileName = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "ui", "MaterialEditorWidget.ui")

            self.ui = QtUiTools.QUiLoader().load(QtCore.QFile(str(uiFileName)))
            self.materialsWidget = self.ui

            self.singleMaterialEditors = [SingleMaterialEditor(m) for m in self.materials]
            for e in self.singleMaterialEditors:
                self.materialsWidget.layout().addWidget(e.ui)

            self.materialsWidget.layout().addStretch()

        def getEditorWidget(self):
            return self.ui
