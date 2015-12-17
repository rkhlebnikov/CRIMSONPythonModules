import numpy

class PhastaConfig(object):
    class ArrayDescriptor(object):
        def __init__(self, phastaDataBlockName, dataType, optional, fields):
            self.phastaDataBlockName = phastaDataBlockName
            self.fields = fields
            self.dataType = dataType
            self.optional = optional

    class Field(object):
        def __init__(self, name, startIndex, nComponents):
            self.name = name
            self.startIndex = startIndex
            self.nComponents = nComponents

    def __init__(self, arrayDescriptors):
        self.arrayDescriptors = arrayDescriptors

    def findDescriptorAndField(self, fieldName):
        for arrayDesc in self.arrayDescriptors:
            for field in arrayDesc.fields:
                if field.name == fieldName:
                    return arrayDesc, field
        return None, None


restartConfig = PhastaConfig([
    PhastaConfig.ArrayDescriptor('solution', numpy.float64, False,
        [
            PhastaConfig.Field('pressure', 0, 1),
            PhastaConfig.Field('velocity', 1, 3),
            PhastaConfig.Field('concentration', 4, 1),
        ]),

    PhastaConfig.ArrayDescriptor('time derivative of solution', numpy.float64, True,
        [
            PhastaConfig.Field('pressure derivative', 0, 1),
            PhastaConfig.Field('velocity derivative', 1, 3),
            PhastaConfig.Field('concentration derivative', 4, 1),
        ]),

    PhastaConfig.ArrayDescriptor('displacement', numpy.float64, True,
        [
            PhastaConfig.Field('displacement', 0, 3),
        ]),

    PhastaConfig.ArrayDescriptor('displacement_ref', numpy.float64, True,
        [
            PhastaConfig.Field('displacement_ref', 0, 3),
        ]),
    # Todo: WSS
])

ybarConfig = PhastaConfig([
    PhastaConfig.ArrayDescriptor('ybar', numpy.float64, False,
        [
            PhastaConfig.Field('ybar', 4, 1),
        ]),
])

