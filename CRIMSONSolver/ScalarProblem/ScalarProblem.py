class ScalarProblem(object):
    def __init__(self):
        self.ReactionCoefficients = {}

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