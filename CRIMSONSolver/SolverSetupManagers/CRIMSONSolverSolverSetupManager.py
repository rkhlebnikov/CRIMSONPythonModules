from CRIMSONSolver.BoundaryConditionSets.BoundaryConditionSet import BoundaryConditionSet
from CRIMSONSolver.BoundaryConditions import InitialPressure, NoSlip, PrescribedVelocities, RCR, ZeroPressure, \
    DeformableWall
from CRIMSONSolver.SolverSetups.SolverSetup3D import SolverSetup3D
from CRIMSONSolver.SolverStudies.SolverStudy import SolverStudy
from CRIMSONSolver.Materials import DeformableWallMaterial


class CRIMSONSolverSolverSetupManager(object):
    humanReadableName = "CRIMSON Solver"

    def __init__(self):
        self.boundaryConditionSetClasses = {"Boundary condition set": BoundaryConditionSet}
        self.solverSetupClasses = {"Solver setup 3D": SolverSetup3D}
        self.solverStudyClasses = {"Solver study 3D": SolverStudy}
        self.boundaryConditionClasses = {"Initial pressure": InitialPressure.InitialPressure,
                                         "No slip": NoSlip.NoSlip,
                                         "Prescribed velocities": PrescribedVelocities.PrescribedVelocities,
                                         "RCR": RCR.RCR,
                                         "Zero pressure": ZeroPressure.ZeroPressure,
                                         "Deformable wall": DeformableWall.DeformableWall,
                                         }
        self.materialClasses = {"Deformable wall material": DeformableWallMaterial.DeformableWallMaterial}

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

    # Solver setups
    def getSolverSetupNames(self):
        return self.solverSetupClasses.keys()

    def createSolverSetupData(self, name):
        return self.solverSetupClasses[name]()

    # Solver studies
    def getSolverStudyNames(self):
        return self.solverStudyClasses.keys()

    def createSolverStudyData(self, name):
        return self.solverStudyClasses[name]()

    # Material information
    def getMaterialInformation(self):
        return [{"Stiffness": 1.0},
                {"Thickness": 1.0, "attributes": {"suffix": " mm"}},
                {"MultiComponent": [
                        {"A11": 0.0},
                        {"A21": 1.0},
                        {"A22": 0.0}
                    ]}
                ]
