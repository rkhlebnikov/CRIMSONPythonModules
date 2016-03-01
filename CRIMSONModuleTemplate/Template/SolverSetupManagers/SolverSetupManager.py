from {{ModuleName}}.BoundaryConditionSets import ({{#BoundaryConditionSetNames}}{{name}}, {{/BoundaryConditionSetNames}})
from {{ModuleName}}.BoundaryConditions import ({{#BoundaryConditionNames}}{{name}}, {{/BoundaryConditionNames}})
from {{ModuleName}}.SolverSetups import ({{#SolverSetupNames}}{{name}}, {{/SolverSetupNames}})
from {{ModuleName}}.SolverStudies import ({{#SolverStudyNames}}{{name}}, {{/SolverStudyNames}})


class {{SolverSetupManagerName}}(object):
    humanReadableName = "{{ModuleName}}"

    def __init__(self):
        self.boundaryConditionSetClasses = {
            {{#BoundaryConditionSetNames}}
                "{{name}}": {{name}}.{{name}},
            {{/BoundaryConditionSetNames}}
            }
        self.solverSetupClasses = {
            {{#SolverSetupNames}}
                "{{name}}": {{name}}.{{name}},
            {{/SolverSetupNames}}
            }
        self.solverStudyClasses = {
            {{#SolverStudyNames}}
                "{{name}}": {{name}}.{{name}},
            {{/SolverStudyNames}}
            }
        self.boundaryConditionClasses = {
            {{#BoundaryConditionNames}}
                "{{name}}": {{name}}.{{name}},
            {{/BoundaryConditionNames}}
            }

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
