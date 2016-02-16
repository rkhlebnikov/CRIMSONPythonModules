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

    class MaterialEditor(object):
        def __init__(self, prescribedVelocitiesBC):
            self.prescribedVelocitiesBC = prescribedVelocitiesBC

            uiFileName = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "ui", "MaterialEditorWidget.ui")

            self.ui = QtUiTools.QUiLoader().load(QtCore.QFile(str(uiFileName)))

            scriptTextEditor = findChild(self.ui, "scriptTextEdit")
            self.highlighter = PythonHighlighter.PythonHighlighter(scriptTextEditor)

        def getEditorWidget(self):
            return self.ui

