from CRIMSONCore.PropertyStorage import PropertyStorage
from CRIMSONCore.VersionedObject import VersionedObject, Versions

class CouplingType(object):
    enumNames = ["Explicit", "Implicit", "P-Implicit"]
    Explicit, Implicit, PImplicit = range(3)

class SolverType(object):
    enumNames = ["memLS", "acusim"]
    memLS, acusim = range(2)

# Note: this class is primarily responsible for holding data that gets written to solver.inp
class SolverParameters3D(PropertyStorage):
    # Where iterations is a list of dict
    # [
    #   {
    #       "Operation": <scalar symbol>,
    #       "Iterations": <Number of iterations>
    #   },
    #   ...
    # ]
    #
    # Example:
    # [
    #   {
    #       "Operation": "III",
    #       "Iterations" 8
    #   },
    #   {
    #       "Operation": "IV",
    #       "Iterations" 20
    #   },
    #   {
    #       "Operation": "III",
    #       "Iterations" 5
    #   },
    #   {
    #       "Operation": "IV",
    #       "Iterations" 6
    #   },
    # ]
    def setIterations(self, iterations):
        self.Iterations = iterations
    
    def getIterations(self):
        return self.Iterations

    def _getStepConstructionSection(self):
        simParametersCategory = self.properties[2]
        simParameters = simParametersCategory['Simulation parameters']
        stepConstructionSection = simParameters[5]

        return stepConstructionSection

    def getFluidIterationCount(self):
        stepConstructionSection = self._getStepConstructionSection()
        numberOfSteps = stepConstructionSection['Step construction']

        #print('DEBUG: [get] Properties is')
        #print(self.properties)
        return numberOfSteps

    def setFluidIterationCount(self, fluidIterationCount):
        stepConstructionSection = self._getStepConstructionSection()
        stepConstructionSection['Step construction'] = fluidIterationCount

        #print('DEBUG: [set] Properties is')
        #print(self.properties)

    def __init__(self):
        PropertyStorage.__init__(self)

        # NOTE: These iterations are not written to solver.inp, they are used by a second Python file in the flowsolver.
        self.Iterations = []

        self.properties = [
            {
                "Time parameters":
                 [
                    {
                        "Number of time steps": 200,
                        "attributes": {"minimum": 1}
                    },
                    {
                        "Time step size": 0.01,
                        "attributes": {"minimum": 0.0, "suffix": " s"}
                    }
                 ]
            },
            {
                "Fluid parameters":
                [
                    {
                        "Viscosity": 0.004,
                        "attributes": {"minimum": 0.0, "suffix": u" g/(mm\u00B7s)"}
                    },
                    {
                        "Density": 0.00106,
                        "attributes": {"minimum": 0.0, "suffix": u" g/mm\u00B3"}
                    }
                ]
            },
            {
                "Simulation parameters":
                [
                    {
                        "Solver type": SolverType.memLS,
                        "attributes": {"enumNames": SolverType.enumNames}
                    },
                    {
                        "Number of time steps between restarts": 5,
                        "attributes": {"minimum": 1}
                    },
                    {
                        "Residual control": True,
                    },
                    {
                        "Residual criteria": 0.001,
                        "attributes": {"minimum": 0.0}
                    },
                    {
                        "Minimum required iterations": 2,
                        "attributes": {"minimum": 1}
                    },
                    {
                        "Step construction": 5,
                        "attributes": {"minimum": 1}
                    },
                    {
                        "Pressure coupling": CouplingType.Implicit,
                        "attributes": {"enumNames": CouplingType.enumNames}
                    },
                    {
                        "Influx coefficient": 0.5,
                        "attributes": {"minimum": 0.01, "maximum": 1.0}
                    },
                    {
                        "Simulate in Purely Zero Dimensions": False,
                    },
                ]
            },
            {
                "Output parameters":
                [
                    {
                        "Output wall shear stress": True
                    },
                    {
                        "Output error indicator": True
                    }
                ]
            },
            {
                "Scalar simulation parameters":
                [
                    {
                        "Scalar Influx Coefficient": 0.5,
                        "attributes": {"minimum": 0.01, "maximum": 1.0}
                    },

                    # If you want to run the fluid solver only for a few timesteps before running the scalar simulation
                    # (e.g., to let the fluids "settle out"), set this to something other than timestep 1.
                    # Note that timesteps are 1-based. This is NOT an iteration.
                    {
                        "Start scalar simulation at timestep": 1,
                        "attributes": {"minimum": 1}
                    },
                    {
                        "End Flow Simulation Early":
                        [
                            # If you want to stop running the flowsolver after a certain number of timesteps, but continue running
                            # the scalar problem after that, enable this option and set the timestep to stop on
                            #
                            # The names are a bit redundant because I think it looks up the name of the property only
                            # based on the innermost name
                            {
                                "End Flow Simulation Early Enable": False,
                            },

                            {
                                "End Flow Simulation at Timestep": 1,
                                "attributes": {"minimum": 1}
                            }
                        ]
                    },

                    # Type type of scalar discontinuity capturing, 
                    # 1 0 is the one we usually use.
                    {
                        "Scalar Discontinuity Capturing": u"1 0"
                    },


                ]
            },
        ]

    def upgrade_Pre2021_To_v2021A(self):
        print('Applying v2021A upgrades to Solver Parameters...')
        self.Iterations = []
        
        scalarSimulationParameters =  {
            "Scalar simulation parameters":
            [
                {
                    "Scalar Influx Coefficient": 0.5,
                    "attributes": {"minimum": 0.01, "maximum": 1.0}
                },

                # If you want to run the fluid solver only for a few timesteps before running the scalar simulation
                # (e.g., to let the fluids "settle out"), set this to something other than timestep 1.
                # Note that timesteps are 1-based. This is NOT an iteration.
                {
                    "Start scalar simulation at timestep": 1,
                    "attributes": {"minimum": 1}
                },
                {
                    "End Flow Simulation Early":
                    [
                        # If you want to stop running the flowsolver after a certain number of timesteps, but continue running
                        # the scalar problem after that, enable this option and set the timestep to stop on
                        #
                        # The names are a bit redundant because I think it looks up the name of the property only
                        # based on the innermost name
                        {
                            "End Flow Simulation Early Enable": False,
                        },

                        {
                            "End Flow Simulation at Timestep": 1,
                            "attributes": {"minimum": 1}
                        }
                    ]
                },

                # Type type of scalar discontinuity capturing, 
                # 1 0 is the one we usually use.
                {
                    "Scalar Discontinuity Capturing": u"1 0"
                },


            ]
        }

        self.properties.append(scalarSimulationParameters)

    def upgradeObject(self, toVersion):
        if(toVersion == Versions.v2021A):
            self.upgrade_Pre2021_To_v2021A()