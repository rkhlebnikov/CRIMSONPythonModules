from CRIMSONCore.PropertyStorage import PropertyStorage

class CouplingType(object):
    enumNames = ["Explicit", "Implicit", "P-Implicit"]
    Explicit, Implicit, PImplicit = range(3)

class SolverType(object):
    enumNames = ["memLS", "acusim"]
    memLS, acusim = range(2)

class SolverSetup3D(PropertyStorage):
    def __init__(self):
        PropertyStorage.__init__(self)
        self.properties = [
            {
                "name": "Time parameters",
                "value": [
                    {
                        "name": "Number of time steps",
                        "value": 200,
                        "attributes": {"minimum": 1}
                    },
                    {
                        "name": "Time step size",
                        "value": 0.01,
                        "attributes": {"minimum": 0.0, "suffix": " s"}
                    }
                ]
            },
            {
                "name": "Fluid parameters",
                "value": [
                    {
                        "name": "Viscosity",
                        "value": 0.004,
                        "attributes": {"minimum": 0.0, "suffix": u" g/(mm\u00B7s)"}
                    },
                    {
                        "name": "Density",
                        "value": 0.00106,
                        "attributes": {"minimum": 0.0, "suffix": u" g/mm\u00B3"}
                    }
                ]
            },
            {
                "name": "Simulation parameters",
                "value": [
                    {
                        "name": "Solver type",
                        "value": SolverType.memLS,
                        "attributes": {"enumNames": SolverType.enumNames}
                    },
                    {
                        "name": "Number of time steps between restarts",
                        "value": 5,
                        "attributes": {"minimum": 1}
                    },
                    {
                        "name": "Residual control",
                        "value": True,
                    },
                    {
                        "name": "Residual criteria",
                        "value": 0.001,
                        "attributes": {"minimum": 0.0}
                    },
                    {
                        "name": "Minimum required iterations",
                        "value": 2,
                        "attributes": {"minimum": 1}
                    },
                    {
                        "name": "Step construction",
                        "value": 5,
                        "attributes": {"minimum": 1}
                    },
                    {
                        "name": "Pressure coupling",
                        "value": CouplingType.Implicit,
                        "attributes": {"enumNames": CouplingType.enumNames}
                    },
                    {
                        "name": "Influx coefficient",
                        "value": 0.5,
                        "attributes": {"minimum": 0.01, "maximum": 1.0}
                    },
                ]
            },
            {
                "name": "Output parameters",
                "value": [
                    {
                        "name": "Output wall shear stress",
                        "value": True,
                    },
                    {
                        "name": "Output error indicator",
                        "value": True,
                    }
                ]
            },
        ]
