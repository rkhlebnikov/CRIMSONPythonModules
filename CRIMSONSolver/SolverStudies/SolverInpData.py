from PythonQt.CRIMSON import FaceType
from collections import OrderedDict
from CRIMSONSolver.SolverSetups.SolverSetup3D import CouplingType, SolverType

__author__ = 'rk13'


class SolverInpData():
    def __init__(self, solverSetupData, faceIndicesAndFileNames):
        self.data = OrderedDict()

        getFaceIds = lambda cond: [str(faceIdAndName[0]) for faceIdentifier, faceIdAndName in
                                   faceIndicesAndFileNames.iteritems() if
                                   cond(faceIdentifier.faceType)]
        coupledSurfaceIds = getFaceIds(lambda faceType: faceType == FaceType.ftCapOutflow)
        outputSurfaceIds = getFaceIds(lambda faceType: faceType != FaceType.ftWall)
        wallShearStressSurfaceIds = getFaceIds(lambda faceType: faceType == FaceType.ftWall)

        props = solverSetupData.getProperties()

        #############################################################################
        solutionControlGroup = self['SOLUTION CONTROL']
        solutionControlGroup['Equation of State'] = 'Incompressible'
        solutionControlGroup['Number of Timesteps'] = props['Number of time steps']
        solutionControlGroup['Time Step Size'] = props['Time step size']

        #############################################################################
        outputControlGroup = self['OUTPUT CONTROL']
        outputControlGroup['Print Error Indicators'] = True
        outputControlGroup['Number of Timesteps between Restarts'] = \
            props['Number of time steps between restarts']
        outputControlGroup['Print ybar'] = props['Output error indicator']

        if props['Output wall shear stress']:
            outputControlGroup['Number of Force Surfaces'] = len(wallShearStressSurfaceIds)
            outputControlGroup["Surface ID's for Force Calculation"] = ' '.join(wallShearStressSurfaceIds)

        #############################################################################
        materialPropertiesGroup = self['MATERIAL PROPERTIES']
        materialPropertiesGroup['Viscosity'] = props['Viscosity']
        materialPropertiesGroup['Density'] = props['Density']

        #############################################################################
        cardiovascularModelingGroup = self['CARDIOVASCULAR MODELING PARAMETERS']
        cardiovascularModelingGroup['Global Node Numbering'] = True
        cardiovascularModelingGroup['Influx Coefficient'] = props['Influx coefficient']

        cardiovascularModelingGroup['Residual Control'] = props['Residual control']
        cardiovascularModelingGroup['Residual Criteria'] = props['Residual criteria']
        cardiovascularModelingGroup['Minimum Required Iterations'] = props['Minimum required iterations']

        cardiovascularModelingGroup['Number of Coupled Surfaces'] = len(coupledSurfaceIds)

        cardiovascularModelingGroup['Pressure Coupling'] = CouplingType.enumNames[props['Pressure coupling']]

        cardiovascularModelingGroup['Number of Surfaces which Output Pressure and Flow'] = len(outputSurfaceIds)
        cardiovascularModelingGroup['List of Output Surfaces'] = ' '.join(outputSurfaceIds)

        #############################################################################
        linearSolverGroup = self['LINEAR SOLVER']
        nSteps = props['Step construction']
        linearSolverGroup['Step Construction'] = '{0} # this is the standard {1} iteration'.format('0 1 ' * nSteps,
                                                                                                   nSteps)
        linearSolverGroup['Solver Type'] = SolverType.enumNames[props['Solver type']]

        #############################################################################
        discretizationControlGroup = self['DISCRETIZATION CONTROL']
        discretizationControlGroup['Basis Function Order'] = 1
        discretizationControlGroup['Quadrature Rule on Interior'] = 2
        discretizationControlGroup['Quadrature Rule on Boundary'] = 2
        discretizationControlGroup['Include Viscous Correction in Stabilization'] = True
        discretizationControlGroup['Lumped Mass Fraction on Left-hand-side'] = 0.0
        discretizationControlGroup['Lumped Mass Fraction on Right-hand-side'] = 0.0
        discretizationControlGroup['Time Integration Rule'] = 'Second Order'
        discretizationControlGroup['Time Integration Rho Infinity'] = 0.0
        discretizationControlGroup['Flow Advection Form'] = 'Convective'

    def __getitem__(self, item):
        return self.data.setdefault(item, OrderedDict())