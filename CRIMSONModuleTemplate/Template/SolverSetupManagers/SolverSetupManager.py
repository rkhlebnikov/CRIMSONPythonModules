from {{ModuleName}}.BoundaryConditionSets import ({{#BoundaryConditionSetNames}}{{name}}, {{/BoundaryConditionSetNames}})
from {{ModuleName}}.BoundaryConditions import ({{#BoundaryConditionNames}}{{name}}, {{/BoundaryConditionNames}})
from {{ModuleName}}.SolverParameters import ({{#SolverParametersNames}}{{name}}, {{/SolverParametersNames}})
from {{ModuleName}}.SolverStudies import ({{#SolverStudyNames}}{{name}}, {{/SolverStudyNames}})
from {{ModuleName}}.Materials import ({{#MaterialNames}}{{name}}, {{/MaterialNames}})


class {{SolverSetupManagerName}}(object):
    humanReadableName = "{{ModuleName}}"

    def __init__(self):
        self.boundaryConditionSetClasses = {
            {{#BoundaryConditionSetNames}}
                "{{name}}": {{name}}.{{name}},
            {{/BoundaryConditionSetNames}}
            }
        self.solverParametersClasses = {
            {{#SolverParametersNames}}
                "{{name}}": {{name}}.{{name}},
            {{/SolverParametersNames}}
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
        self.materialClasses = {
            {{#MaterialNames}}
                "{{name}}": {{name}}.{{name}},
            {{/MaterialNames}}
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
