from PythonQt.CRIMSON import FaceType

from CRIMSONSolver.Materials.MaterialBase import MaterialBase

class AnisoDeformableWallMaterial(MaterialBase):
    unique = False
    humanReadableName = "Deformable wall material (anisotropic)"
    applicableFaceTypes = [FaceType.ftWall]

    def __init__(self):
        MaterialBase.__init__(self)
        self.properties = [
            {"Young's modulus (anisotropic)":
                [
                    {"C_qqqq": 0}, 
                    {"C_qqzz": 0}, 
                    {"C_zzzz": 0},
                    {"0.25*(C_qzqz+C_qzzq+C_zqzq+C_zqqz)": 0},
                    {"C_rqrq": 0}, 
                    {"C_rzrz": 0},
                ]
            },
            {"Thickness": 1.0, "attributes": {"suffix": u" mm", "minimum": 0.0}},
        ]

        self.fillMaterialData()

