import numpy

from CRIMSONCore.BoundaryCondition import BoundaryCondition
from CRIMSONSolver.BoundaryConditions.PrescribedVelocitiesEditor import PrescribedVelocitiesEditor

from PythonQt.CRIMSON import FaceType

class ProfileType(object):
    enumNames = ["Parabolic", "Womersley", "Plug"]
    Parabolic, Womersley, Plug = range(3)


class PrescribedVelocities(BoundaryCondition):
    unique = False
    humanReadableName = "Prescribed velocities"
    applicableFaceTypes = [FaceType.ftCapInflow, FaceType.ftCapOutflow]

    def __init__(self):
        BoundaryCondition.__init__(self)
        self.properties = [
            {
                "Profile type": ProfileType.Parabolic,
                "attributes": {"enumNames": ProfileType.enumNames}
            },
            {
                "Output parameters":
                [
                    {
                        "Number of periods": 1,
                        "attributes": {"minimum": 1}
                    }
                ],
            },
        ]

        self.originalWaveform = numpy.array([])
        self.smoothedWaveform = numpy.array([])
        self.firstFilteredCoef = 0
        self.numberOfSamples = 100

        self.editor = None

    def createCustomEditorWidget(self):
        if not self.editor:
            self.editor = PrescribedVelocitiesEditor(self)
        return self.editor.getEditorWidget()

    def __getstate__(self):
        odict = self.__dict__.copy() # copy the dict
        del odict['editor'] # editor shouldn't be pickled
        return odict

    def __setstate__(self, dict):
        self.__dict__.update(dict)
        self.editor = None # Reload classes on un-pickling

