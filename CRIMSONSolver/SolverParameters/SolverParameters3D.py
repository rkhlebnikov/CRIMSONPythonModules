from CRIMSONCore.PropertyStorage import PropertyStorage

class CouplingType(object):
    enumNames = ["Explicit", "Implicit", "P-Implicit"]
    Explicit, Implicit, PImplicit = range(3)

class SolverType(object):
    enumNames = ["memLS", "acusim"]
    memLS, acusim = range(2)

class SolverParameters3D(PropertyStorage):
    def __init__(self):
        PropertyStorage.__init__(self)
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
                "Scalar simulation parameters":
                [
                    {
                        "Residual control": True,
                    },
                    {
                        "Residual criteria": 0.001,
                        "attributes": {"minimum": 0.0}
                    },
                    {
                        "Step construction sequence": "0 1 0 1 0 1",
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
        ]