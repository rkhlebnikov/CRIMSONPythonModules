from PythonQt.CRIMSON import FaceType
from collections import OrderedDict
from CRIMSONSolver.SolverParameters.SolverParameters3D import CouplingType, SolverType
from CRIMSONSolver.ScalarProblem.Scalar import Scalar
from PythonQt.CRIMSON import Utils

__author__ = 'rk13'


class SolverInpData():
    def __init__(self, solverParametersData, faceIndicesAndFileNames, scalars):
        self.data = OrderedDict()

        getFaceIds = lambda cond: [str(faceIdAndName[0]) for faceIdentifier, faceIdAndName in
                                   faceIndicesAndFileNames.iteritems() if
                                   cond(faceIdentifier.faceType)]
        coupledSurfaceIds = getFaceIds(lambda faceType: faceType == FaceType.ftCapOutflow)
        outputSurfaceIds = getFaceIds(lambda faceType: faceType != FaceType.ftWall)
        wallShearStressSurfaceIds = getFaceIds(lambda faceType: faceType == FaceType.ftWall)

        props = solverParametersData.getProperties()

        isScalar = (len(scalars)>0)
        if isScalar:
            diffusivities = ""
            for scalar in scalars:
                diffusivities = diffusivities + str(scalar.getProperties()["Diffusion coefficient"]) + " "


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
        if isScalar:
            materialPropertiesGroup['Scalar Diffusivity'] = diffusivities

        #############################################################################
        cardiovascularModelingGroup = self['CARDIOVASCULAR MODELING PARAMETERS']
        cardiovascularModelingGroup['Global Node Numbering'] = True
        cardiovascularModelingGroup['Influx Coefficient'] = props['Influx coefficient']

        cardiovascularModelingGroup['Residual Control'] = props['Residual control']
        cardiovascularModelingGroup['Residual Criteria'] = props['Residual criteria']
        if isScalar:
            cardiovascularModelingGroup['Scalar Residual Control'] = props['Scalar residual control']
            for index in enumerate(scalars):
                cardiovascularModelingGroup['Scalar {0} Solver Tolerance'.format(index+1)] = props['Scalar residual criteria']
        cardiovascularModelingGroup['Minimum Required Iterations'] = props['Minimum required iterations']

        cardiovascularModelingGroup['Number of Coupled Surfaces'] = len(coupledSurfaceIds)

        cardiovascularModelingGroup['Pressure Coupling'] = CouplingType.enumNames[props['Pressure coupling']]

        cardiovascularModelingGroup['Number of Surfaces which Output Pressure and Flow'] = len(outputSurfaceIds)
        cardiovascularModelingGroup['List of Output Surfaces'] = ' '.join(outputSurfaceIds)

        try:
            cardiovascularModelingGroup['Simulate in Purely Zero Dimensions'] = props[
                'Simulate in Purely Zero Dimensions']
        except KeyError:
            # Catch case where old scene does not contain Simulate in Purely Zero Dimensions; just set False
            # until the user explicitly changes this.
            Utils.logWarning('This is an old scene; Simulate\n'
                             'in Purely Zero Dimensions was missing; setting it to '
                             'False. Delete and recreate your Solver\nParameters '
                             'in CRIMSON to avoid this warning.')
            cardiovascularModelingGroup['Simulate in Purely Zero Dimensions'] = False

        #############################################################################
        linearSolverGroup = self['LINEAR SOLVER']
        if isScalar:
            linearSolverGroup['Solve Scalars'] = len(scalars)
            linearSolverGroup['Step Construction'] = props['Step construction sequence']
            Utils.logInformation(props['Step construction sequence'])
        else:
            try:
                nSteps = props['Step construction (no. of solves and updates)']

            except KeyError:
                # Catch case where old scene does not contain new naming of Step Construction
                Utils.logWarning('This is an old scene; Checking\n'
                                 'old naming convention.')
                nSteps = props['Step construction']

            linearSolverGroup['Step Construction'] = '{0} # this is the standard {1} iteration'.format(
                '0 1 ' * nSteps, nSteps)
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