class POVRay(object):

    @staticmethod
    def serialize(solid):
        pass


def save(filename, solids, textures=):
    with open(filename, 'w') as pov:
        for solid in solids:
            pov.write(POVRay.serialize(solid))
