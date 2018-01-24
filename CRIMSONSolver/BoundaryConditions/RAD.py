from CRIMSONCore.FaceData import FaceData
from PythonQt.CRIMSON import FaceType

class RAD(FaceData):
    unique = False
    humanReadableName = "Reaction-advection diffusion"
    applicableFaceTypes = [FaceType.ftCapInflow, FaceType.ftCapOutflow, FaceType.ftWall]

    def __init__(self):
        FaceData.__init__(self)

        self.RADNodeUID = None
        self.RADData = None

    def setDataObject(self, data):  # for use in CPP code
        self.RADData = data

    def setDataNodeUID(self, uid):  # for use in CPP code
        self.RADNodeUID = uid

    def getDataNodeUID(self):  # for use in CPP code
        return self.RADNodeUID

    def __getstate__(self):
        odict = self.__dict__.copy()  # copy the dict
        del odict['RADData']  # RADData shouldn't be pickled
        return odict

    def __setstate__(self, dict):
        self.__dict__.update(dict)
        self.RADData = None  # Reload classes on un-pickling

