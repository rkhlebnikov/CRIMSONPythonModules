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
    class RepresentationType(object):
        Constant, Table, Script = range(3)


    class InputVariableType(object):
        DistanceAlongPath, LocalRadius, x, y, z = range(5)


    class SingleMaterialEditor(object):
        def __init__(self, materialData):
            self.materialData = materialData

            uiPath =  os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")
            uiFileName = os.path.join(uiPath, "SingleMaterialEditorWidget.ui")

            self.ui = QtUiTools.QUiLoader().load(QtCore.QFile(str(uiFileName)))

            findChild = lambda name: self.ui.findChild(PythonQt.QtCore.QObject, name)

            self.scriptTextEditor = findChild("scriptTextEdit")
            self.highlighter = PythonHighlighter.PythonHighlighter(self.scriptTextEditor)
            self.scriptTextEditor.setText(materialData.scriptData)

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
                self.representationComboBox.setCurrentIndex(materialData.representation - 1)

            self.materialNameLineEdit = findChild("materialNameLineEdit")
            self.materialNameLineEdit.setText(materialData.name)

            self.tableWidget = findChild("tableWidget")

            addRowBeforeButton = findChild("addRowBeforeButton")
            addRowBeforeButton.setIcon(QtGui.QIcon(os.path.join(uiPath, 'icons', 'before.png')))
            addRowBeforeButton.connect('clicked(bool)', self.addRowBefore)

            addRowAfterButton = findChild("addRowAfterButton")
            addRowAfterButton.setIcon(QtGui.QIcon(os.path.join(uiPath, 'icons', 'after.png')))
            addRowAfterButton.connect('clicked(bool)', self.addRowAfter)

            removeRowsButton = findChild("removeRowsButton")
            removeRowsButton.setIcon(QtGui.QIcon(os.path.join(uiPath, 'icons', 'delete.png')))
            removeRowsButton.connect('clicked(bool)', self.removeRows)

            loadTableButton = findChild("loadTableButton")
            loadTableButton.setIcon(QtGui.QIcon(os.path.join(uiPath, 'icons', 'open.png')))
            loadTableButton.connect('clicked(bool)', self.loadTableFromFile)

            saveTableButton = findChild("saveTableButton")
            saveTableButton.setIcon(QtGui.QIcon(os.path.join(uiPath, 'icons', 'save.png')))
            saveTableButton.connect('clicked(bool)', self.saveTableToFile)

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
                self.tableWidget.setRowCount(tableData.shape[0])

                it = numpy.nditer(tableData, flags=['multi_index'])
                while not it.finished:
                    row = it.multi_index[0]
                    col = 0 if len(it.multi_index) == 1 else it.multi_index[1]
                    self.tableWidget.setItem(row, col, QtGui.QTableWidgetItem(str(it[0])))
                    it.iternext()

            self.fillingTable = False

        def fillDataFromTable(self):
            if self.fillingTable:
                return
            self.materialData.tableData.data = numpy.empty((self.tableWidget.rowCount, self.tableWidget.columnCount))
            for row in xrange(self.tableWidget.rowCount):
                for col in xrange(self.tableWidget.columnCount):
                    item = self.tableWidget.item(row, col)
                    self.materialData.tableData.data[row, col] = float(item.text()) if item is not None else 0

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
                data = numpy.loadtxt(fileName)
                print
                if len(data.shape) <= 1:
                    nCols = len(data.shape)
                else:
                    nCols = data.shape[1]

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

            numpy.savetxt(fileName, tableData, fmt='%g', delimiter='\t')

    class TableData(object):
        def __init__(self, data=numpy.zeros((2, 1)), inputVariableType=InputVariableType.DistanceAlongPath):
            self.data = data
            self.inputVariableType = inputVariableType

    class MaterialData(object):
        def __init__(self, name='', nComponents=1, componentNames=None, repr=RepresentationType.Constant,
                     tableData = TableData(),
                     scriptData=''):
            self.name = name
            self.nComponents = nComponents
            self.componentNames = componentNames
            self.representation = repr
            self.tableData = tableData
            self.scriptData = scriptData


    class MaterialEditor(object):
        def __init__(self, materials):
            self.materials = [MaterialData('Stiffness', 1),
                              MaterialData('Thickness', 3, ['T11', 'T12', 'T22'], RepresentationType.Table,
                                           TableData(numpy.zeros((5, 4)), InputVariableType.LocalRadius),
'''def compute():
   pass
''')]
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
