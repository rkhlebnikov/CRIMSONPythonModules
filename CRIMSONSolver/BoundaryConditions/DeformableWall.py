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
                "Vessel wall properties":
                [
                    {
                        "Density": 0.001,
                        "attributes": {"suffix": u" g/mm\u00B3", "minimum": 0.0}
                    },
                    {
                        "Thickness": 1.0,
                        "attributes": {"suffix": u" mm", "minimum": 0.0}
                    },
                    {
                        "Young's modulus": 4661000.0,
                        "attributes": {"suffix": u" g/(mm\u00B7s\u00B2)", "minimum": 0.0}
                    },
                    {
                        "Poisson ratio": 0.5,
                        "attributes": {"minimum": -1.0, "maximum": 0.5}
                    },
                    # Shear constant, unitless, never changes as per CAFA thesis p. 79
                    #{
                    #    "Shear constant": 0.833333,
                    #    "attributes": {"suffix": u" g/(mm\u00B7s\u00B2)", "minimum": 0.0}
                    #},
                ]
            },
            {
                "Tissue support properties":
                [
                    {
                        "Enable tissue support term": True,
                    },
                    {
                        "Stiffness coefficient": 40.0,
                    },
                    {
                        "Damping properties":
                        [
                            {
                                "Enable damping term": True,
                            },
                            {
                                "Damping coefficient": 100.0,
                            },
                        ]
                    },
                    #{
                    #    "State filtering properties": [
                    #        {
                    #            "Enable state filter term": False,
                    #        },
                    #        {
                    #            "State filter coefficient": 0.0,
                    #        },
                    #    ]
                    #},
                ]
            },
        ]