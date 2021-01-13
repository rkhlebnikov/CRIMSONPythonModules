from CRIMSONCore.VersionedObject import VersionedObject, Versions

class ScalarProblem(VersionedObject):
    def __init__(self):
        self.ReactionCoefficients = {}
        VersionedObject.__init__(self)
    """
        Sample:
        self.ReactionCoefficients = {
            "k1": 1.234,
            "k2": 3.545
        }
    """

    def getReactionCoefficients(self):
        return self.ReactionCoefficients

    def setReactionCoefficients(self, reactionCoefficients):
        self.ReactionCoefficients = reactionCoefficients