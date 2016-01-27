from CRIMSONCore.BoundaryCondition import BoundaryCondition
from PythonQt.CRIMSON import FaceType

class DeformableWall(BoundaryCondition):
    unique = True
    humanReadableName = "Deformable wall"
    applicableFaceTypes = [FaceType.ftWall]

    def __init__(self):
        BoundaryCondition.__init__(self)
        self.properties = [
            {
                "name": "Vessel wall properties",
                "value": [
                    {
                        "name": "Density",
                        "value": 0.001,
                        "attributes": {"suffix": u" g/mm\u00B3", "minimum": 0.0}
                    },
                    {
                        "name": "Thickness",
                        "value": 1.0,
                        "attributes": {"suffix": u" mm", "minimum": 0.0}
                    },
                    {
                        "name": "Young's modulus",
                        "value": 4661000.0,
                        "attributes": {"suffix": u" g/(mm\u00B7s\u00B2)", "minimum": 0.0}
                    },
                    {
                        "name": "Poisson ratio",
                        "value": 0.5,
                        "attributes": {"minimum": -1.0, "maximum": 0.5}
                    },
                    # Shear constant, unitless, never changes as per CAFA thesis p. 79
                    #{
                    #    "name": "Shear constant",
                    #    "value": 0.833333,
                    #    "attributes": {"suffix": u" g/(mm\u00B7s\u00B2)", "minimum": 0.0}
                    #},
                ]
            },
            {
                "name": "Tissue support properties",
                "value": [
                    {
                        "name": "Enable tissue support term",
                        "value": True,
                    },
                    {
                        "name": "Stiffness coefficient",
                        "value": 40.0,
                    },
                    {
                        "name": "Damping properties",
                        "value": [
                            {
                                "name": "Enable damping term",
                                "value": True,
                            },
                            {
                                "name": "Damping coefficient",
                                "value": 100.0,
                            },
                        ]
                    },
                    #{
                    #    "name": "State filtering properties",
                    #    "value": [
                    #        {
                    #            "name": "Enable state filter term",
                    #            "value": False,
                    #        },
                    #        {
                    #            "name": "State filter coefficient",
                    #            "value": 0.0,
                    #        },
                    #    ]
                    #},
                ]
            },
        ]