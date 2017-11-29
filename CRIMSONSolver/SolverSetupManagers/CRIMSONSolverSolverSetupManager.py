from CRIMSONSolver.BoundaryConditionSets.BoundaryConditionSet import BoundaryConditionSet
from CRIMSONSolver.BoundaryConditions import InitialPressure, NoSlip, PrescribedVelocities, RCR, ZeroPressure, \
    DeformableWall, Netlist, PCMRI
from CRIMSONSolver.SolverParameters.SolverParameters3D import SolverParameters3D
from CRIMSONSolver.SolverStudies.SolverStudy import SolverStudy
from CRIMSONSolver.Materials import DeformableWallMaterial, AnisoDeformableWallMaterial


class CRIMSONSolverSolverSetupManager(object):
    humanReadableName = "CRIMSON Solver"

    def __init__(self):
        self.boundaryConditionSetClasses = {"Boundary condition set": BoundaryConditionSet}
        self.solverParametersClasses = {"Solver parameters 3D": SolverParameters3D}
        self.solverStudyClasses = {"Solver study 3D": SolverStudy}
        self.boundaryConditionClasses = {"Initial pressure": InitialPressure.InitialPressure,
                                         "No slip": NoSlip.NoSlip,
                                         "Prescribed velocities (analytic)": PrescribedVelocities.PrescribedVelocities,
                                         "RCR": RCR.RCR,
                                         "Zero pressure": ZeroPressure.ZeroPressure,
                                         "Deformable wall": DeformableWall.DeformableWall,
                                         "Netlist": Netlist.Netlist,
                                         "Prescribed velocities (PC-MRI)": PCMRI.PCMRI
                                         }
        self.materialClasses = {"Deformable wall material": DeformableWallMaterial.DeformableWallMaterial,
                                "Deformable wall material (anisotropic)": AnisoDeformableWallMaterial.AnisoDeformableWallMaterial}

    # Boundary condition sets
    def getBoundaryConditionSetNames(self):
        return self.boundaryConditionSetClasses.keys()

    def createBoundaryConditionSet(self, name):
        return self.boundaryConditionSetClasses[name]()

    # Boundary conditions
    def getBoundaryConditionNames(self, ownerBCSet):
        return self.boundaryConditionClasses.keys()

    def createBoundaryCondition(self, name, ownerBCSet):
        return self.boundaryConditionClasses[name]()

    # Materials
    def getMaterialNames(self):
        return self.materialClasses.keys()

    def createMaterial(self, name):
        return self.materialClasses[name]()

    # Solver parameters
    def getSolverParametersNames(self):
        return self.solverParametersClasses.keys()

    def createSolverParameters(self, name):
        return self.solverParametersClasses[name]()

    # Solver studies
    def getSolverStudyNames(self):
        return self.solverStudyClasses.keys()

    def createSolverStudy(self, name):
        return self.solverStudyClasses[name]()