import numpy
import math

from CRIMSONSolver.BoundaryConditions.PrescribedVelocities import ProfileType

def plugProfileFunction(distance, maxDistance):
    return 0 if distance < 1e-6 else 1

def parabolicProfileFunction(distance, maxDistance):
    order = 2
    return (order + 2) / order * (1 - math.pow(1 - distance / maxDistance, order))


class FlowProfileGenerator(object):
    profileFunctions = {ProfileType.Plug: plugProfileFunction,
                        ProfileType.Parabolic: parabolicProfileFunction}

    def __init__(self, profileType, solidModelData, meshData, faceIdentifier):
        self.faceNormal = solidModelData.getFaceNormal(faceIdentifier)
        distanceMap = {pointIndex: solidModelData.getDistanceToFaceEdge(faceIdentifier,
                                                                        *meshData.getNodeCoordinates(pointIndex))
                       for pointIndex in meshData.getNodeIdsForFace(faceIdentifier)}

        maxDistance = max(distanceMap.itervalues())

        profileFunction = FlowProfileGenerator.profileFunctions[profileType]
        profileValues = {pointIndex: profileFunction(distance, maxDistance) for
                         pointIndex, distance in distanceMap.iteritems()}

        # Compute the volume of the flow profile prism based on a triangle defined by indices
        def computeSubvolume(indices):
            positions = [numpy.array(meshData.getNodeCoordinates(x)) for x in indices]
            crossProduct = numpy.cross(positions[1] - positions[0], positions[2] - positions[0])
            area = numpy.linalg.norm(crossProduct) / 2.0

            return area * reduce(lambda x, y: x + y, (profileValues.get(i, 0) for i in indices)) / 3.0

        totalVolume = reduce(lambda x, y: x + y,
                             (computeSubvolume(faceInfo[2:]) for faceInfo in
                              meshData.getMeshFaceInfoForFace(faceIdentifier)))

        self.normalizedProfileValues = {pointIndex: profileValue / totalVolume for
                                        pointIndex, profileValue in profileValues.iteritems()}

    def generateProfile(self, flowRates):
        return ((pointIndex, ([flowRate * normalizedProfileValue * x for x in self.faceNormal] for flowRate in flowRates)) for
                pointIndex, normalizedProfileValue in
                self.normalizedProfileValues.iteritems())