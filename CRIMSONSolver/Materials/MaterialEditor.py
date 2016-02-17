try:
    import os
    import math

    import PythonQt

    PythonQt.QtCore.QObject = PythonQt.private.QObject

    from PythonQt import QtGui, QtCore, QtUiTools
    from PythonQt.CRIMSON import Utils
    
    import PythonHighlighter

except:
    class MaterialEditor(object):
        pass

else:
    def findChild(widget, name):
        for w in widget.children():
            if w.objectName == name:
                return w
        for w in widget.children():
            result = findChild(w, name)
            if result:
                return result

    class RepresentationType(object):
        Constant, Table, Script = range(3)

    class SingleMaterialEditor(object):
        def __init__(self, materialData):
            self.materialData = materialData

            uiFileName = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "ui", "SingleMaterialEditorWidget.ui")

            self.ui = QtUiTools.QUiLoader().load(QtCore.QFile(str(uiFileName)))

            self.scriptTextEditor = findChild(self.ui, "scriptTextEdit")
            self.highlighter = PythonHighlighter.PythonHighlighter(self.scriptTextEditor)
            self.scriptTextEditor.setText(materialData.scriptData)

            self.representationComboBox = findChild(self.ui, "representationComboBox")
            self.customMaterialFrame = findChild(self.ui, "customMaterialFrame")
            self.overrideCheckBox = findChild(self.ui, "overrideCheckBox")

            if materialData.representation == RepresentationType.Constant:
                self.customMaterialFrame.hide()
            else:
                self.overrideCheckBox.setChecked(True)
                self.representationComboBox.setCurrentIndex(materialData.representation - 1)

            self.materialNameLineEdit = findChild(self.ui, "materialNameLineEdit")
            self.materialNameLineEdit.setText(materialData.name)

    class MaterialData(object):
        def __init__(self, name = '', nDimensions = 1, repr = RepresentationType.Constant, tableData = [], scriptData = ''):
            self.name = name
            self.nDimensions = nDimensions
            self.representation = repr
            self.tableData = tableData
            self.scriptData = scriptData

    class MaterialEditor(object):
        def __init__(self, materials):
            self.materials = [MaterialData('Stiffness', 1), MaterialData('Thickness', 3, RepresentationType.Script, [],
'''def compute():
    pass
''')]
            uiFileName = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "ui", "MaterialEditorWidget.ui")

            self.ui = QtUiTools.QUiLoader().load(QtCore.QFile(str(uiFileName)))
            self.materialsWidget = findChild(self.ui, "materialsWidget")

            self.singleMaterialEditors = [SingleMaterialEditor(m) for m in self.materials]
            for e in self.singleMaterialEditors:
                self.materialsWidget.layout().addWidget(e.ui)

            self.materialsWidget.layout().addStretch()

        def getEditorWidget(self):
            return self.ui


